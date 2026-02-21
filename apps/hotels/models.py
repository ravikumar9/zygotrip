from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings
from apps.hotels.validators import validate_https_image_url
from apps.core.models import TimeStampedModel


class Property(TimeStampedModel):
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
	name = models.CharField(max_length=140)
	slug = models.SlugField(unique=True, blank=True, null=True)
	property_type = models.CharField(max_length=80, default='Hotel')
	
	# LOCATION ARCHITECTURE: Hierarchical FKs (not text strings)
	# This enables: geo search, distance sorting, contextual navigation
	city = models.ForeignKey('core.City', on_delete=models.PROTECT, related_name='hotels')
	locality = models.ForeignKey('core.Locality', on_delete=models.SET_NULL, null=True, blank=True, related_name='hotels')
	
	# Legacy fields for backwards compatibility (DEPRECATED - use FKs above)
	city_text = models.CharField(max_length=80, blank=True, help_text="DEPRECATED: Use city FK")
	area = models.CharField(max_length=120, blank=True)
	landmark = models.CharField(max_length=120, blank=True)
	country = models.CharField(max_length=80, default='India')
	address = models.CharField(max_length=200)
	description = models.TextField()
	
	# INTELLIGENCE SIGNALS (what makes cards feel informative)
	rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	review_count = models.IntegerField(default=0, help_text="Total reviews")
	popularity_score = models.IntegerField(default=0, help_text="Booking velocity + search rank")
	
	# Geo coordinates (REQUIRED for distance sorting)
	latitude = models.DecimalField(max_digits=9, decimal_places=6)
	longitude = models.DecimalField(max_digits=9, decimal_places=6)
	
	# PRICING: Moved to RoomType model (domain-driven design)
	# Property pricing is now COMPUTED from room types, not stored
	# Legacy fields removed - use @property base_price instead
	
	# BOOKING SIGNALS (displayed on card)
	bookings_today = models.IntegerField(default=0, help_text="Bookings in last 24h")
	bookings_this_week = models.IntegerField(default=0)
	is_trending = models.BooleanField(default=False, help_text="Hot property indicator")
	
	# POLICY SIGNALS (filter criteria)
	has_free_cancellation = models.BooleanField(default=True)
	cancellation_hours = models.IntegerField(default=24, help_text="Free cancellation window")
	
	def get_distance_from(self, lat, lng):
		"""Calculate distance from given coordinates (km)"""
		from math import radians, cos, sin, asin, sqrt
		
		# Haversine formula
		lon1, lat1, lon2, lat2 = map(radians, [float(self.longitude), float(self.latitude), lng, lat])
		dlon = lon2 - lon1
		dlat = lat2 - lat1
		a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
		c = 2 * asin(sqrt(a))
		km = 6371 * c  # Earth radius in km
		return round(km, 1)
	
	@property
	def base_price(self):
		"""
		COMPUTED PROPERTY: Returns minimum room price
		Pricing is now sourced from RoomType model (domain-driven design)
		This property provides backward compatibility for existing code
		"""
		from django.db.models import Min
		import logging
		
		logger = logging.getLogger(__name__)
		logger.warning(
			f"DEPRECATION: Property.base_price accessed for {self.name}. "
			"Migrate to using room_types queryset with annotations."
		)
		
		min_price = self.room_types.aggregate(Min('base_price'))['base_price__min']
		return min_price if min_price is not None else 0
	
	@property
	def discount_price(self):
		"""DEPRECATED: Use RoomType pricing with date-based RoomInventory"""
		return None
	
	@property
	def dynamic_price(self):
		"""DEPRECATED: Use RoomType pricing with date-based RoomInventory"""
		return None

	def clean(self):
		"""Validation firewall: reject invalid ratings"""
		if self.rating < 0 or self.rating > 5:
			raise ValidationError({'rating': 'Rating must be between 0 and 5'})

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)[:200]
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class PropertyImage(TimeStampedModel):
	"""Property images with featured flag"""
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
	image_url = models.URLField()
	caption = models.CharField(max_length=200, blank=True)
	is_featured = models.BooleanField(default=False)
	display_order = models.IntegerField(default=0)

	class Meta:
		ordering = ['-is_featured', 'display_order']

	def clean(self):
		"""Validate image URL has proper extension"""
		validate_https_image_url(self.image_url)

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)
		if self.is_featured:
			PropertyImage.objects.filter(property=self.property, is_featured=True).exclude(pk=self.pk).update(is_featured=False)

	def __str__(self):
		return f"{self.property.name} - Image {self.id}"


class PropertyOffer(TimeStampedModel):
	"""Promotional offers and discounts"""
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='offers')
	title = models.CharField(max_length=200)
	description = models.TextField()
	discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
	discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	valid_from = models.DateField()
	valid_until = models.DateField()
	is_active = models.BooleanField(default=True)
	code = models.CharField(max_length=50, unique=True)

	def clean(self):
		"""Validate date range and discount values"""
		if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
			raise ValidationError('valid_from must be before valid_until')
		if self.discount_percentage and (self.discount_percentage < 0 or self.discount_percentage > 90):
			raise ValidationError({'discount_percentage': 'Discount percentage must be between 0 and 90'})
		if self.discount_amount and self.discount_amount < 0:
			raise ValidationError({'discount_amount': 'Discount amount cannot be negative'})

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.property.name} - {self.title}"


class RatingAggregate(TimeStampedModel):
	"""Aggregated ratings breakdown (like Goibibo's rating cards)"""
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rating_breakdown')
	cleanliness = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	service = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	location = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	amenities = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	value_for_money = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	total_reviews = models.IntegerField(default=0)

	def clean(self):
		"""Validate all ratings are between 0 and 5"""
		rating_fields = ['cleanliness', 'service', 'location', 'amenities', 'value_for_money']
		errors = {}
		for field in rating_fields:
			value = getattr(self, field)
			if value < 0 or value > 5:
				errors[field] = f'{field.replace("_", " ").title()} rating must be between 0 and 5'
		if errors:
			raise ValidationError(errors)
		if self.total_reviews < 0:
			raise ValidationError({'total_reviews': 'Total reviews cannot be negative'})

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.property.name} - Rating Breakdown"


class Category(TimeStampedModel):
	"""Property categories for filtering"""
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(unique=True)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=40, blank=True)

	class Meta:
		verbose_name_plural = 'Categories'

	def __str__(self):
		return self.name


class PropertyCategory(TimeStampedModel):
	"""Many-to-many relationship for property categories"""
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='categories')
	category = models.ForeignKey(Category, on_delete=models.CASCADE)

	class Meta:
		unique_together = ['property', 'category']
		verbose_name_plural = 'Property Categories'

	def __str__(self):
		return f"{self.property.name} - {self.category.name}"

class PropertyPolicy(TimeStampedModel):
	"""Property policies (cancellation, check-in, etc)"""
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='policies')
	title = models.CharField(max_length=120)
	description = models.TextField()

	def __str__(self):
		return f"{self.property.name} - {self.title}"


class PropertyAmenity(TimeStampedModel):
	"""Property amenities with optional icons"""
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='amenities')
	name = models.CharField(max_length=120)
	icon = models.CharField(max_length=40, blank=True)

	class Meta:
		verbose_name_plural = 'Property Amenities'

	def __str__(self):
		return f"{self.property.name} - {self.name}"