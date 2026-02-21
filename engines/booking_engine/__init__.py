"""
Booking Engine - Core booking workflow orchestration
PHASE 3: Extracted from booking app
CRITICAL RULE: NO app imports - pure business logic
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
import uuid


def generate_booking_reference() -> str:
    """Generate unique booking reference code"""
    return f"BK{uuid.uuid4().hex[:8].upper()}"


def calculate_nights(check_in: date, check_out: date) -> int:
    """Calculate number of nights"""
    delta = check_out - check_in
    return max(0, delta.days)


def validate_date_range(check_in: date, check_out: date) -> tuple[bool, str]:
    """
    Validate booking date range
    
    Returns:
        (is_valid, error_message)
    """
    today = date.today()
    
    if check_in < today:
        return False, "Check-in date cannot be in the past"
    
    if check_out <= check_in:
        return False, "Check-out must be after check-in"
    
    nights = calculate_nights(check_in, check_out)
    if nights > 30:
        return False, "Maximum stay is 30 nights"
    
    if nights == 0:
        return False, "Minimum stay is 1 night"
    
    return True, ""


def calculate_booking_expiry(created_at: datetime, timeout_minutes: int = 15) -> datetime:
    """Calculate booking expiry time"""
    return created_at + timedelta(minutes=timeout_minutes)


def is_booking_expired(created_at: datetime, timeout_minutes: int = 15) -> bool:
    """Check if booking has expired"""
    expiry = calculate_booking_expiry(created_at, timeout_minutes)
    return datetime.now() >= expiry


def calculate_total_guests(guest_list: list[Dict[str, Any]]) -> int:
    """Calculate total number of guests"""
    return len(guest_list)


def validate_guest_count(guests: int, max_guests: int) -> tuple[bool, str]:
    """
    Validate guest count against maximum
    
    Returns:
        (is_valid, error_message)
    """
    if guests < 1:
        return False, "At least 1 guest is required"
    
    if guests > max_guests:
        return False, f"Maximum {max_guests} guests allowed"
    
    return True, ""


def calculate_booking_total(
    base_price: Decimal,
    quantity: int,
    nights: int,
    meal_price: Decimal = Decimal('0.00'),
    service_fee: Decimal = Decimal('0.00'),
    gst: Decimal = Decimal('0.00'),
    discount: Decimal = Decimal('0.00')
) -> Decimal:
    """Calculate total booking amount"""
    room_total = base_price * quantity * nights
    meal_total = meal_price * quantity * nights if meal_price else Decimal('0.00')
    
    subtotal = room_total + meal_total
    total = subtotal + service_fee + gst - discount
    
    return max(Decimal('0.00'), total.quantize(Decimal('0.01')))


def determine_booking_status(
    payment_status: str,
    checkin_date: date
) -> str:
    """
    Determine booking status based on payment and dates
    
    Returns:
        'pending', 'confirmed', 'checked_in', 'completed', 'cancelled'
    """
    if payment_status != 'completed':
        return 'pending'
    
    today = date.today()
    
    if checkin_date > today:
        return 'confirmed'
    elif checkin_date == today:
        return 'checked_in'
    else:
        return 'completed'


def can_cancel_booking(
    status: str,
    checkin_date: date
) -> tuple[bool, str]:
    """
    Check if booking can be cancelled
    
    Returns:
        (can_cancel, reason)
    """
    if status == 'cancelled':
        return False, "Booking is already cancelled"
    
    if status == 'completed':
        return False, "Cannot cancel completed booking"
    
    if checkin_date < date.today():
        return False, "Cannot cancel after check-in date"
    
    return True, ""


def calculate_booking_value_score(
    total_amount: Decimal,
    nights: int,
    guest_count: int
) -> float:
    """
    Calculate booking value score for prioritization
    Higher score = higher priority
    """
    # Average per-night value
    nightly_value = float(total_amount) / max(nights, 1)
    # Guest multiplier (more guests = slightly higher score)
    guest_factor = 1 + (guest_count * 0.05)
    # Duration factor (longer stays = slightly higher score)
    duration_factor = 1 + (min(nights, 14) * 0.02)
    
    score = nightly_value * guest_factor * duration_factor
    return round(score, 2)


def generate_confirmation_code() -> str:
    """Generate confirmation code for booking"""
    return f"CONF{uuid.uuid4().hex[:10].upper()}"