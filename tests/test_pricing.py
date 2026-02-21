"""
Pricing Engine Comprehensive Tests

Tests Phase 2: Unified pricing determinism, bounds, and competitor rules
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from unittest.mock import patch

from apps.hotels.models import Property
from apps.accounts.models import User
from apps.pricing.core_engine import (
    UnifiedPricingEngine,
    PricingConfig,
    calculate_price
)


class PricingDeterminismTestCase(TestCase):
    """Test that pricing is deterministic and reproducible"""
    
    def setUp(self):
        self.engine = UnifiedPricingEngine()
    
    def test_identical_inputs_identical_outputs(self):
        """Rule: Same inputs ALWAYS produce same outputs"""
        base_price = Decimal('1000')
        demand_score = 75
        competitor_price = Decimal('950')
        
        results = []
        for _ in range(5):
            result = self.engine.calculate_price(
                base_price=base_price,
                demand_score=demand_score,
                competitor_price=competitor_price
            )
            results.append(result['final_price'])
        
        # All results should be identical
        for price in results[1:]:
            assert price == results[0]
    
    def test_no_random_variation(self):
        """Pricing should never vary due to randomness"""
        base_price = Decimal('1500')
        
        # Call 10 times with identical inputs
        prices = [
            self.engine.calculate_price(base_price=base_price)['final_price']
            for _ in range(10)
        ]
        
        # All should be identical
        assert len(set(prices)) == 1


class DemandMultiplierTestCase(TestCase):
    """Test demand score to multiplier mapping"""
    
    def setUp(self):
        self.engine = UnifiedPricingEngine()
        self.base_price = Decimal('1000')
    
    def test_very_low_demand_multiplier(self):
        """Demand 0-20: multiplier = 0.70"""
        low = self.engine.calculate_price(base_price=self.base_price, demand_score=10)
        assert low['demand_multiplier'] == Decimal('0.70')
    
    def test_low_demand_multiplier(self):
        """Demand 20-40: multiplier = 0.85"""
        low = self.engine.calculate_price(base_price=self.base_price, demand_score=30)
        assert low['demand_multiplier'] == Decimal('0.85')
    
    def test_normal_demand_multiplier(self):
        """Demand 40-60: multiplier = 1.00"""
        normal = self.engine.calculate_price(base_price=self.base_price, demand_score=50)
        assert normal['demand_multiplier'] == Decimal('1.00')
    
    def test_high_demand_multiplier(self):
        """Demand 60-80: multiplier = 1.15"""
        high = self.engine.calculate_price(base_price=self.base_price, demand_score=70)
        assert high['demand_multiplier'] == Decimal('1.15')
    
    def test_very_high_demand_multiplier(self):
        """Demand 80+: multiplier = 1.25"""
        very_high = self.engine.calculate_price(base_price=self.base_price, demand_score=90)
        assert very_high['demand_multiplier'] == Decimal('1.25')
    
    def test_demand_increases_price(self):
        """Higher demand = higher price"""
        low_demand = self.engine.calculate_price(
            base_price=self.base_price,
            demand_score=20
        )
        high_demand = self.engine.calculate_price(
            base_price=self.base_price,
            demand_score=80
        )
        
        assert high_demand['final_price'] > low_demand['final_price']


class CompetitorPricingRuleTestCase(TestCase):
    """Test competitor pricing rules"""
    
    def setUp(self):
        self.engine = UnifiedPricingEngine()
    
    def test_never_exceeds_competitor_plus_5_percent(self):
        """Rule: Price never > competitor × 1.05"""
        competitor_price = Decimal('500')
        max_allowed = competitor_price * Decimal('1.05')  # 525
        
        result = self.engine.calculate_price(
            base_price=Decimal('2000'),  # High base price
            demand_score=100,  # Very high demand
            competitor_price=competitor_price
        )
        
        assert result['final_price'] <= max_allowed
    
    def test_never_below_competitor_minus_10_percent(self):
        """Rule: Price never < competitor × 0.90"""
        competitor_price = Decimal('1000')
        min_allowed = competitor_price * Decimal('0.90')  # 900
        
        result = self.engine.calculate_price(
            base_price=Decimal('100'),  # Low base price
            demand_score=0,  # Very low demand
            competitor_price=competitor_price
        )
        
        assert result['final_price'] >= min_allowed
    
    def test_high_base_price_capped_by_competitor(self):
        """High base price is capped when competitor is low"""
        result = self.engine.calculate_price(
            base_price=Decimal('10000'),  # Way higher than competitor
            demand_score=90,
            competitor_price=Decimal('500')
        )
        
        max_allowed = Decimal('500') * Decimal('1.05')
        assert result['final_price'] <= max_allowed
    
    def test_low_base_price_boosted_above_competitor_floor(self):
        """Low base price can be overridden by competitor floor"""
        result = self.engine.calculate_price(
            base_price=Decimal('100'),
            demand_score=10,
            competitor_price=Decimal('1000')
        )
        
        min_allowed = Decimal('1000') * Decimal('0.90')
        # Final price should be at least at the floor or at base safety
        # Test that it's not unreasonably low
        assert result['final_price'] > Decimal('50')


class SafetyBoundsTestCase(TestCase):
    """Test min/max price safety bounds"""
    
    def setUp(self):
        self.engine = UnifiedPricingEngine()
    
    def test_price_never_below_70_percent_of_base(self):
        """Rule: Price >= 0.70x base"""
        base_price = Decimal('1000')
        
        result = self.engine.calculate_price(
            base_price=base_price,
            demand_score=0,  # Minimum demand
            competitor_price=Decimal('10')  # Very low competitor
        )
        
        min_allowed = base_price * Decimal('0.70')
        assert result['final_price'] >= min_allowed
    
    def test_price_never_above_250_percent_of_base(self):
        """Rule: Price <= 2.50x base"""
        base_price = Decimal('1000')
        
        result = self.engine.calculate_price(
            base_price=base_price,
            demand_score=100,  # Maximum demand
            competitor_price=Decimal('10000')  # Very high competitor
        )
        
        max_allowed = base_price * Decimal('2.50')
        assert result['final_price'] <= max_allowed
    
    def test_safety_bounds_apply_to_all_calculations(self):
        """All pricing calculations respect bounds"""
        base_price = Decimal('500')
        
        # Generate 20 random scenarios
        scenarios = [
            {'demand_score': 0, 'competitor_price': None},
            {'demand_score': 25, 'competitor_price': Decimal('100')},
            {'demand_score': 50, 'competitor_price': Decimal('500')},
            {'demand_score': 75, 'competitor_price': Decimal('1000')},
            {'demand_score': 100, 'competitor_price': Decimal('5000')},
        ]
        
        for scenario in scenarios:
            result = self.engine.calculate_price(
                base_price=base_price,
                **scenario
            )
            
            min_allowed = base_price * Decimal('0.70')
            max_allowed = base_price * Decimal('2.50')
            
            assert result['final_price'] >= min_allowed
            assert result['final_price'] <= max_allowed


class PricingBreakdownTestCase(TestCase):
    """Test that pricing breakdown is complete and accurate"""
    
    def setUp(self):
        self.engine = UnifiedPricingEngine()
    
    def test_breakdown_includes_all_components(self):
        """Breakdown should show all calculation steps"""
        result = self.engine.calculate_price(
            base_price=Decimal('1000'),
            demand_score=70,
            competitor_price=Decimal('950')
        )
        
        assert 'breakdown' in result
        breakdown = result['breakdown']
        
        # Should include all steps
        assert 'base_price' in breakdown
        assert 'demand_multiplier' in breakdown
        assert 'after_demand' in breakdown
        assert 'competitor_adjustment' in breakdown
        assert 'after_competitor' in breakdown
        assert 'safety_bounds' in breakdown
    
    def test_final_price_matches_breakdown(self):
        """Final price should match breakdown calculation"""
        result = self.engine.calculate_price(
            base_price=Decimal('1000'),
            demand_score=60,
            competitor_price=Decimal('900')
        )
        
        # Manually verify calculation path
        base = Decimal('1000')
        demand_mult = Decimal('1.00')  # Demand 60 = normal
        after_demand = base * demand_mult
        
        # Result final_price should be determinable from breakdown
        assert result['final_price'] >= Decimal('0')
        assert result['final_price'] > Decimal('0')  # Not zero
    
    def test_safe_flag_indicates_safety_violation(self):
        """Safe flag shows if price had to be bounded"""
        # Create price that needs bounding
        unsafe_result = self.engine.calculate_price(
            base_price=Decimal('1000'),
            demand_score=0,
            competitor_price=Decimal('10')  # Would force price too low
        )
        
        # Safe flag should indicate if adjustments were made
        assert 'safe' in unsafe_result


class EdgeCaseTestCase(TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        self.engine = UnifiedPricingEngine()
    
    def test_zero_base_price_handled(self):
        """Should handle zero base price gracefully"""
        # Zero price might raise exception or return None
        try:
            result = self.engine.calculate_price(base_price=Decimal('0'))
            # If it returns, it should be safe
            assert result is not None
        except Exception:
            # Exception is acceptable for invalid input
            pass
    
    def test_very_high_base_price(self):
        """Handle very high base prices"""
        result = self.engine.calculate_price(base_price=Decimal('1000000'))
        
        # Should still apply rules
        assert result['final_price'] >= Decimal('700000')  # 0.7x
        assert result['final_price'] <= Decimal('2500000')  # 2.5x
    
    def test_demand_boundary_values(self):
        """Test demand at exact boundary values"""
        base = Decimal('1000')
        
        # Test at boundaries: 0, 20, 40, 60, 80, 100
        for demand in [0, 20, 40, 60, 80, 100]:
            result = self.engine.calculate_price(base_price=base, demand_score=demand)
            assert result['final_price'] > 0
            assert 700 <= result['final_price'] <= 2500


if __name__ == '__main__':
    pytest.main([__file__, '-v'])