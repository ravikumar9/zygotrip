import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.core.models import TimeStampedModel
from apps.accounts.models import User
from apps.hotels.models import Property
from apps.rooms.models import RoomType
from apps.core.validators import validate_future_date


class Booking(TimeStampedModel):
	STATUS_PENDING = 'pending'
	STATUS_REVIEW = 'review'
	STATUS_PAYMENT = 'payment'
	STATUS_CONFIRMED = 'confirmed'
	STATUS_CANCELLED = 'cancelled'

	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending'),
		(STATUS_REVIEW, 'Review'),
		(STATUS_PAYMENT, 'Payment'),
		(STATUS_CONFIRMED, 'Confirmed'),
		(STATUS_CANCELLED, 'Cancelled'),
	]

	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	public_booking_id = models.CharField(max_length=50, unique=True, editable=False, db_index=True, null=True, blank=True)
	idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
	check_in = models.DateField(validators=[validate_future_date])
	check_out = models.DateField(validators=[validate_future_date])
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	promo_code = models.CharField(max_length=30, blank=True)
	
	# GUEST DETAILS (directly on booking for easy access)
	guest_name = models.CharField(max_length=120, blank=True)
	guest_email = models.EmailField(blank=True)
	guest_phone = models.CharField(max_length=20, blank=True)
	
	# Booking timer (10 minutes from creation)
	timer_expires_at = models.DateTimeField(null=True, blank=True)
	
	def save(self, *args, **kwargs):
		# Generate public_booking_id on first creation
		if not self.pk and not self.public_booking_id:
			date_str = self.created_at.strftime('%Y%m%d') if self.created_at else timezone.now().strftime('%Y%m%d')
			short_id = str(self.uuid)[:8].upper()
			self.public_booking_id = f"BK-{date_str}-HTL-{short_id}"
		# Set timer on first creation (only for review and payment statuses)
		if not self.pk and self.status in [self.STATUS_REVIEW, self.STATUS_PAYMENT]:
			self.timer_expires_at = timezone.now() + timedelta(minutes=10)
		super().save(*args, **kwargs)

	def is_timer_expired(self):
		if self.timer_expires_at is None:
			return False
		return timezone.now() > self.timer_expires_at

	def __str__(self):
		return f"{self.uuid}"


class BookingRoom(TimeStampedModel):
	booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='rooms')
	room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)

	class Meta:
		app_label = 'booking'


class BookingGuest(TimeStampedModel):
	booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='guests')
	full_name = models.CharField(max_length=120)
	age = models.PositiveIntegerField(default=18)
	email = models.EmailField(blank=True)


class BookingPriceBreakdown(TimeStampedModel):
	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='price_breakdown')
	base_amount = models.DecimalField(max_digits=12, decimal_places=2)
	meal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	gst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	promo_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2)


class BookingStatusHistory(TimeStampedModel):
	booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
	status = models.CharField(max_length=20, choices=Booking.STATUS_CHOICES)
	note = models.CharField(max_length=200, blank=True)


# Import models from distributed_locks for migration generation
from .distributed_locks import BookingRetryQueue