"""Stub pricing services module."""
from decimal import Decimal


def calculate_price_breakdown(property_obj=None, room_type=None, check_in=None, check_out=None, quantity=1, meal_plan=None, promo_code=None):
    """
    Calculate price breakdown for a booking.
    
    Returns:
        dict: Price breakdown with base_price, meal_price, tax, and total
    """
    return {
        'base_price': Decimal('0.00'),
        'meal_price': Decimal('0.00'),
        'tax': Decimal('0.00'),
        'total': Decimal('0.00'),
        'currency': 'USD'
    }