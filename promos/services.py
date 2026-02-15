from decimal import Decimal
from .models import Promo


def calculate_promo_discount(promo, amount):
    if not promo:
        return Decimal('0.00')
    amount = Decimal(amount)
    if promo.discount_type == Promo.TYPE_PERCENT:
        return (amount * promo.value / Decimal('100.0')).quantize(Decimal('0.01'))
    return promo.value
