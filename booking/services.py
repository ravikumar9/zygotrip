from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pricing.services import calculate_price_breakdown
from promos.models import PromoUsage
from promos.selectors import get_active_promo
from promos.services import calculate_promo_discount
from rooms.models import RoomInventory
from .models import Booking, BookingGuest, BookingPriceBreakdown, BookingRoom, BookingStatusHistory


def _date_range(start_date, end_date):
    current = start_date
    while current < end_date:
        yield current
        current += timedelta(days=1)


def create_booking(user, property_obj, room_type, quantity, meal_plan, check_in, check_out, guests, promo_code=''):
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
        inventories = RoomInventory.objects.select_for_update().filter(
            room_type=room_type,
            date__gte=check_in,
            date__lt=check_out,
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

        booking = Booking.objects.create(
            user=user,
            property=property_obj,
            check_in=check_in,
            check_out=check_out,
            status=Booking.STATUS_REVIEW,
            total_amount=breakdown['total_amount'],
            promo_code=promo.code if promo else '',
        )
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

    return booking
