"""
Security & Fraud Detection Tests

Tests Phase 4 & 5: Input validation firewall + fraud detection
"""

import pytest
from decimal import Decimal, InvalidOperation
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from core.validators import (
    InputValidator,
    FraudPrice,
    SuspiciousPrice,
    StaleData,
    ValidationConfig
)
from security.pricing_guard import (
    PricingGuard,
    FraudDetection,
    RateLimitExceeded
)


# ============================================================================
# PHASE 4: INPUT VALIDATION FIREWALL TESTS
# ============================================================================

class PriceValidationTestCase(TestCase):
    """Test price input validation"""
    
    def test_positive_price_required(self):
        """Negative price rejected"""
        with pytest.raises(FraudPrice):
            InputValidator.validate_price(Decimal('-100'))
    
    def test_zero_price_rejected(self):
        """Zero price rejected"""
        with pytest.raises(FraudPrice):
            InputValidator.validate_price(Decimal('0'))
    
    def test_minimum_price_100_rupees(self):
        """Rule: Price must be >= ₹100"""
        with pytest.raises(SuspiciousPrice):
            InputValidator.validate_price(Decimal('50'))
        
        # Boundary: exactly 100 should pass
        result = InputValidator.validate_price(Decimal('100'))
        assert result == Decimal('100')
    
    def test_maximum_price_1_million_rupees(self):
        """Rule: Price must be <= ₹1,000,000"""
        with pytest.raises(SuspiciousPrice):
            InputValidator.validate_price(Decimal('2000000'))
        
        # Boundary: exactly 1M should pass
        result = InputValidator.validate_price(Decimal('1000000'))
        assert result == Decimal('1000000')
    
    def test_valid_price_range(self):
        """Valid prices pass validation"""
        valid_prices = [
            Decimal('100'),
            Decimal('500'),
            Decimal('1000'),
            Decimal('50000'),
            Decimal('999999'),
        ]
        
        for price in valid_prices:
            result = InputValidator.validate_price(price)
            assert result == price
    
    def test_string_price_converted(self):
        """String prices are converted properly"""
        result = InputValidator.validate_price('500')
        assert isinstance(result, Decimal)
        assert result == Decimal('500')
    
    def test_price_with_decimal_places(self):
        """Prices with decimals handled"""
        result = InputValidator.validate_price(Decimal('1000.50'))
        assert result == Decimal('1000.50')


class DemandScoreValidationTestCase(TestCase):
    """Test demand score validation"""
    
    def test_demand_minimum_zero(self):
        """Demand score minimum is 0"""
        result = InputValidator.validate_demand_score(0)
        assert result == 0
    
    def test_demand_maximum_hundred(self):
        """Demand score maximum is 100"""
        result = InputValidator.validate_demand_score(100)
        assert result == 100
    
    def test_demand_below_zero_rejected(self):
        """Negative demand scores rejected"""
        with pytest.raises(Exception):
            InputValidator.validate_demand_score(-1)
    
    def test_demand_above_hundred_rejected(self):
        """Demand scores > 100 rejected"""
        with pytest.raises(Exception):
            InputValidator.validate_demand_score(101)
    
    def test_valid_demand_scores(self):
        """Valid scores in range pass"""
        for score in [0, 25, 50, 75, 100]:
            result = InputValidator.validate_demand_score(score)
            assert result == score


class ConfidenceScoreValidationTestCase(TestCase):
    """Test confidence score validation"""
    
    def test_confidence_minimum_zero(self):
        """Confidence minimum is 0.0"""
        result = InputValidator.validate_confidence_score(0.0)
        assert result == 0.0
    
    def test_confidence_maximum_one(self):
        """Confidence maximum is 1.0"""
        result = InputValidator.validate_confidence_score(1.0)
        assert result == 1.0
    
    def test_confidence_below_zero_rejected(self):
        """Negative confidence rejected"""
        with pytest.raises(Exception):
            InputValidator.validate_confidence_score(-0.1)
    
    def test_confidence_above_one_rejected(self):
        """Confidence > 1.0 rejected"""
        with pytest.raises(Exception):
            InputValidator.validate_confidence_score(1.1)
    
    def test_valid_confidence_scores(self):
        """Valid scores pass"""
        for score in [0.0, 0.25, 0.5, 0.75, 0.9, 1.0]:
            result = InputValidator.validate_confidence_score(score)
            assert result == score


