from django.db import models
import json

# Import location models for registration
from .location_models import Country, State, City, Locality, LocationSearchIndex, RegionGroup


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		abstract = True


class OperationLog(TimeStampedModel):
	"""Audit log for critical operations"""
	
	OPERATION_CHOICES = [
		('booking_failed', 'Booking Failed'),
		('booking_created', 'Booking Created'),
		('payment_failed', 'Payment Failed'),
		('payment_initiated', 'Payment Initiated'),
		('coupon_applied', 'Coupon Applied'),
		('coupon_rejected', 'Coupon Rejected'),
		('inventory_sync', 'Inventory Sync'),
		('price_calculated', 'Price Calculated'),
		('mapping_decision', 'Mapping Decision'),
		('fraud_triggered', 'Fraud Triggered'),
	]
	
	STATUS_CHOICES = [
		('success', 'Success'),
		('failed', 'Failed'),
		('pending', 'Pending'),
	]
	
	operation_type = models.CharField(max_length=50, choices=OPERATION_CHOICES)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	details = models.TextField()  # JSON string with operation details
	timestamp = models.DateTimeField(db_index=True)
	
	class Meta:
		ordering = ['-timestamp']
		indexes = [
			models.Index(fields=['operation_type', 'status', '-timestamp']),
			models.Index(fields=['timestamp']),
		]
		verbose_name_plural = "Operation Logs"
	
	def get_details(self):
		"""Parse JSON details"""
		try:
			return json.loads(self.details)
		except:
			return {}
	
	def __str__(self):
		return f"{self.get_operation_type_display()} - {self.get_status_display()} @ {self.timestamp}"


# Import observability models for migration generation
from .observability import SystemMetrics, InventoryHealthCheck, PerformanceLog