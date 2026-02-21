from decimal import Decimal


def calculate_price_breakdown(base_amount, meal_amount, service_fee_rate, gst_rate, promo_discount):
    base_amount = Decimal(base_amount)
    meal_amount = Decimal(meal_amount)
    promo_discount = Decimal(promo_discount)

    service_fee = (base_amount * Decimal('0.05')).quantize(Decimal('0.01'))
    if service_fee > Decimal('500.00'):
        service_fee = Decimal('500.00')

    gst_rate_applied = Decimal('0.05') if base_amount < Decimal('7500.00') else Decimal('0.18')
    gst = (base_amount * gst_rate_applied).quantize(Decimal('0.01'))

    total = base_amount + meal_amount + service_fee + gst - promo_discount
    if total < Decimal('0.00'):
        total = Decimal('0.00')
    return {
        'base_amount': base_amount,
        'meal_amount': meal_amount,
        'service_fee': service_fee,
        'gst': gst,
        'promo_discount': promo_discount,
        'total_amount': total,
    }