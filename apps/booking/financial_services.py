"""
Financial calculations for booking domain (PHASE 2, PROMPT 4).

HARDENED RULES:
1. All financial calculations happen in service layer, NEVER in views
2. Deterministic: same inputs always produce same outputs
3. All amounts are Decimal, never float
4. Zero commission scenarios are handled
5. GST is 18% (configurable per settings)
"""
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from .models import Booking


def calculate_booking_financials(booking, gross_amount):
    """
    Calculate all financial fields for a booking.
    
    Args:
        booking: Booking instance (must be in HOLD status)
        gross_amount: Base booking amount (Decimal)
    
    Returns:
        dict with all financial fields
    """
    gross = Decimal(str(gross_amount))
    
    # Commission: configurable percentage
    commission_rate = Decimal(
        str(getattr(settings, 'BOOKING_COMMISSION_RATE', '0.15'))
    )  # 15% default
    commission = gross * commission_rate
    
    # GST: 18% on gross
    gst_rate = Decimal(
        str(getattr(settings, 'GST_RATE', '0.18'))
    )
    gst = gross * gst_rate
    
    # Payment gateway fee: 2% of gross
    gateway_fee_rate = Decimal(
        str(getattr(settings, 'PAYMENT_GATEWAY_FEE_RATE', '0.02'))
    )
    gateway_fee = gross * gateway_fee_rate
    
    # Net payable: gross - commission - gateway fee (no GST deducted)
    net_payable = gross - commission - gateway_fee
    
    return {
        'gross_amount': gross,
        'commission_amount': commission,
        'gst_amount': gst,
        'gateway_fee': gateway_fee,
        'net_payable_to_hotel': max(Decimal('0'), net_payable),  # Never negative
    }


@transaction.atomic
def set_booking_financials(booking, gross_amount):
    """
    Atomically update booking financial fields.
    
    Args:
        booking: Booking instance
        gross_amount: Gross booking amount
    
    Returns:
        Updated Booking instance
    """
    if booking.status not in [Booking.STATUS_HOLD, Booking.STATUS_PAYMENT_PENDING]:
        raise ValueError(
            f'Cannot set financials on booking in {booking.status} status'
        )
    
    financials = calculate_booking_financials(booking, gross_amount)
    
    booking.gross_amount = financials['gross_amount']
    booking.commission_amount = financials['commission_amount']
    booking.gst_amount = financials['gst_amount']
    booking.gateway_fee = financials['gateway_fee']
    booking.net_payable_to_hotel = financials['net_payable_to_hotel']
    booking.total_amount = booking.gross_amount + booking.gst_amount
    
    booking.save(update_fields=[
        'gross_amount',
        'commission_amount',
        'gst_amount',
        'gateway_fee',
        'net_payable_to_hotel',
        'total_amount',
        'updated_at',
    ])
    
    return booking


def get_booking_financial_summary(booking):
    """Get human-readable financial breakdown for booking."""
    return {
        'gross': booking.gross_amount,
        'commission': booking.commission_amount,
        'gst': booking.gst_amount,
        'gateway_fee': booking.gateway_fee,
        'net_payable': booking.net_payable_to_hotel,
        'total': booking.total_amount,
        'refund': booking.refund_amount,
        'settlement_status': booking.settlement_status,
    }
