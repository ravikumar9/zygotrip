import uuid
from django.db import models
from core.models import TimeStampedModel
from accounts.models import User


class PackageCategory(TimeStampedModel):
	"""Package category: Adventure, Beach, Cultural, Religious, etc."""
	name = models.CharField(max_length=50, unique=True)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=50, blank=True, help_text="Emoji or icon")

	class Meta:
		verbose_name_plural = "Package Categories"

	def __str__(self):
		return self.name


class Package(TimeStampedModel):
	"""Holiday package with duration, itinerary, and pricing"""
	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	name = models.CharField(max_length=150)
	description = models.TextField()
	category = models.ForeignKey(PackageCategory, on_delete=models.PROTECT, related_name='packages')
	duration_days = models.PositiveIntegerField(help_text="Number of days in the package")
	destination = models.CharField(max_length=100)
	base_price = models.DecimalField(max_digits=12, decimal_places=2)
	rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
	review_count = models.PositiveIntegerField(default=0)
	image_url = models.URLField(blank=True)
	inclusions = models.TextField(help_text="Comma-separated inclusions")
	exclusions = models.TextField(blank=True, help_text="Comma-separated exclusions")
	is_active = models.BooleanField(default=True)
	max_group_size = models.PositiveIntegerField(default=30)
	difficulty_level = models.CharField(
		max_length=20,
		choices=[('easy', 'Easy'), ('moderate', 'Moderate'), ('hard', 'Hard')],
		default='easy'
	)

	def __str__(self):
		return self.name

	def get_inclusions_list(self):
		if self.inclusions:
			return [i.strip() for i in self.inclusions.split(',')]
		return []

	def get_exclusions_list(self):
		if self.exclusions:
			return [e.strip() for e in self.exclusions.split(',')]
		return []


class PackageItinerary(TimeStampedModel):
	"""Day-by-day itinerary for a package"""
	package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='itinerary')
	day_number = models.PositiveIntegerField()
	title = models.CharField(max_length=150)
	description = models.TextField()
	meals_included = models.CharField(max_length=20, choices=[('B', 'Breakfast'), ('L', 'Lunch'), ('D', 'Dinner'), ('BLD', 'All Three')], blank=True)
	accommodation = models.CharField(max_length=100, blank=True)

	class Meta:
		unique_together = ('package', 'day_number')
		ordering = ['day_number']

	def __str__(self):
		return f"Day {self.day_number} - {self.title}"


class PackageBooking(TimeStampedModel):
	"""Package booking with traveler details"""
	STATUS_PENDING = 'pending'
	STATUS_REVIEW = 'review'
	STATUS_PAYMENT = 'payment'
	STATUS_CONFIRMED = 'confirmed'
	STATUS_CANCELLED = 'cancelled'

	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending'),
		(STATUS_REVIEW, 'Review'),
		(STATUS_PAYMENT, 'Payment'),
		(STATUS_CONFIRMED, 'Confirmed'),
		(STATUS_CANCELLED, 'Cancelled'),
	]

	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='package_bookings')
	package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='bookings')
	start_date = models.DateField()
	end_date = models.DateField()
	number_of_travelers = models.PositiveIntegerField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	promo_code = models.CharField(max_length=30, blank=True)
	special_requests = models.TextField(blank=True)

	def __str__(self):
		return f"Package Booking - {self.uuid}"


class PackageTraveler(TimeStampedModel):
	"""Individual traveler in a package booking"""
	booking = models.ForeignKey(PackageBooking, on_delete=models.CASCADE, related_name='travelers')
	full_name = models.CharField(max_length=120)
	age = models.PositiveIntegerField()
	relationship = models.CharField(max_length=50, blank=True)  # Friend, Family, Spouse, etc.
	email = models.EmailField(blank=True)
	phone = models.CharField(max_length=15, blank=True)

	def __str__(self):
		return f"{self.full_name} - {self.booking.uuid}"


class PackagePriceBreakdown(TimeStampedModel):
	"""Price breakdown for package booking"""
	booking = models.OneToOneField(PackageBooking, on_delete=models.CASCADE, related_name='price_breakdown')
	per_person_base = models.DecimalField(max_digits=12, decimal_places=2)
	total_base = models.DecimalField(max_digits=12, decimal_places=2)
	accommodation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	meals = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	activities = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	transport = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	gst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	promo_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		verbose_name_plural = "Package Price Breakdowns"

	def __str__(self):
		return f"Price Breakdown - {self.booking.uuid}"
