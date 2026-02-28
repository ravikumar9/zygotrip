"""
Payment Gateway Integration Models
Support for Wallet, UPI (Paytm), Cards (Cashfree), and Stripe fallback
"""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from decimal import Decimal


class Payment(models.Model):
    """Legacy stub Payment model - keeping for backwards compatibility."""
    booking = models.ForeignKey('booking.Booking', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'payments'

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"


class WalletBalance(TimeStampedModel):
	"""User wallet balance for direct payments"""
	
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='wallet'
	)
	
	balance = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		default=0.00,
		help_text="Current wallet balance"
	)
	
	# Prevent negative balance
	def deduct(self, amount):
		"""Deduct amount from wallet with validation"""
		if self.balance < amount:
			raise ValueError("Insufficient wallet balance")
		
		self.balance -= Decimal(str(amount))
		self.save()
		return True
	
	def add(self, amount):
		"""Add amount to wallet"""
		self.balance += Decimal(str(amount))
		self.save()
		return True
	
	class Meta:
		verbose_name = "Wallet Balance"
		verbose_name_plural = "Wallet Balances"
	
	def __str__(self):
		return f"{self.user.email} - ₹{self.balance}"


class WalletTransaction(TimeStampedModel):
	"""Track all wallet transactions (credits and debits)"""
	
	TRANSACTION_TYPES = [
		('credit', 'Credit'),
		('debit', 'Debit'),
	]
	
	wallet = models.ForeignKey(
		WalletBalance,
		on_delete=models.CASCADE,
		related_name='transactions'
	)
	
	transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	
	# Reference
	booking_reference = models.CharField(max_length=100, blank=True, help_text="Booking ID if payment for booking")
	description = models.CharField(max_length=200)
	
	# Balance snapshot
	balance_before = models.DecimalField(max_digits=10, decimal_places=2)
	balance_after = models.DecimalField(max_digits=10, decimal_places=2)
	
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['-created_at']
		verbose_name = "Wallet Transaction"
		verbose_name_plural = "Wallet Transactions"
	
	def __str__(self):
		return f"{self.transaction_type.title()} ₹{self.amount} - {self.description}"


class PaymentTransaction(TimeStampedModel):
	"""Track all payment transactions across all gateways"""
	
	GATEWAY_CHOICES = [
		('wallet', 'ZygoTrip Wallet'),
		('paytm_upi', 'Paytm UPI'),
		('cashfree', 'Cashfree'),
		('stripe', 'Stripe'),
	]
	
	STATUS_CHOICES = [
		('initiated', 'Initiated'),
		('pending', 'Pending'),
		('success', 'Success'),
		('failed', 'Failed'),
		('cancelled', 'Cancelled'),
		('refunded', 'Refunded'),
	]
	
	# Transaction IDs
	transaction_id = models.CharField(max_length=100, unique=True, help_text="Our internal transaction ID")
	gateway_transaction_id = models.CharField(max_length=200, blank=True, help_text="Gateway's transaction ID")
	
	# Gateway used
	gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
	
	# User and booking
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='payment_transactions'
	)
	
	booking_reference = models.CharField(max_length=100, help_text="Booking reference number")
	
	# Amount
	amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Payment amount")
	currency = models.CharField(max_length=3, default='INR')
	
	# Status
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
	
	# Metadata
	payment_method_details = models.JSONField(blank=True, null=True, help_text="Additional payment method info")
	gateway_response = models.JSONField(blank=True, null=True, help_text="Full gateway response")
	failure_reason = models.TextField(blank=True, help_text="Reason for failure if applicable")
	
	# Webhooks
	webhook_received = models.BooleanField(default=False)
	webhook_data = models.JSONField(blank=True, null=True)
	
	# Refund tracking
	refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
	refund_initiated_at = models.DateTimeField(null=True, blank=True)
	refund_completed_at = models.DateTimeField(null=True, blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-created_at']
		verbose_name = "Payment Transaction"
		verbose_name_plural = "Payment Transactions"
		indexes = [
			models.Index(fields=['user', 'status']),
			models.Index(fields=['booking_reference']),
			models.Index(fields=['gateway', 'status']),
		]
	
	def __str__(self):
		return f"{self.transaction_id} - {self.gateway} - ₹{self.amount} ({self.status})"
	
	def mark_success(self, gateway_transaction_id, gateway_response=None):
		"""Mark payment as successful"""
		self.status = 'success'
		self.gateway_transaction_id = gateway_transaction_id
		if gateway_response:
			self.gateway_response = gateway_response
		self.save()
	
	def mark_failed(self, reason, gateway_response=None):
		"""Mark payment as failed"""
		self.status = 'failed'
		self.failure_reason = reason
		if gateway_response:
			self.gateway_response = gateway_response
		self.save()
	
	def initiate_refund(self, amount=None):
		"""Initiate refund for this transaction"""
		from django.utils import timezone
		
		if self.status != 'success':
			raise ValueError("Can only refund successful transactions")
		
		refund_amount = amount or self.amount
		if refund_amount > self.amount:
			raise ValueError("Refund amount cannot exceed transaction amount")
		
		self.refund_amount = refund_amount
		self.refund_initiated_at = timezone.now()
		self.status = 'refunded'
		self.save()
		
		return True


class PaymentGatewayConfig(models.Model):
	"""Configuration for payment gateways"""
	
	gateway_name = models.CharField(max_length=50, unique=True)
	is_enabled = models.BooleanField(default=True)
	
	# Priority (lower = higher priority)
	priority = models.IntegerField(default=100, help_text="Lower number = higher priority")
	
	# Configuration (API keys, merchant IDs, etc.)
	config_data = models.JSONField(help_text="Gateway-specific configuration")
	
	# Limits
	min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
	max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['priority']
		verbose_name = "Payment Gateway Config"
		verbose_name_plural = "Payment Gateway Configs"
	
	def __str__(self):
		status = "✓" if self.is_enabled else "✗"
		return f"{status} {self.gateway_name} (Priority: {self.priority})"
