"""
Settlement generation service (PHASE 2, PROMPT 5).

Generates settlements for properties based on period and booking data.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Booking, Settlement, SettlementLineItem


@transaction.atomic
def generate_settlement(hotel, period_start, period_end):
    """
    Generate or update settlement for a hotel in a given period.
    
    Process:
    1. Find all CONFIRMED bookings in period
    2. Exclude bookings already in other settlements  
    3. Create settlement with aggregated amounts
    4. Create line items for each booking
    5. Mark bookings as SETTLEMENT_PENDING
    
    Args:
        hotel: Property instance
        period_start: datetime.date
        period_end: datetime.date (inclusive)
    
    Returns:
        Settlement instance
    """
    # Check if settlement already exists (idempotent)
    try:
        existing = Settlement.objects.get(
            hotel=hotel,
            period_start=period_start,
            period_end=period_end,
        )
        # If draft, allow regeneration; otherwise, return existing
        if existing.status != Settlement.STATUS_DRAFT:
            return existing
        settlement = existing
    except Settlement.DoesNotExist:
        settlement = Settlement.objects.create(
            hotel=hotel,
            period_start=period_start,
            period_end=period_end,
            status=Settlement.STATUS_DRAFT,
        )
    
    # Find confirmed bookings in period (checkout on or after period_start, checkin before period_end)
    eligible_bookings = Booking.objects.filter(
        property=hotel,
        status=Booking.STATUS_CONFIRMED,
        check_out__gte=period_start,
        check_in__lte=period_end,
    ).select_for_update()
    
    # Clear previous line items if regenerating
    SettlementLineItem.objects.filter(settlement=settlement).delete()
    
    total_gross = Decimal('0')
    total_commission = Decimal('0')
    total_gateway_fee = Decimal('0')
    total_payable = Decimal('0')
    total_refunded = Decimal('0')
    
    for booking in eligible_bookings:
        # Only include if not already settled
        existing_settlement = SettlementLineItem.objects.filter(
            booking=booking
        ).exclude(settlement=settlement).first()
        
        if existing_settlement:
            # Already in another settlement, skip
            continue
        
        # Create line item snapshot
        SettlementLineItem.objects.create(
            settlement=settlement,
            booking=booking,
            gross_amount=booking.gross_amount,
            commission_amount=booking.commission_amount,
            gateway_fee=booking.gateway_fee,
            payable_amount=booking.net_payable_to_hotel,
            refund_amount=booking.refund_amount,
        )
        
        # Aggregate
        total_gross += booking.gross_amount
        total_commission += booking.commission_amount
        total_gateway_fee += booking.gateway_fee
        total_payable += booking.net_payable_to_hotel
        total_refunded += booking.refund_amount
        
        # Mark booking as SETTLEMENT_PENDING if still CONFIRMED
        if booking.status == Booking.STATUS_CONFIRMED:
            booking.status = Booking.STATUS_SETTLEMENT_PENDING
            booking.settlement_status = 'settlement_pending'
            booking.save(update_fields=['status', 'settlement_status', 'updated_at'])
    
    # Update settlement totals
    settlement.total_gross = total_gross
    settlement.total_commission = total_commission
    settlement.total_gateway_fee = total_gateway_fee
    settlement.total_payable = total_payable
    settlement.total_refunded = total_refunded
    settlement.save(update_fields=[
        'total_gross',
        'total_commission',
        'total_gateway_fee',
        'total_payable',
        'total_refunded',
        'updated_at',
    ])
    
    return settlement


def get_unsettled_bookings(hotel, limit_date=None):
    """
    Get bookings ready for settlement.
    
    Returns bookings that are CONFIRMED and checkout date is on or before limit_date.
    """
    qs = Booking.objects.filter(
        property=hotel,
        status=Booking.STATUS_CONFIRMED,
    )
    
    if limit_date:
        qs = qs.filter(check_out__lte=limit_date)
    
    return qs
