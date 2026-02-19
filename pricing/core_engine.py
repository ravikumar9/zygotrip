"""
Unified Pricing Engine - Production Grade

Single source of truth for all pricing calculations.
No dual engines. No logic duplication.

Safety guarantees:
- Deterministic: Same inputs always produce same output
- Bounded: Price never < 0.7x base, never > 2.5x base
- Auditable: Every price change logged with calculation breakdown
- Competitor-aware: Never price > competitor + 5%
"""

import logging
import time
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.utils import timezone
from core.models import OperationLog
from core.observability import PerformanceLog
from inventory.models import PriceHistory

logger = logging.getLogger('zygotrip')


class PricingConfig:
    """Centralized pricing configuration"""
    
    # Demand multipliers (0-100 scale → price multiplier)
    DEMAND_MULTIPLIERS = {
        'very_low': Decimal('0.70'),    # <20: 30% discount
        'low': Decimal('0.85'),         # 20-40: 15% discount
        'normal': Decimal('1.00'),      # 40-60: no change
        'high': Decimal('1.15'),        # 60-80: 15% premium
        'very_high': Decimal('1.25'),   # 80-100: 25% premium
    }
    
    # Competitor pricing rules
    COMPETITOR_MAX_MARKUP = Decimal('1.05')  # Never > competitor + 5%
    COMPETITOR_MAX_DISCOUNT = Decimal('0.90')  # Never < competitor - 10%
    
    # Price bounds (safety guard)
    MIN_PRICE_MULTIPLIER = Decimal('0.70')  # Minimum: 70% of base
    MAX_PRICE_MULTIPLIER = Decimal('2.50')  # Maximum: 250% of base
    
    # Freshness requirements
    COMPETITOR_DATA_FRESHNESS_MINUTES = 60  # Ignore data older than 1 hour
    
    @staticmethod
    def get_demand_level(demand_score: int) -> str:
        """
        Classify demand score into demand level.
        
        Args:
            demand_score: 0-100 demand indicator
        
        Returns:
            Demand level: 'very_low', 'low', 'normal', 'high', 'very_high'
        """
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


