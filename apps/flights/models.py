import uuid
from django.db import models
from apps.core.models import TimeStampedModel


class Flight(TimeStampedModel):
	"""Flight model - Coming Soon"""
	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	airline = models.CharField(max_length=100)
	flight_number = models.CharField(max_length=20, unique=True)
	from_city = models.CharField(max_length=50)
	to_city = models.CharField(max_length=50)
	departure_time = models.DateTimeField()
	arrival_time = models.DateTimeField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	available_seats = models.PositiveIntegerField()

	class Meta:
		verbose_name_plural = "Flights"

	def __str__(self):
		return f"{self.airline} {self.flight_number}"