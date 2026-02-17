from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from apps.hotels.validators import validate_https_image_url
from core.models import TimeStampedModel
from accounts.models import User


class Property(TimeStampedModel):
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
	name = models.CharField(max_length=140)
	slug = models.SlugField(unique=True, blank=True, null=True)
	property_type = models.CharField(max_length=80, default='Hotel')
	city = models.CharField(max_length=80)
	area = models.CharField(max_length=120, blank=True)
	landmark = models.CharField(max_length=120, blank=True)
	country = models.CharField(max_length=80)
	address = models.CharField(max_length=200)
	description = models.TextField()
	rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	
	# Google Maps
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	
	# Pricing
	base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	dynamic_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

	def clean(self):
		"""Validation firewall: reject negative prices and invalid ratings"""
		if self.base_price and self.base_price < 0:
			raise ValidationError({'base_price': 'Price cannot be negative'})
		if self.discount_price and self.discount_price < 0:
			raise ValidationError({'discount_price': 'Discount price cannot be negative'})
		if self.dynamic_price and self.dynamic_price < 0:
			raise ValidationError({'dynamic_price': 'Dynamic price cannot be negative'})
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
