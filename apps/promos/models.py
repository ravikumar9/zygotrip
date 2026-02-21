from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.accounts.models import User
from apps.booking.models import Booking


class Promo(TimeStampedModel):
	TYPE_PERCENT = 'percent'
	TYPE_AMOUNT = 'amount'

	TYPE_CHOICES = [
		(TYPE_PERCENT, 'Percent'),
		(TYPE_AMOUNT, 'Amount'),
	]

	MODULE_CHOICES = [
		('hotels', 'Hotels'),
		('buses', 'Buses'),
		('cabs', 'Cabs'),
		('packages', 'Packages'),
		('flights', 'Flights'),
		('trains', 'Trains'),
		('all', 'All Modules'),
	]

	code = models.CharField(max_length=20, unique=True)
	discount_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_PERCENT)
	value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Discount value (% or amount)")
	max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Max discount cap")
	max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
	starts_at = models.DateField(null=True, blank=True)
	ends_at = models.DateField(null=True, blank=True)
	applicable_module = models.CharField(max_length=50, choices=MODULE_CHOICES, default='all')
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['code', 'is_active']),
			models.Index(fields=['applicable_module', 'is_active']),
			models.Index(fields=['ends_at']),
		]

	def __str__(self):
		return self.code

	def is_valid(self):
		"""Check if coupon is valid"""
		if not self.is_active:
			return False
		now = timezone.now().date()
		if self.starts_at and self.starts_at > now:
			return False
		if self.ends_at and self.ends_at < now:
			return False
		return True


class PromoUsage(TimeStampedModel):
	promo = models.ForeignKey(Promo, on_delete=models.CASCADE, related_name='usages')
	booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='promo_usages')
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	class Meta:
		verbose_name_plural = "Promo Usage"
		indexes = [models.Index(fields=['promo', 'user'])]

	def __str__(self):
		return f"{self.promo.code} - {self.user.email}"