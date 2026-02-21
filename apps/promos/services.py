from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from .models import Promo


def calculate_promo_discount(promo, amount):
    if not promo:
        return Decimal('0.00')
    amount = Decimal(amount)
    if promo.discount_type == Promo.TYPE_PERCENT:
        return (amount * promo.value / Decimal('100.0')).quantize(Decimal('0.01'))
    return promo.value


class CouponService:
    """Service for finding and applying best available coupons"""
    
    @staticmethod
    def get_best_coupon(user, module, base_price):
        """
        Get best coupon for user across all modules.
        
        Args:
            user: User instance
            module: 'hotels', 'buses', 'cabs', 'packages'
            base_price: Price to calculate discount on
        
        Returns:
            dict with coupon details or None
        """
        try:
            now = timezone.now()
            
            # Filter active promos applicable to module
            active_promos = Promo.objects.filter(
                is_active=True,
                expires_at__gte=now
            ).order_by('-value')
            
            if not active_promos.exists():
                return None
            
            best_promo = active_promos.first()
            discount = calculate_promo_discount(best_promo, base_price)
            
            return {
                'code': best_promo.code,
                'discount_amount': float(discount),
                'description': f"Save ₹{int(discount)}",
                'promo_id': best_promo.id
            }
        except:
            return None
    
    @staticmethod
    def validate_coupon(coupon_code, user, module, base_price):
        """Validate if coupon is usable"""
        try:
            coupon = Promo.objects.get(code=coupon_code.upper(), is_active=True)
            discount = calculate_promo_discount(coupon, base_price)
            return True, coupon, discount
        except:
            return False, None, Decimal('0')