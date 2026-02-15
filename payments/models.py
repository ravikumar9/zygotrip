import uuid
from django.db import models
from core.models import TimeStampedModel
from booking.models import Booking


class Payment(TimeStampedModel):
	STATUS_PENDING = 'pending'
	STATUS_PAID = 'paid'
	STATUS_FAILED = 'failed'

	METHOD_CARD = 'card'
	METHOD_WALLET = 'wallet'
	METHOD_MIXED = 'mixed'

	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending'),
		(STATUS_PAID, 'Paid'),
		(STATUS_FAILED, 'Failed'),
	]

	METHOD_CHOICES = [
		(METHOD_CARD, 'Card'),
		(METHOD_WALLET, 'Wallet'),
		(METHOD_MIXED, 'Mixed'),
	]

	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_CARD)
	wallet_used = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Invoice(TimeStampedModel):
	STATUS_OPEN = 'open'
	STATUS_PAID = 'paid'

	STATUS_CHOICES = [
		(STATUS_OPEN, 'Open'),
		(STATUS_PAID, 'Paid'),
	]

	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
	issued_at = models.DateTimeField(auto_now_add=True)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)

# Create your models here.