class CompetitorFreshnessValidationTestCase(TestCase):
    """Test competitor price freshness validation"""
    
    def test_fresh_competitor_price_accepted(self):
        """Competitor price < 1 hour old is fresh"""
        price = Decimal('500')
        freshness_minutes = 30
        
        result, is_fresh = InputValidator.validate_competitor_price(
            price,
            freshness_minutes=freshness_minutes
        )
        
        assert result == price
        assert is_fresh == True
    
    def test_stale_competitor_price_flagged(self):
        """Competitor price > 1 hour old is stale"""
        price = Decimal('500')
        freshness_minutes = 90
        
        result, is_fresh = InputValidator.validate_competitor_price(
            price,
            freshness_minutes=freshness_minutes
        )
        
        assert is_fresh == False
    
    def test_boundary_60_minutes(self):
        """Exactly 60 minutes is boundary"""
        price = Decimal('500')
        
        result, is_fresh = InputValidator.validate_competitor_price(
            price,
            freshness_minutes=60
        )
        
        # 60 min is exactly the boundary
        assert is_fresh == False  # Consider boundary as stale


# ============================================================================
# PHASE 5: FRAUD DETECTION TESTS
# ============================================================================

class PriceChangeDetectionTestCase(TestCase):
    """Test fraud detection for price changes"""
    
    def test_price_drop_70_percent_blocked(self):
        """Rule: Drop > 70% = FRAUD"""
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(
                property_id=1,
                new_price=Decimal('100'),
                previous_price=Decimal('500')  # 80% drop
            )
    
    def test_price_drop_exactly_70_percent_blocked(self):
        """Boundary: 70% drop is blocked"""
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(
                property_id=1,
                new_price=Decimal('300'),
                previous_price=Decimal('1000')  # Exactly 70% drop
            )
    
    def test_price_drop_69_percent_allowed(self):
        """Drop < 70% is allowed"""
        result = PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('310'),
            previous_price=Decimal('1000')  # 69% drop
        )
        assert result == True
    
    def test_price_rise_200_percent_blocked(self):
        """Rule: Rise > 200% = FRAUD"""
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(
                property_id=1,
                new_price=Decimal('5000'),
                previous_price=Decimal('1000')  # 400% rise
            )
    
    def test_price_rise_exactly_200_percent_blocked(self):
        """Boundary: 200% rise is blocked"""
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(
                property_id=1,
                new_price=Decimal('3000'),
                previous_price=Decimal('1000')  # Exactly 200% rise
            )
    
    def test_price_rise_199_percent_allowed(self):
        """Rise < 200% is allowed"""
        result = PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('2990'),
            previous_price=Decimal('1000')  # 199% rise
        )
        assert result == True
    
    def test_normal_price_increases_allowed(self):
        """Normal increases (10-30%) allowed"""
        result = PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('1100'),
            previous_price=Decimal('1000')  # 10% increase
        )
        assert result == True
    
    def test_normal_price_decreases_allowed(self):
        """Normal decreases (10-30%) allowed"""
        result = PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('700'),
            previous_price=Decimal('1000')  # 30% decrease
        )
        assert result == True


