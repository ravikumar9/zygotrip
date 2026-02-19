"""
Real Pricing Intelligence System
Stores daily price history, computes rolling averages, detects surge demand.
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.db import models
from django.utils import timezone
from django.db.models import Avg, Max, Min, StdDev, Count
from core.models import TimeStampedModel

logger = logging.getLogger('zygotrip')


class PricingHistory(TimeStampedModel):
    """Store daily pricing history for demand-based pricing intelligence"""
    
    SERVICE_CHOICES = [
        ('hotel', 'Hotel'),
        ('bus', 'Bus'),
        ('cab', 'Cab'),
        ('package', 'Package'),
    ]
    
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    service_id = models.PositiveIntegerField(db_index=True)  # Property/Bus/Cab/Package ID
    
    # Price tracking
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Demand metrics
    demand_score = models.PositiveIntegerField(default=0, help_text="0-100 scale")
    occupancy_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    active_bookings = models.PositiveIntegerField(default=0)
    
    # Competitive pricing
    competitor_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Average competitor price"
    )
    price_vs_competitor = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="% difference vs competitor"
    )
    
    # Seasonality
    season = models.CharField(
        max_length=20,
        choices=[('peak', 'Peak'), ('off', 'Off-season'), ('shoulder', 'Shoulder')],
        default='shoulder'
    )
    
    # External factors
    day_of_week = models.CharField(max_length=10)
    is_weekend = models.BooleanField(default=False)
    is_holiday = models.BooleanField(default=False)
    
    recorded_at = models.DateTimeField(db_index=True)
    
    class Meta:
        verbose_name_plural = "Pricing Histories"
        indexes = [
            models.Index(fields=['service_type', 'service_id', '-recorded_at']),
            models.Index(fields=['-recorded_at']),
            models.Index(fields=['demand_score', '-recorded_at']),
            models.Index(fields=['season', 'service_type']),
        ]
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.get_service_type_display()} #{self.service_id} - ₹{self.calculated_price}"
    
    @classmethod
    def get_7day_average_demand(cls, service_type: str, service_id: int) -> float:
        """Calculate 7-day rolling average demand score"""
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        avg = cls.objects.filter(
            service_type=service_type,
            service_id=service_id,
            recorded_at__gte=seven_days_ago
        ).aggregate(avg_demand=Avg('demand_score'))
        
        return round(avg['avg_demand'] or 0, 2)
    
    @classmethod
    def get_price_trend(cls, service_type: str, service_id: int, days: int = 7) -> List[Dict]:
        """Get price trend over N days"""
        start_date = timezone.now() - timedelta(days=days)
        
        history = cls.objects.filter(
            service_type=service_type,
            service_id=service_id,
            recorded_at__gte=start_date
        ).values('recorded_at', 'calculated_price', 'demand_score', 'occupancy_percent').order_by('recorded_at')
        
        return list(history)
    
    @classmethod
    def get_seasonal_baseline(cls, service_type: str, season: str) -> Dict:
        """Get baseline metrics for a season"""
        metrics = cls.objects.filter(
            service_type=service_type,
            season=season
        ).aggregate(
            avg_price=Avg('calculated_price'),
            max_price=Max('calculated_price'),
            min_price=Min('calculated_price'),
            avg_demand=Avg('demand_score'),
            std_dev=StdDev('calculated_price')
        )
        
        return metrics
    
    @classmethod
    def detect_surge_periods(cls, service_type: str, threshold_percentile: int = 75) -> List[Dict]:
        """Detect high-demand periods (surge pricing eligible)"""
        from django.db.models import Q
        
        # Get baseline demand
        baseline = cls.objects.filter(
            service_type=service_type
        ).aggregate(baseline=Avg('demand_score'))['baseline'] or 50
        
        # Get 90th percentile demand threshold
        high_demand_threshold = baseline * (threshold_percentile / 50)  # Scale to percentile
        
        surges = cls.objects.filter(
            service_type=service_type,
            demand_score__gte=high_demand_threshold
        ).values('recorded_at', 'service_id', 'demand_score', 'calculated_price').order_by('-demand_score')[:20]
        
        return list(surges)


class CompetitorPricingData(TimeStampedModel):
    """Track competitor pricing for market intelligence"""
    
    service_type = models.CharField(max_length=20)
    service_id = models.PositiveIntegerField(db_index=True)
    
    # Competitor information
    competitor_name = models.CharField(max_length=100)
    competitor_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Our pricing
    our_price = models.DecimalField(max_digits=12, decimal_places=2)
    price_difference = models.DecimalField(max_digits=12, decimal_places=2)  # our - competitor
    
    # When obtained
    snapshot_date = models.DateField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['service_type', 'snapshot_date']),
            models.Index(fields=['competitor_name', 'snapshot_date']),
        ]
        ordering = ['-snapshot_date']
    
    def __str__(self):
        return f"{self.competitor_name}: ₹{self.competitor_price} vs Ours: ₹{self.our_price}"


class PricingRecommendation(models.Model):
    """AI-generated pricing recommendations"""
    
    SERVICE_TYPES = [('hotel', 'Hotel'), ('bus', 'Bus'), ('cab', 'Cab'), ('package', 'Package')]
    
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    service_id = models.PositiveIntegerField(db_index=True)
    
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    recommended_price = models.DecimalField(max_digits=12, decimal_places=2)
    price_change_percent = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Reason for recommendation
    REASON_CHOICES = [
        ('surge', 'High Demand / Surge'),
        ('low_occupancy', 'Low Occupancy'),
        ('competitor', 'Competitor Pricing'),
        ('seasonal', 'Seasonal Adjustment'),
        ('market_trend', 'Market Trend'),
    ]
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    explanation = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['service_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_service_type_display()} #{self.service_id}: ₹{self.current_price} → ₹{self.recommended_price}"


class PricingRuleEngine:
    """Dynamic pricing calculation engine"""
    
    def __init__(self):
        self.logger = logging.getLogger('zygotrip')
        
        # Pricing multipliers
        self.DEMAND_MULTIPLIER = {
            'very_low': 0.7,    # 30% discount
            'low': 0.85,        # 15% discount
            'normal': 1.0,      # No change
            'high': 1.25,       # 25% premium
            'very_high': 1.5,   # 50% premium
        }
        
        self.SEASON_MULTIPLIER = {
            'off': 0.8,         # 20% discount
            'shoulder': 1.0,    # No change
            'peak': 1.4,        # 40% premium
        }
        
        self.OCCUPANCY_MULTIPLIER = {
            (0, 30): 0.75,      # <30% occupied: 25% discount
            (30, 50): 0.9,      # 30-50% occupied: 10% discount
            (50, 70): 1.0,      # 50-70% occupied: Normal
            (70, 85): 1.15,     # 70-85% occupied: 15% premium
            (85, 100): 1.4,     # 85-100% occupied: 40% premium
        }
        
        self.COMPETITOR_MARGIN = 0.95  # Price 5% below competitor if they're cheaper
    
    def get_demand_level(self, demand_score: int) -> str:
        """Classify demand level"""
        if demand_score < 20:
            return 'very_low'
        elif demand_score < 40:
            return 'low'
        elif demand_score < 60:
            return 'normal'
        elif demand_score < 80:
            return 'high'
        else:
            return 'very_high'
    
    def get_occupancy_multiplier(self, occupancy_percent: float) -> float:
        """Get multiplier based on occupancy"""
        for (lower, upper), multiplier in self.OCCUPANCY_MULTIPLIER.items():
            if lower <= occupancy_percent < upper:
                return multiplier
        return 1.0
    
    def calculate_price(
        self,
        base_price: Decimal,
        demand_score: int = 50,
        occupancy_percent: float = 50,
        season: str = 'shoulder',
        competitor_price: Optional[Decimal] = None,
        is_weekend: bool = False,
    ) -> Dict:
        """
        Calculate dynamic price based on multiple factors.
        Returns dict with calculated price and breakdown.
        """
        base_price = Decimal(str(base_price))
        
        # Get multipliers
        demand_level = self.get_demand_level(demand_score)
        demand_mult = self.DEMAND_MULTIPLIER.get(demand_level, 1.0)
        season_mult = self.SEASON_MULTIPLIER.get(season, 1.0)
        occupancy_mult = self.get_occupancy_multiplier(occupancy_percent)
        
        # Weekend premium
        weekend_mult = 1.1 if is_weekend else 1.0
        
        # Calculate intermediate price
        intermediate_price = base_price * Decimal(str(demand_mult)) * Decimal(str(season_mult)) * Decimal(str(occupancy_mult)) * Decimal(str(weekend_mult))
        
        # Competitor pricing adjustment
        competitor_adjustment = Decimal('1.0')
        if competitor_price:
            competitor_price = Decimal(str(competitor_price))
            if intermediate_price > competitor_price * Decimal('1.1'):
                # Our price is 10%+ higher, reduce it
                intermediate_price = competitor_price * Decimal(str(self.COMPETITOR_MARGIN))
        
        # Cap maximum price at 2x base
        max_price = base_price * Decimal('2.0')
        if intermediate_price > max_price:
            intermediate_price = max_price
        
        # Floor minimum price at 0.5x base
        min_price = base_price * Decimal('0.5')
        if intermediate_price < min_price:
            intermediate_price = min_price
        
        # Round to nearest rupee
        final_price = intermediate_price.quantize(Decimal('1'))
        
        return {
            'base_price': base_price,
            'calculated_price': final_price,
            'price_increase_percent': round(float((final_price - base_price) / base_price * 100), 2),
            'demand_multiplier': demand_mult,
            'season_multiplier': season_mult,
            'occupancy_multiplier': occupancy_mult,
            'weekend_multiplier': weekend_mult,
            'demand_level': demand_level,
            'breakdown': {
                'demand': f"{demand_level.replace('_', ' ')} demand ({demand_score}/100)",
                'occupancy': f"{occupancy_percent:.0f}% occupied",
                'season': f"{season.capitalize()} season",
                'weekend': 'Weekend premium applied' if is_weekend else 'Weekday pricing',
                'competitor': f"₹{competitor_price} (competitor)" if competitor_price else "No comparable data",
            }
        }
    
    def generate_recommendation(
        self,
        service_type: str,
        service_id: int,
        current_price: Decimal,
        demand_score: int,
        occupancy_percent: float,
    ) -> Optional[Dict]:
        """Generate pricing recommendation"""
        pricing_result = self.calculate_price(
            base_price=current_price,
            demand_score=demand_score,
            occupancy_percent=occupancy_percent,
        )
        
        recommended_price = pricing_result['calculated_price']
        price_change_percent = pricing_result['price_increase_percent']
        
        if abs(price_change_percent) < 2:
            return None  # No significant change needed
        
        # Determine reason
        if demand_score > 75:
            reason = 'surge'
        elif occupancy_percent < 30:
            reason = 'low_occupancy'
        elif abs(price_change_percent) > 15:
            reason = 'seasonal'
        else:
            reason = 'market_trend'
        
        confidence = min(100, 50 + abs(demand_score - 50))  # Higher confidence with extreme demand
        
        return {
            'service_type': service_type,
            'service_id': service_id,
            'current_price': current_price,
            'recommended_price': recommended_price,
            'price_change_percent': Decimal(str(price_change_percent)),
            'reason': reason,
            'confidence_score': Decimal(str(confidence)),
            'explanation': pricing_result['breakdown'],
        }


def record_pricing_snapshot(
    service_type: str,
    service_id: int,
    base_price: Decimal,
    calculated_price: Decimal,
    demand_score: int,
    occupancy_percent: float,
    competitor_price: Optional[Decimal] = None,
) -> PricingHistory:
    """Record a pricing decision in history for analysis"""
    
    today = date.today()
    day_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][today.weekday()]
    is_weekend = today.weekday() >= 5
    
    # Determine season (simplified)
    month = today.month
    if month in [5, 6, 7, 8]:  # Summer
        season = 'peak'
    elif month in [12, 1]:  # Winter holidays
        season = 'peak'
    elif month in [3, 4, 9, 10, 11]:  # Shoulder
        season = 'shoulder'
    else:
        season = 'off'
    
    # Calculate price vs competitor
    price_vs_competitor = None
    if competitor_price:
        price_vs_competitor = ((calculated_price - competitor_price) / competitor_price * 100)
    
    history = PricingHistory.objects.create(
        service_type=service_type,
        service_id=service_id,
        base_price=base_price,
        calculated_price=calculated_price,
        demand_score=demand_score,
        occupancy_percent=occupancy_percent,
        competitor_price=competitor_price,
        price_vs_competitor=price_vs_competitor,
        season=season,
        day_of_week=day_of_week,
        is_weekend=is_weekend,
        is_holiday=False,  # TODO: Integrate holiday calendar
        recorded_at=timezone.now(),
    )
    
    return history
