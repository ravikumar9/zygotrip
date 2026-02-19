from datetime import timedelta
import time
from decimal import Decimal
from django.conf import settings
from django.db import OperationalError, connection, transaction
from django.utils import timezone
from core.models import OperationLog
from core.observability import PerformanceLog
from pricing.services import calculate_price_breakdown
from promos.models import PromoUsage
from promos.selectors import get_active_promo
from promos.services import calculate_promo_discount
from rooms.models import RoomInventory
from .models import Booking, BookingGuest, BookingPriceBreakdown, BookingRoom, BookingStatusHistory

_IDEMPOTENCY_COLUMN_AVAILABLE = None


def _has_idempotency_column():
    global _IDEMPOTENCY_COLUMN_AVAILABLE
    if _IDEMPOTENCY_COLUMN_AVAILABLE is not None:
        return _IDEMPOTENCY_COLUMN_AVAILABLE
    try:
        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor,
                    Booking._meta.db_table,
                )
            }
        _IDEMPOTENCY_COLUMN_AVAILABLE = 'idempotency_key' in columns
    except OperationalError:
        _IDEMPOTENCY_COLUMN_AVAILABLE = False
    return _IDEMPOTENCY_COLUMN_AVAILABLE


def _date_range(start_date, end_date):
    current = start_date
    while current < end_date:
        yield current
        current += timedelta(days=1)


def create_booking(
    user,
    property_obj,
    room_type,
    quantity,
    meal_plan,
    check_in,
    check_out,
    guests,
    promo_code='',
    idempotency_key=None,
):
    start_time = time.time()
    try:
        use_idempotency = idempotency_key and _has_idempotency_column()
        if use_idempotency:
            existing = Booking.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing
        nights = (check_out - check_in).days
        if nights <= 0:
            raise ValueError('Invalid date range')

        base_amount = Decimal(room_type.base_price) * quantity * nights
        meal_amount = Decimal('0.00')
        if meal_plan:
            meal_amount = Decimal(meal_plan.price) * quantity * nights

        promo = get_active_promo(promo_code) if promo_code else None
        if promo and promo.max_uses:
            usage_count = PromoUsage.objects.filter(promo=promo).count()
            if usage_count >= promo.max_uses:
                promo = None
        promo_discount = calculate_promo_discount(promo, base_amount + meal_amount)

        breakdown = calculate_price_breakdown(
            base_amount,
            meal_amount,
            settings.SERVICE_FEE_RATE,
            settings.GST_RATE,
            promo_discount,
        )

        with transaction.atomic():
            lock_start = time.time()
            inventories_qs = RoomInventory.objects.select_for_update().filter(
                room_type=room_type,
                date__gte=check_in,
                date__lt=check_out,
            )
            inventories = list(inventories_qs)
            lock_ms = int((time.time() - lock_start) * 1000)
            PerformanceLog.objects.create(
                operation_type='inventory_lock',
                duration_ms=lock_ms,
                start_time=timezone.now(),
                end_time=timezone.now(),
                status='success',
                resource_id=property_obj.id,
            )

            inventory_map = {item.date: item for item in inventories}
            for day in _date_range(check_in, check_out):
                inventory = inventory_map.get(day)
                if not inventory or inventory.available_count < quantity:
                    raise ValueError('Insufficient inventory')

            for day in _date_range(check_in, check_out):
                inventory = inventory_map[day]
                inventory.available_count -= quantity
                inventory.save(update_fields=['available_count', 'updated_at'])

            booking_fields = {
                'user': user,
                'property': property_obj,
                'check_in': check_in,
                'check_out': check_out,
                'status': Booking.STATUS_REVIEW,
                'total_amount': breakdown['total_amount'],
                'promo_code': promo.code if promo else '',
            }
            if use_idempotency:
                booking_fields['idempotency_key'] = idempotency_key
            booking = Booking.objects.create(**booking_fields)
            BookingRoom.objects.create(booking=booking, room_type=room_type, quantity=quantity)
            for guest in guests:
                BookingGuest.objects.create(
                    booking=booking,
                    full_name=guest['full_name'],
                    age=guest['age'],
                    email=guest.get('email', ''),
                )
            BookingPriceBreakdown.objects.create(booking=booking, **breakdown)
            if promo:
                PromoUsage.objects.create(promo=promo, booking=booking, user=user)
            BookingStatusHistory.objects.create(booking=booking, status=Booking.STATUS_REVIEW)

        duration_ms = int((time.time() - start_time) * 1000)
        PerformanceLog.objects.create(
            operation_type='booking_create',
            duration_ms=duration_ms,
            start_time=timezone.now(),
            end_time=timezone.now(),
            status='success',
            user_id=user.id if user else None,
            resource_id=booking.id if booking else None,
        )
        OperationLog.objects.create(
            operation_type='booking_created',
            status='success',
            details=str({'booking_id': booking.id, 'total_amount': str(booking.total_amount)}),
            timestamp=timezone.now(),
        )
        return booking
    except Exception as exc:
        duration_ms = int((time.time() - start_time) * 1000)
        PerformanceLog.objects.create(
            operation_type='booking_create',
            duration_ms=duration_ms,
            start_time=timezone.now(),
            end_time=timezone.now(),
            status='error',
            error_message=str(exc),
            user_id=user.id if user else None,
            resource_id=property_obj.id if property_obj else None,
        )
        OperationLog.objects.create(
            operation_type='booking_failed',
            status='failed',
            details=str({'error': str(exc), 'property_id': getattr(property_obj, 'id', None)}),
            timestamp=timezone.now(),
        )
        raise
