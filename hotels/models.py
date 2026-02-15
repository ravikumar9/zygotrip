from django.db import models
from core.models import TimeStampedModel
from accounts.models import User


class Property(TimeStampedModel):
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
	name = models.CharField(max_length=140)
	city = models.CharField(max_length=80)
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

	def __str__(self):
		return self.name


class PropertyImage(TimeStampedModel):
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
	image_url = models.URLField()
	is_featured = models.BooleanField(default=False)


class PropertyPolicy(TimeStampedModel):
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='policies')
	title = models.CharField(max_length=120)
	description = models.TextField()


class PropertyAmenity(TimeStampedModel):
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='amenities')
	name = models.CharField(max_length=120)
	icon = models.CharField(max_length=40, blank=True)

# Create your models here.
