from django.db import models
from core.models import TimeStampedModel
from accounts.models import User
from booking.models import Booking


class Promo(TimeStampedModel):
	TYPE_PERCENT = 'percent'
	TYPE_AMOUNT = 'amount'

	TYPE_CHOICES = [
		(TYPE_PERCENT, 'Percent'),
		(TYPE_AMOUNT, 'Amount'),
	]

	code = models.CharField(max_length=20, unique=True)
	discount_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
	value = models.DecimalField(max_digits=10, decimal_places=2)
	max_uses = models.PositiveIntegerField(default=0)
	starts_at = models.DateField(null=True, blank=True)
	ends_at = models.DateField(null=True, blank=True)

	def __str__(self):
		return self.code


class PromoUsage(TimeStampedModel):
	promo = models.ForeignKey(Promo, on_delete=models.CASCADE, related_name='usages')
	booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='promo_usages')
	user = models.ForeignKey(User, on_delete=models.CASCADE)

# Create your models here.