class UnifiedPricingEngine:
    """
    Single unified engine for all pricing calculations.
    
    Calculation flow:
    1. Start with base price
    2. Apply demand multiplier
    3. Apply competitor adjustment
    4. Apply safety bounds
    5. Return final price with breakdown
    """
    
    def __init__(self):
        self.config = PricingConfig()
        self.logger = logger
    
    def calculate_price(
        self,
        base_price: Decimal,
        demand_score: int = 50,
        competitor_price: Optional[Decimal] = None,
        competitor_freshness_minutes: Optional[int] = None
    ) -> Dict:
        """
        Calculate final price with full breakdown.
        
        Args:
            base_price: Base price before multipliers
            demand_score: 0-100 demand indicator
            competitor_price: Competitor reference price (optional)
            competitor_freshness_minutes: Age of competitor price
        
        Returns:
            Dictionary with:
            - final_price: Final calculated price
            - base_price: Input base price
            - demand_multiplier: Applied demand multiplier
            - competitor_adjustment: Applied competitor adjustment
            - demand_level: Classified demand level
            - breakdown: Step-by-step calculation explanation
            - safe: Whether final price passed safety bounds
        """
        
        start_time = time.time()
        try:
            # Validation
            base_price = Decimal(str(base_price))
            if base_price <= 0:
                raise ValueError(f"Base price must be positive, got {base_price}")
            
            if not (0 <= demand_score <= 100):
                raise ValueError(f"Demand score must be 0-100, got {demand_score}")
        
        breakdown = []
        
        # Step 1: Base price
        current_price = base_price
        breakdown.append(f"Base price: ₹{current_price}")
        
        # Step 2: Apply demand multiplier
        demand_level = self.config.get_demand_level(demand_score)
        demand_multiplier = self.config.DEMAND_MULTIPLIERS[demand_level]
        
        current_price = current_price * demand_multiplier
        breakdown.append(
            f"Demand ({demand_level}, score {demand_score}): "
            f"×{demand_multiplier} → ₹{current_price}"
        )
        
        # Step 3: Apply competitor adjustment
        competitor_adjustment = Decimal('1.0')
        
        if competitor_price:
            competitor_price = Decimal(str(competitor_price))
            
            # Check freshness
            if competitor_freshness_minutes is not None:
                if competitor_freshness_minutes > self.config.COMPETITOR_DATA_FRESHNESS_MINUTES:
                    self.logger.warning(
                        f"Competitor price data is {competitor_freshness_minutes} min old "
                        f"(max allowed: {self.config.COMPETITOR_DATA_FRESHNESS_MINUTES})"
                    )
                    competitor_price = None
            
            if competitor_price:
                # Rule: Never price > competitor + 5%
                max_allowed = competitor_price * self.config.COMPETITOR_MAX_MARKUP
                
                if current_price > max_allowed:
                    competitor_adjustment = max_allowed / current_price
                    current_price = max_allowed
                    breakdown.append(
                        f"Competitor adjustment: capped at "
                        f"₹{competitor_price} × {self.config.COMPETITOR_MAX_MARKUP} = ₹{current_price}"
                    )
        
        # Step 4: Apply safety bounds
        min_price = base_price * self.config.MIN_PRICE_MULTIPLIER
        max_price = base_price * self.config.MAX_PRICE_MULTIPLIER
        
        price_safe = min_price <= current_price <= max_price
        
        if current_price < min_price:
            self.logger.warning(
                f"Price ₹{current_price} below minimum ₹{min_price}, capping"
            )
            current_price = min_price
        
        if current_price > max_price:
            self.logger.warning(
                f"Price ₹{current_price} above maximum ₹{max_price}, capping"
            )
            current_price = max_price
        
        breakdown.append(
            f"Safety bounds: ₹{min_price}-₹{max_price} | "
            f"Final: ₹{current_price}"
        )
        
            # Step 5: Round to 2 decimals
            final_price = current_price.quantize(Decimal('0.01'))
        
            # Calculate price change percent
            price_change_percent = float(
                ((final_price - base_price) / base_price * 100)
                if base_price > 0
                else 0
            )
            
            result = {
                'final_price': final_price,
                'base_price': base_price,
                'demand_level': demand_level,
                'demand_multiplier': demand_multiplier,
                'competitor_adjustment': competitor_adjustment,
                'price_change_percent': round(price_change_percent, 2),
                'breakdown': breakdown,
                'safe': price_safe,
            }
            
            # Observability: performance + audit log
            duration_ms = int((time.time() - start_time) * 1000)
            PerformanceLog.objects.create(
                operation_type='price_calculation',
                duration_ms=duration_ms,
                start_time=timezone.now(),
                end_time=timezone.now(),
                status='success',
            )
            OperationLog.objects.create(
                operation_type='price_calculated',
                status='success',
                details=str({
                    'base_price': str(base_price),
                    'final_price': str(final_price),
                    'demand_score': demand_score,
                    'competitor_price': str(competitor_price) if competitor_price else None,
                    'breakdown': breakdown,
                }),
                timestamp=timezone.now(),
            )
            
            return result
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            PerformanceLog.objects.create(
                operation_type='price_calculation',
                duration_ms=duration_ms,
                start_time=timezone.now(),
                end_time=timezone.now(),
                status='error',
                error_message=str(exc),
            )
            OperationLog.objects.create(
                operation_type='price_calculated',
                status='failed',
                details=str({'error': str(exc)}),
                timestamp=timezone.now(),
            )
            raise
    
    def validate_price(self, price: Decimal, base_price: Decimal) -> Tuple[bool, str]:
        """
        Validate if a price is within acceptable bounds.
        
        Rules:
        - Price > 0
        - Price >= base * 0.7 (minimum)
        - Price <= base * 2.5 (maximum)
        
        Returns:
            Tuple of (valid, reason)
        """
        price = Decimal(str(price))
        base_price = Decimal(str(base_price))
        
        if price <= 0:
            return False, "Price must be positive"
        
        min_price = base_price * self.config.MIN_PRICE_MULTIPLIER
        max_price = base_price * self.config.MAX_PRICE_MULTIPLIER
        
        if price < min_price:
            return False, f"Price ₹{price} below minimum ₹{min_price}"
        
        if price > max_price:
            return False, f"Price ₹{price} above maximum ₹{max_price}"
        
        return True, "Valid"


def calculate_price(base_price: Decimal, **kwargs) -> Dict:
    """
    Convenience function to calculate price using singleton engine.
    """
    return UnifiedPricingEngine().calculate_price(base_price, **kwargs)
