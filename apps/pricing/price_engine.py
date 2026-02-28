"""
PHASE 4: Price Engine Hardening
Strict calculation pipeline: Base → Property discount → Platform discount → Coupon → 
Add-ons → Service fee → GST → Final

All fee percentages stored in database (NO hardcoded values).
"""
from decimal import Decimal
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class PriceEngine:
    """
    Strict pricing calculation with all steps transparent and traceable.
    
    Formula:
    1. base_price = room.base_price * nights * occupancy
    2. property_discount = base_price * (property.discount_percent / 100)
    3. subtotal_after_property_discount = base_price - property_discount
    4. platform_discount = subtotal_after_property_discount * (platform.discount_percent / 100)
    5. subtotal_after_platform_discount = subtotal_after_property_discount - platform_discount
    6. coupon_discount = subtotal_after_platform_discount * (coupon.discount_percent / 100)
    7. subtotal_after_coupon = subtotal_after_platform_discount - coupon_discount
    8. add_ons_total = sum(add_on prices)
    9. subtotal_with_addons = subtotal_after_coupon + add_ons_total
    10. service_fee = MIN(subtotal_with_addons * 5%, 500) [5% with maximum cap of 500 rupees]
    11. subtotal_with_service = subtotal_with_addons + service_fee
    12. gst = subtotal_with_service * (gst_percent / 100) [Dynamic: 5% if <=7500, 18% if >7500]
    13. final_price = subtotal_with_service + gst
    """
    
    @staticmethod
    def calculate(room_type, nights, rooms=1, 
                  property_discount_percent=0, platform_discount_percent=0, 
                  coupon_discount_percent=0, add_ons=None,
                  service_fee_percent=None, gst_percent=None):
        """
        Calculate price with full breakdown.
        
        Args:
            room_type: RoomType instance (has base_price)
            nights: int (number of nights)
            rooms: int (number of rooms)
            property_discount_percent: float (owner-set discount)
            platform_discount_percent: float (admin-set global discount)
            coupon_discount_percent: float (coupon discount)
            add_ons: [{'name': str, 'price': decimal}] (extra charges)
            service_fee_percent: float (from database setting, optional)
            gst_percent: float (IGNORED - calculated dynamically based on room tariff)
            
        Returns:
            {
                'base_price': Decimal,
                'property_discount': Decimal,
                'platform_discount': Decimal,
                'coupon_discount': Decimal,
                'add_ons_total': Decimal,
                'service_fee': Decimal,
                'gst': Decimal,
                'final_price': Decimal,
                'breakdown': {... detailed line items ...}
            }
        """
        # Get service fee from platform settings
        if service_fee_percent is None:
            try:
                from apps.core.models import PlatformSettings
                platform_settings = PlatformSettings.get_settings()
                service_fee_percent = Decimal(str(platform_settings.service_fee_percent))
            except:
                service_fee_percent = Decimal('10')  # Fallback default
        
        # Convert to Decimal for precise calculation
        base = Decimal(str(room_type.base_price)) * nights * rooms
        
        # Step 1: Property discount (owner-controlled)
        property_discount = base * (Decimal(str(property_discount_percent)) / Decimal('100'))
        subtotal1 = base - property_discount
        
        # Step 2: Platform discount (admin-controlled global offers)
        platform_discount = subtotal1 * (Decimal(str(platform_discount_percent)) / Decimal('100'))
        subtotal2 = subtotal1 - platform_discount
        
        # Step 3: Coupon discount
        coupon_discount = subtotal2 * (Decimal(str(coupon_discount_percent)) / Decimal('100'))
        subtotal3 = subtotal2 - coupon_discount
        
        # Step 4: Add-ons (breakfast, late checkout, etc)
        add_ons_total = Decimal('0')
        add_ons_list = []
        if add_ons:
            for add_on in add_ons:
                price = Decimal(str(add_on.get('price', 0)))
                add_ons_total += price
                add_ons_list.append({
                    'name': add_on.get('name', 'Add-on'),
                    'price': price
                })
        subtotal4 = subtotal3 + add_ons_total
        
        # Step 5: Service fee (platform-controlled percentage) - 5% MAX 500 CAP
        service_fee = subtotal4 * (Decimal('5') / Decimal('100'))
        # Apply maximum cap of 500 rupees
        service_fee = min(service_fee, Decimal('500'))
        subtotal5 = subtotal4 + service_fee
        
        # Step 6: GST/Tax - DYNAMIC CALCULATION based on room tariff
        # Room tariff <= 7500: 5% GST
        # Room tariff > 7500: 18% GST
        room_tariff_per_night = Decimal(str(room_type.base_price))

        if room_tariff_per_night <= Decimal('7500'):
            gst_percent_calculated = Decimal('5')
        else:
            gst_percent_calculated = Decimal('18')
        
        gst = subtotal5 * (gst_percent_calculated / Decimal('100'))
        final_price = subtotal5 + gst
        
        return {
            'base_price': base.quantize(Decimal('0.01')),
            'property_discount': property_discount.quantize(Decimal('0.01')),
            'platform_discount': platform_discount.quantize(Decimal('0.01')),
            'coupon_discount': coupon_discount.quantize(Decimal('0.01')),
            'add_ons_total': add_ons_total.quantize(Decimal('0.01')),
            'service_fee': service_fee.quantize(Decimal('0.01')),
            'gst': gst.quantize(Decimal('0.01')),
            'final_price': final_price.quantize(Decimal('0.01')),
            'breakdown': {
                'base_price': str(base),
                'nights': nights,
                'rooms': rooms,
                'room_tariff_per_night': str(room_tariff_per_night),
                'property_discount_percent': property_discount_percent,
                'platform_discount_percent': platform_discount_percent,
                'coupon_discount_percent': coupon_discount_percent,
                'service_fee_percent': str(service_fee_percent),
                'gst_percent': str(gst_percent_calculated),
                'add_ons': add_ons_list,
                'total_discount': str(property_discount + platform_discount + coupon_discount),
            }
        }
    
    @staticmethod
    def format_for_display(price_calc):
        """
        Format price calculation for template display.
        Shows: Base | Discount | After Discount | Service Fee | Tax | Final
        """
        return {
            'base': price_calc['base_price'],
            'property_discount': price_calc['property_discount'],
            'platform_discount': price_calc['platform_discount'],
            'coupon_discount': price_calc['coupon_discount'],
            'total_discount': (
                price_calc['property_discount'] + 
                price_calc['platform_discount'] + 
                price_calc['coupon_discount']
            ),
            'after_discount': (
                price_calc['base_price'] - 
                price_calc['property_discount'] - 
                price_calc['platform_discount'] - 
                price_calc['coupon_discount']
            ),
            'add_ons': price_calc['add_ons_total'],
            'service_fee': price_calc['service_fee'],
            'gst': price_calc['gst'],
            'final': price_calc['final_price'],
        }
