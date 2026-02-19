from django.db import models
from core.models import TimeStampedModel
from accounts.models import User


class Wallet(TimeStampedModel):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
	balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

	def __str__(self):
		return f"{self.user.email}"


class WalletTransaction(TimeStampedModel):
	TRANSACTION_TYPE_CREDIT = 'credit'
	TRANSACTION_TYPE_DEBIT = 'debit'
	TRANSACTION_TYPE_REFUND = 'refund'

	TRANSACTION_TYPE_CHOICES = [
		(TRANSACTION_TYPE_CREDIT, 'Credit'),
		(TRANSACTION_TYPE_DEBIT, 'Debit'),
		(TRANSACTION_TYPE_REFUND, 'Refund'),
	]

	STATUS_PENDING = 'pending'
	STATUS_COMPLETED = 'completed'
	STATUS_FAILED = 'failed'
	STATUS_CANCELLED = 'cancelled'

	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending'),
		(STATUS_COMPLETED, 'Completed'),
		(STATUS_FAILED, 'Failed'),
		(STATUS_CANCELLED, 'Cancelled'),
	]

	wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	description = models.CharField(max_length=255, blank=True)
	reference_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
	
	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['wallet', '-created_at']),
			models.Index(fields=['status']),
		]

	def __str__(self):
		return f"{self.wallet.user.email} - {self.transaction_type} ₹{self.amount} ({self.status})"
