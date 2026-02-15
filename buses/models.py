import uuid
from django.db import models
from core.models import TimeStampedModel
from accounts.models import User


class BusType(TimeStampedModel):
	"""Bus type options: Sleeper, Semi Sleeper, AC, Non-AC, Volvo, Seater"""
	SLEEPER = 'sleeper'
	SEMI_SLEEPER = 'semi_sleeper'
	AC = 'ac'
	NON_AC = 'non_ac'
	VOLVO = 'volvo'
	SEATER = 'seater'

	TYPE_CHOICES = [
		(SLEEPER, 'Sleeper'),
		(SEMI_SLEEPER, 'Semi Sleeper'),
		(AC, 'AC'),
		(NON_AC, 'Non-AC'),
		(VOLVO, 'Volvo'),
		(SEATER, 'Seater'),
	]

	name = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True)
	base_fare = models.DecimalField(max_digits=8, decimal_places=2, default=500)
	capacity = models.PositiveIntegerField(default=40)

	class Meta:
		verbose_name_plural = "Bus Types"

	def __str__(self):
		return self.get_name_display()


class Bus(TimeStampedModel):
	"""Bus model with routes and schedules"""
	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	registration_number = models.CharField(max_length=20, unique=True)
	bus_type = models.ForeignKey(BusType, on_delete=models.PROTECT)
	operator_name = models.CharField(max_length=100)
	from_city = models.CharField(max_length=50)
	to_city = models.CharField(max_length=50)
	departure_time = models.TimeField()
	arrival_time = models.TimeField()
	price_per_seat = models.DecimalField(max_digits=8, decimal_places=2)
	available_seats = models.PositiveIntegerField()
	is_active = models.BooleanField(default=True)
	amenities = models.CharField(max_length=500, blank=True, help_text="Comma-separated amenities")

	def __str__(self):
		return f"{self.operator_name} - {self.from_city} to {self.to_city}"

	def get_amenities_list(self):
		if self.amenities:
			return [a.strip() for a in self.amenities.split(',')]
		return []


class BusSeat(TimeStampedModel):
	"""Individual seat in a bus with seat state management"""
	AVAILABLE = 'available'
	BOOKED = 'booked'
	LADIES = 'ladies'
	SELECTED = 'selected'

	STATE_CHOICES = [
		(AVAILABLE, 'Available'),
		(BOOKED, 'Booked'),
		(LADIES, 'Ladies Seat'),
		(SELECTED, 'Selected'),
	]

	bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
	seat_number = models.CharField(max_length=10)  # e.g., "A1", "B2"
	row = models.CharField(max_length=2)  # A, B, C, D, etc.
	column = models.PositiveIntegerField()  # 1, 2, 3, 4
	is_ladies_seat = models.BooleanField(default=False)
	state = models.CharField(max_length=20, choices=STATE_CHOICES, default=AVAILABLE)

	class Meta:
		unique_together = ('bus', 'seat_number')

	def __str__(self):
		return f"{self.bus.registration_number} - Seat {self.seat_number}"


class BusBooking(TimeStampedModel):
	"""Bus booking with passenger details"""
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
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bus_bookings')
	bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='bookings')
	journey_date = models.DateField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	promo_code = models.CharField(max_length=30, blank=True)

	def __str__(self):
		return f"Bus Booking - {self.uuid}"


class BusBookingPassenger(TimeStampedModel):
	"""Passenger details for bus booking"""
	MALE = 'male'
	FEMALE = 'female'

	GENDER_CHOICES = [
		(MALE, 'Male'),
		(FEMALE, 'Female'),
	]

	booking = models.ForeignKey(BusBooking, on_delete=models.CASCADE, related_name='passengers')
	seat = models.ForeignKey(BusSeat, on_delete=models.PROTECT)
	full_name = models.CharField(max_length=120)
	age = models.PositiveIntegerField()
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default=MALE)
	phone = models.CharField(max_length=15, blank=True)
	id_proof_type = models.CharField(max_length=50, blank=True)
	id_proof_number = models.CharField(max_length=50, blank=True)

	def __str__(self):
		return f"{self.full_name} - {self.booking.uuid}"


class BusPriceBreakdown(TimeStampedModel):
	"""Price breakdown for bus booking"""
	booking = models.OneToOneField(BusBooking, on_delete=models.CASCADE, related_name='price_breakdown')
	base_amount = models.DecimalField(max_digits=12, decimal_places=2)
	service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	gst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	promo_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		verbose_name_plural = "Bus Price Breakdowns"

	def __str__(self):
		return f"Price Breakdown - {self.booking.uuid}"