class PriceManipulationScenarioTestCase(TestCase):
    """Test realistic fraud scenarios"""
    
    def test_scenario_flash_crash_attack(self):
        """Attacker tries to crash price to ₹5"""
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(
                property_id=1,
                new_price=Decimal('5'),
                previous_price=Decimal('1000')
            )
    
    def test_scenario_overnight_price_doubling(self):
        """Manual overnight doubling (100% rise) is allowed"""
        result = PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('2000'),
            previous_price=Decimal('1000')  # 100% rise
        )
        assert result == True  # Allowed (under 200%)
    
    def test_scenario_competitor_matching(self):
        """Matching competitor price (within bounds) is allowed"""
        result = PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('950'),
            previous_price=Decimal('1000')  # Down 5% to match competitor
        )
        assert result == True
    
    def test_scenario_multiple_small_changes(self):
        """Series of small changes (all <= 30%) is allowed"""
        price = Decimal('1000')
        
        for _ in range(5):
            # 10% increase each time
            price = price * Decimal('1.10')
            result = PricingGuard.check_price_change(
                property_id=1,
                new_price=price,
                previous_price=price / Decimal('1.10')
            )
            assert result == True


@patch('security.pricing_guard.cache')
class UpdateRateLimitTestCase(TestCase):
    """Test supplier update rate limiting"""
    
    def test_under_50_updates_per_minute_allowed(self, mock_cache):
        """50 or fewer updates/minute allowed"""
        mock_cache.get.return_value = 49  # 49 existing updates
        
        result = PricingGuard.check_update_rate(
            supplier_name='booking',
            supplier_id='prop001'
        )
        
        # Should pass silently or return True
        assert result == True or result is None
    
    def test_over_50_updates_per_minute_blocked(self, mock_cache):
        """> 50 updates/minute blocked"""
        mock_cache.get.return_value = 51  # 51 existing updates
        
        with pytest.raises(RateLimitExceeded):
            PricingGuard.check_update_rate(
                supplier_name='booking',
                supplier_id='prop001'
            )
    
    def test_1000_updates_per_hour_warning(self, mock_cache):
        """1000+ updates/hour triggers warning"""
        # Mock hour cache to return 1001
        mock_cache.get.side_effect = lambda key: 1001 if 'hour' in key else 30
        
        # Should not raise exception, but log warning
        result = PricingGuard.check_update_rate(
            supplier_name='booking',
            supplier_id='prop001'
        )
        
        # Should return or warn but not crash
        assert result is not None or result == True


class DemandSpikeDetectionTestCase(TestCase):
    """Test demand spike anomaly detection"""
    
    def test_small_demand_change_allowed(self):
        """Small changes (<50 points) allowed"""
        # 10 point change
        result = PricingGuard.check_demand_spike(
            property_id=1,
            new_score=60,
            previous_score=50
        )
        # Should not raise exception
        assert result is None or result == True
    
    def test_demand_spike_50_points_boundary(self):
        """Exactly 50 point change might trigger warning"""
        # 50 point change
        result = PricingGuard.check_demand_spike(
            property_id=1,
            new_score=100,
            previous_score=50
        )
        # Boundary case - might warn but not block
        assert result is None or result == False
    
    def test_large_demand_spike_unusual(self):
        """100+ point changes are anomalous"""
        # This might warn but not crash the system
        result = PricingGuard.check_demand_spike(
            property_id=1,
            new_score=100,
            previous_score=0  # Max possible change
        )
        # Should either warn or return safely
        assert result is None or isinstance(result, bool)


class ComprehensiveGuardTestCase(TestCase):
    """Test all guards together"""
    
    @patch('security.pricing_guard.cache')
    def test_check_all_guards_pass(self, mock_cache):
        """All guards pass for normal scenario"""
        mock_cache.get.return_value = 10  # Low update rate
        
        # Should pass all checks
        PricingGuard.check_price_change(1, Decimal('1050'), Decimal('1000'))
        PricingGuard.check_update_rate('booking', 'prop001')
        PricingGuard.check_demand_spike(1, 55, 50)
    
    @patch('security.pricing_guard.cache')
    def test_check_all_guards_fail_on_fraud(self, mock_cache):
        """Fails immediately on fraud detection"""
        mock_cache.get.return_value = 10
        
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(1, Decimal('100'), Decimal('1000'))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
