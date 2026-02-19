from django.db import models
from django.core.exceptions import ValidationError
from core.models import TimeStampedModel
from hotels.models import Property
from apps.hotels.validators import validate_https_image_url, validate_uploaded_image


class RoomType(TimeStampedModel):
	BED_TYPES = (
		('single', 'Single Bed'),
		('double', 'Double Bed'),
		('twin', 'Twin Beds'),
		('queen', 'Queen Bed'),
		('king', 'King Bed'),
	)
	
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='room_types')
	name = models.CharField(max_length=120)
	description = models.TextField()
	base_price = models.DecimalField(max_digits=10, decimal_places=2)
	max_guests = models.PositiveIntegerField(default=2)
	
	# Room details
	bed_type = models.CharField(max_length=20, choices=BED_TYPES, default='double')
	room_size_sqm = models.PositiveIntegerField(null=True, blank=True, help_text="Room size in square meters")

	def __str__(self):
		return f"{self.property.name} - {self.name}"


class RoomImage(TimeStampedModel):
	room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='images')
	image_url = models.URLField()
	image_file = models.ImageField(upload_to='rooms/', null=True, blank=True)
	is_featured = models.BooleanField(default=False)
	display_order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['display_order']

	def clean(self):
		if self.image_url:
			validate_https_image_url(self.image_url)
		validate_uploaded_image(self.image_file)

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"Room Image - {self.room_type.name}"


class RoomAmenity(TimeStampedModel):
	room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='amenities')
	name = models.CharField(max_length=120)
	icon = models.CharField(max_length=40, blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return f"{self.room_type.name} - {self.name}"


class RoomInventory(TimeStampedModel):
	room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='inventories')
	date = models.DateField()
	available_count = models.PositiveIntegerField(default=0)

	class Meta:
		unique_together = ('room_type', 'date')

# Create your models here.
