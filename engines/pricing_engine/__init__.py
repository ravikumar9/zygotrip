"""
Pricing Engine - Global pricing calculations
PHASE 3: Extracted from pricing app
CRITICAL RULE: NO app imports allowed
"""
from decimal import Decimal
from typing import Dict, Any


def calculate_price_breakdown(
    base_amount: Decimal,
    meal_amount: Decimal,
    service_fee_rate: Decimal,
    gst_rate: Decimal,
    promo_discount: Decimal = Decimal('0.00')
) -> Dict[str, Decimal]:
    """
    Calculate complete price breakdown for booking
    
    Args:
        base_amount: Base room price
        meal_amount: Meal plan cost
        service_fee_rate: Service fee percentage (e.g., 0.10 for 10%)
        gst_rate: GST percentage (e.g., 0.18 for 18%)
        promo_discount: Promo discount amount
    
    Returns:
        Dict with breakdown: base, meals, service_fee, gst, discount, total
    """
    subtotal = base_amount + meal_amount
    service_fee = subtotal * service_fee_rate
    
    # Apply discount before GST
    discounted_amount = subtotal - promo_discount
    if discounted_amount < 0:
        discounted_amount = Decimal('0.00')
    
    # GST on discounted amount + service fee
    taxable_amount = discounted_amount + service_fee
    gst = taxable_amount * gst_rate
    
    total = taxable_amount + gst
    
    return {
        'base': base_amount,
        'meals': meal_amount,
        'subtotal': subtotal,
       'service_fee': service_fee,
        'discount': promo_discount,
        'gst': gst,
        'total': total.quantize(Decimal('0.01'))
    }


def calculate_markup(base_price: Decimal, markup_percentage: Decimal) -> Decimal:
    """
    Calculate markup on base price
    
    Args:
        base_price: Original price
        markup_percentage: Markup as decimal (e.g., 0.15 for 15%)
    
    Returns:
        Marked up price
    """
    markup = base_price * markup_percentage
    return (base_price + markup).quantize(Decimal('0.01'))


def calculate_discount_amount(original_price: Decimal, discount_percentage: Decimal) -> Decimal:
    """
    Calculate discount amount from percentage
    
    Args:
        original_price: Original price
        discount_percentage: Discount as decimal (e.g., 0.20 for 20%)
    
    Returns:
        Discount amount
    """
    discount = original_price * discount_percentage
    return discount.quantize(Decimal('0.01'))


def apply_tiered_discount(base_price: Decimal, nights: int) -> Dict[str, Any]:
    """
    Apply tiered discount based on number of nights
    
    Args:
        base_price: Base price per night
        nights: Number of nights
    
    Returns:
        Dict with original, discount_rate, discount_amount, final_price
    """
    # Discount tiers: 7+ nights = 10%, 14+ nights = 15%, 30+ nights = 20%
    if nights >= 30:
        discount_rate = Decimal('0.20')
    elif nights >= 14:
        discount_rate = Decimal('0.15')
    elif nights >= 7:
        discount_rate = Decimal('0.10')
    else:
        discount_rate = Decimal('0.00')
    
    total_price = base_price * nights
    discount_amount = calculate_discount_amount(total_price, discount_rate)
    final_price = total_price - discount_amount
    
    return {
        'original_price': total_price,
        'discount_rate': float(discount_rate * 100),
        'discount_amount': discount_amount,
        'final_price': final_price,
        'nights': nights
    }


def calculate_cancellation_charge(
    total_amount: Decimal,
    days_before_checkin: int,
    cancellation_policy: str = 'moderate'
) -> Dict[str, Decimal]:
    """
    Calculate cancellation charges based on policy
    
    Args:
        total_amount: Total booking amount
        days_before_checkin: Days remaining until check-in
        cancellation_policy: 'flexible', 'moderate', or 'strict'
    
    Returns:
        Dict with charge, refund, policy
    """
    if cancellation_policy == 'flexible':
        # Free cancellation up to 1 day before
        charge_rate = Decimal('0.00') if days_before_checkin >= 1 else Decimal('0.20')
    elif cancellation_policy == 'strict':
        # 50% if 7+ days, 100% otherwise
        charge_rate = Decimal('0.50') if days_before_checkin >= 7 else Decimal('1.00')
    else:  # moderate
        # 50% if 3+ days, 100% otherwise
        charge_rate = Decimal('0.50') if days_before_checkin >= 3 else Decimal('1.00')
    
    charge = (total_amount * charge_rate).quantize(Decimal('0.01'))
    refund = (total_amount - charge).quantize(Decimal('0.01'))
    
    return {
        'charge': charge,
        'refund': refund,
        'charge_percentage': float(charge_rate * 100),
        'policy': cancellation_policy
    }