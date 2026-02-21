import uuid
from django.db import models
from apps.core.models import TimeStampedModel
from apps.accounts.models import User


class Train(TimeStampedModel):
	"""Train model - Coming Soon"""
	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	train_number = models.CharField(max_length=20, unique=True)
	train_name = models.CharField(max_length=100)
	from_station = models.CharField(max_length=50)
	to_station = models.CharField(max_length=50)
	departure_time = models.TimeField()
	arrival_time = models.TimeField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	available_seats = models.PositiveIntegerField()

	class Meta:
		verbose_name_plural = "Trains"

	def __str__(self):
		return f"{self.train_number} - {self.train_name}"