import uuid
from django.db import models
from core.models import TimeStampedModel
from accounts.models import User


class Cab(TimeStampedModel):
	"""Cab model - Coming Soon"""
	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	cab_type = models.CharField(max_length=50, choices=[("sedan", "Sedan"), ("suv", "SUV"), ("van", "Van")])
	from_location = models.CharField(max_length=100)
	to_location = models.CharField(max_length=100)
	distance_km = models.DecimalField(max_digits=5, decimal_places=2)
	price_per_km = models.DecimalField(max_digits=8, decimal_places=2)
	available = models.BooleanField(default=True)

	class Meta:
		verbose_name_plural = "Cabs"

	def __str__(self):
		return f"{self.get_cab_type_display()} - {self.from_location} to {self.to_location}"
