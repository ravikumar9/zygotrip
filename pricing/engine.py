# pricing/engine.py - Price Intelligence Engine

from decimal import Decimal
from django.utils import timezone
from datetime import datetime, date


class PricingEngine:
    """Dynamic pricing engine with demand-based multipliers"""
    
    @staticmethod
    def calculate_price(base_price, demand_level='normal', occupancy_percent=50, 
                       is_weekend=False, competitor_price=None, season='normal'):
        """
        Calculate dynamic price based on multiple factors.
        
        Args:
            base_price: Base price in rupees (Decimal)
            demand_level: 'low', 'normal', 'high'
            occupancy_percent: 0-100 occupancy percentage
            is_weekend: Boolean for weekend pricing
            competitor_price: Price from competitors (optional)
            season: 'low', 'normal', 'peak'
        
        Returns:
            Decimal: Calculated price with all multipliers applied
        """
        
        price = Decimal(str(base_price))
        
        # Demand multiplier
        demand_multiplier = Decimal('1.0')
        if demand_level == 'high':
            demand_multiplier = Decimal('1.20')  # +20%
        elif demand_level == 'low':
            demand_multiplier = Decimal('0.90')  # -10%
        
        price *= demand_multiplier
        
        # Occupancy multiplier - high occupancy increases price
        if occupancy_percent > 80:
            occupancy_multiplier = Decimal('1.15')  # +15%
        elif occupancy_percent > 60:
            occupancy_multiplier = Decimal('1.08')  # +8%
        else:
            occupancy_multiplier = Decimal('1.0')
        
        price *= occupancy_multiplier
        
        # Weekend multiplier
        if is_weekend:
            price *= Decimal('1.10')  # +10%
        
        # Seasonal multiplier
        seasonal_multiplier = Decimal('1.0')
        if season == 'peak':
            seasonal_multiplier = Decimal('1.25')  # +25%
        elif season == 'low':
            seasonal_multiplier = Decimal('0.85')  # -15%
        
        price *= seasonal_multiplier
        
        # Competitor price floor
        if competitor_price:
            competitor_floor = Decimal(str(competitor_price)) * Decimal('0.98')  # 2% cheaper
            if price > competitor_floor:
                price = competitor_floor
        
        # Round to nearest rupee
        return price.quantize(Decimal('1.00'))
    
    @staticmethod
    def get_demand_level(bookings_count, available_count):
        """
        Determine demand level based on booking ratio.
        """
        if available_count == 0:
            return 'high'
        
        occupancy_ratio = bookings_count / (bookings_count + available_count)
        
        if occupancy_ratio > 0.7:
            return 'high'
        elif occupancy_ratio > 0.4:
            return 'normal'
        else:
            return 'low'
    
    @staticmethod
    def is_weekend(check_date):
        """Check if date is weekend"""
        if isinstance(check_date, str):
            check_date = datetime.fromisoformat(check_date).date()
        return check_date.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    @staticmethod
    def get_season(check_date):
        """
        Determine season based on date.
        Peak: Dec 15 - Jan 5, Jun 15 - Jul 31
        Low: May 15 - Jun 14
        Normal: Rest
        """
        if isinstance(check_date, str):
            check_date = datetime.fromisoformat(check_date).date()
        
        month_day = (check_date.month, check_date.day)
        
        # Peak season
        if (month_day >= (12, 15) or month_day <= (1, 5)):
            return 'peak'
        if (month_day >= (6, 15) and month_day <= (7, 31)):
            return 'peak'
        
        # Low season
        if month_day >= (5, 15) and month_day <= (6, 14):
            return 'low'
        
        return 'normal'
