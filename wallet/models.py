from django.db import models
from core.models import TimeStampedModel
from accounts.models import User


class Wallet(TimeStampedModel):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
	balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

	def __str__(self):
		return f"{self.user.email}"


class WalletTransaction(TimeStampedModel):
	TYPE_CREDIT = 'credit'
	TYPE_DEBIT = 'debit'
	TYPE_REFUND = 'refund'

	TYPE_CHOICES = [
		(TYPE_CREDIT, 'Credit'),
		(TYPE_DEBIT, 'Debit'),
		(TYPE_REFUND, 'Refund'),
	]

	wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	type = models.CharField(max_length=20, choices=TYPE_CHOICES)
	reference = models.CharField(max_length=120, blank=True)

# Create your models here.
