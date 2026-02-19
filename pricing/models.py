from django.db import models
from decimal import Decimal
from core.models import TimeStampedModel


class PriceHistory(TimeStampedModel):
    """Track historical pricing for demand-based adjustments"""
    
    SERVICE_HOTEL = 'hotel'
    SERVICE_BUS = 'bus'
    SERVICE_CAB = 'cab'
    SERVICE_PACKAGE = 'package'
    
    SERVICE_CHOICES = [
        (SERVICE_HOTEL, 'Hotel'),
        (SERVICE_BUS, 'Bus'),
        (SERVICE_CAB, 'Cab'),
        (SERVICE_PACKAGE, 'Package'),
    ]
    
    # Service reference
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    service_id = models.PositiveIntegerField()  # ID of hotel, bus, cab, or package
    
    # Pricing data
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Demand metrics
    demand_score = models.PositiveIntegerField(default=50)  # 0-100 scale
    occupancy_percent = models.PositiveIntegerField(default=50)  # 0-100
    active_bookings = models.PositiveIntegerField(default=0)
    available_inventory = models.PositiveIntegerField(default=0)
    
    # Meta fields
    is_weekend = models.BooleanField(default=False)
    season = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('peak', 'Peak'),
        ],
        default='normal'
    )
    
    # Competitor data
    competitor_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    competitor_count = models.PositiveIntegerField(default=0)
    
    # Timestamp for historical lookback
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['service_type', 'service_id', '-recorded_at']),
            models.Index(fields=['recorded_at']),
            models.Index(fields=['demand_score']),
        ]
    
    def __str__(self):
        return f"{self.get_service_type_display()} #{self.service_id} - ₹{self.calculated_price} @ {self.recorded_at}"
    
    @classmethod
    def get_7day_average_demand(cls, service_type, service_id):
        """Get average demand score for last 7 days"""
        from django.utils import timezone
        from datetime import timedelta
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        prices = cls.objects.filter(
            service_type=service_type,
            service_id=service_id,
            recorded_at__gte=seven_days_ago
        ).values_list('demand_score', flat=True)
        
        if not prices:
            return 50  # Default neutral demand
        
        return sum(prices) // len(prices)
    
    @classmethod
    def get_price_trend(cls, service_type, service_id, days=7):
        """Get price trend for the last N days"""
        from django.utils import timezone
        from datetime import timedelta
        
        lookback = timezone.now() - timedelta(days=days)
        
        prices = cls.objects.filter(
            service_type=service_type,
            service_id=service_id,
            recorded_at__gte=lookback
        ).order_by('recorded_at').values('recorded_at', 'calculated_price', 'demand_score')
        
        return list(prices)

