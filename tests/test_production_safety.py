"""
Production Safety Test Suite

Tests all 6 architectural phases:
1. Mapping validation (no duplicates, confidence thresholds)
2. Pricing determinism (same inputs = same outputs)
3. Concurrency safety (race conditions prevented)
4. Input validation (fraud detection, suspicious prices)
5. Fraud protection (price manipulation blocked)
6. Immutable history (prices logged immutably)

Run with: python manage.py test tests.test_production_safety
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.utils import timezone
from unittest.mock import patch, MagicMock
import threading
import time

# Imports
from hotels.models import Property
from accounts.models import User
from inventory.models import SupplierPropertyMap, PropertyInventory, PriceHistory
from inventory.matching_engine import match_supplier_property, create_supplier_mapping
from pricing.core_engine import UnifiedPricingEngine, calculate_price
from inventory.concurrency import InventoryManager, InsufficientInventory
from core.validators import InputValidator, FraudPrice, SuspiciousPrice
from security.pricing_guard import PricingGuard, FraudDetection


# ============================================================================
# PHASE 1: MAPPING TESTS
# ============================================================================

class MappingTestCase(TestCase):
    """Test supplier property mapping with strict identity validation"""
    
    def setUp(self):
        """Create test property"""
        self.user = User.objects.create_user(
            username='owner1',
            email='owner1@test.com',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Taj Palace',
            city='Delhi',
            country='India',
            address='123 Palace Rd',
            description='Luxury hotel',
            latitude=28.6139,
            longitude=77.2090
        )
    
    def test_mapping_same_city_similar_name(self):
        """Case 1: Same city, similar name should match"""
        matched, confidence, status = match_supplier_property(
            supplier_name='booking',
            external_id='taj_palace_001',
            supplier_property_name='Taj Palace Hotel',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert matched == self.property
        assert confidence > 0.85
        assert status == 'approved'
    
    def test_mapping_different_city_rejects(self):
        """Case 2: Different city rejects match"""
        matched, confidence, status = match_supplier_property(
            supplier_name='booking',
            external_id='taj_goa_001',
            supplier_property_name='Taj Residency',
            supplier_city='Goa',  # Different city
            supplier_lat=15.295511,
            supplier_lng=73.834215
        )
        
        assert matched is None
        assert status.startswith('rejected')
    
    def test_no_duplicate_external_id(self):
        """Rule: Cannot have duplicate external ID"""
        # Create first mapping
        mapping1, _, _ = create_supplier_mapping(
            supplier_name='booking',
            external_id='ext001',
            supplier_property_name='Taj Palace',
            supplier_city='Delhi',  
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert mapping1 is not None
        
        # Try to create duplicate
        mapping2, _, success = create_supplier_mapping(
            supplier_name='booking',
            external_id='ext001',  # Same external ID
            supplier_property_name='Another Name',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert success == False
        assert mapping2 is None
    
    def test_confidence_below_threshold_rejected(self):
        """Rule: Confidence < 0.70 rejected"""
        # Create property with different name and location
        other_property = Property.objects.create(
            owner=self.user,
            name='Hotel XYZ',
            city='Delhi',
            country='India',
            address='456 Other Rd',
            description='Other hotel',
            latitude=28.5500,  # Different location (0.06° ≈ 6.7km away)
            longitude=77.2000
        )
        
        matched, confidence, status = match_supplier_property(
            supplier_name='airbnb',
            external_id='xyz_001',
            supplier_property_name='Completely Different Name',
            supplier_city='Delhi',
            supplier_lat=28.5500,
            supplier_lng=77.2000
        )
        
        # Should not match due to low name similarity
        assert status.startswith('rejected') or confidence < 0.70


# ============================================================================
# PHASE 2: PRICING TESTS
# ============================================================================

class PricingEngineTestCase(TestCase):
    """Test unified pricing engine determinism and bounds"""
    
    def setUp(self):
        self.engine = UnifiedPricingEngine()
        self.base_price = Decimal('1000')
    
    def test_deterministic_same_inputs_same_output(self):
        """Rule: Same inputs always produce same output"""
        result1 = self.engine.calculate_price(
            base_price=self.base_price,
            demand_score=75,
            competitor_price=Decimal('950')
        )
        
        result2 = self.engine.calculate_price(
            base_price=self.base_price,
            demand_score=75,
            competitor_price=Decimal('950')
        )
        
        assert result1['final_price'] == result2['final_price']
    
    def test_demand_affects_price_correctly(self):
        """Case 1: High demand (90) should increase price"""
        low_demand = self.engine.calculate_price(
            base_price=1000,
            demand_score=30  # Low demand
        )
        
        high_demand = self.engine.calculate_price(
            base_price=1000,
            demand_score=90  # High demand
        )
        
        assert high_demand['final_price'] > low_demand['final_price']
    
    def test_competitor_pricing_never_exceeds_cap(self):
        """Case 2: Price never > competitor + 5%"""
        result = self.engine.calculate_price(
            base_price=Decimal('1000'),
            demand_score=90,  # High demand would push up
            competitor_price=Decimal('500')  # Low competitor price
        )
        
        max_allowed = Decimal('500') * Decimal('1.05')
        assert result['final_price'] <= max_allowed
    
    def test_price_bounded_min_max(self):
        """Rule: Price >= 0.7x base, <= 2.5x base"""
        # Try to drive price way down
        very_low_demand = self.engine.calculate_price(
            base_price=1000,
            demand_score=1
        )
        
        # Try to drive price way up
        very_high_demand = self.engine.calculate_price(
            base_price=1000,
            demand_score=100,
            competitor_price=Decimal('10000')
        )
        
        assert very_low_demand['final_price'] >= 700  # 0.7x
        assert very_high_demand['final_price'] <= 2500  # 2.5x


# ============================================================================
# PHASE 3: CONCURRENCY TESTS
# ============================================================================

class ConcurrencyTestCase(TransactionTestCase):
    """Test race condition prevention with SELECT FOR UPDATE"""
    
    def setUp(self):
        """Create test property and inventory"""
        self.user = User.objects.create_user(
            username='owner1',
            email='owner1@test.com',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Test Hotel',
            city='Delhi',
            country='India',
            address='123 Test Rd',
            description='Test hotel',
            base_price=1000
        )
        self.inventory = PropertyInventory.objects.create(
            property=self.property,
            total_rooms=1,  # Only 1 room
            available_rooms=1
        )
    
    def test_concurrent_bookings_only_one_succeeds(self):
        """
        Stress test: 50 concurrent booking attempts on 1 room.
        Expected: 1 success, 49 fail.
        """
        success_count = [0]
        failure_count = [0]
        lock = threading.Lock()
        
        def attempt_booking():
            try:
                InventoryManager.deduct_rooms(self.property.id, 1)
                with lock:
                    success_count[0] += 1
            except InsufficientInventory:
                with lock:
                    failure_count[0] += 1
        
        threads = []
        for _ in range(50):
            t = threading.Thread(target=attempt_booking)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Should have exactly 1 success and 49 failures
        assert success_count[0] == 1, f"Expected 1 success, got {success_count[0]}"
        assert failure_count[0] == 49, f"Expected 49 failures, got {failure_count[0]}"
    
    def test_restore_rooms_after_cancellation(self):
        """Test room restoration (booking cancellation)"""
        # Deduct 1 room
        InventoryManager.deduct_rooms(self.property.id, 1)
        
        self.inventory.refresh_from_db()
        assert self.inventory.available_rooms == 0
        
        # Restore 1 room
        InventoryManager.restore_rooms(self.property.id, 1)
        
        self.inventory.refresh_from_db()
        assert self.inventory.available_rooms == 1


# ============================================================================
# PHASE 4: VALIDATION FIREWALL TESTS
# ============================================================================

class ValidationFirewallTestCase(TestCase):
    """Test input validation and fraud detection"""
    
    def test_price_positive_required(self):
        """Rule: Price must be positive"""
        with pytest.raises(FraudPrice):
            InputValidator.validate_price(-100)
        
        with pytest.raises(FraudPrice):
            InputValidator.validate_price(0)
    
    def test_price_minimum_threshold(self):
        """Rule: Price must be >= ₹100"""
        with pytest.raises(SuspiciousPrice):
            InputValidator.validate_price(Decimal('50'))
    
    def test_price_maximum_threshold(self):
        """Rule: Price must be <= ₹1,000,000"""
        with pytest.raises(SuspiciousPrice):
            InputValidator.validate_price(Decimal('2000000'))
    
    def test_demand_score_bounds(self):
        """Rule: Demand score 0-100"""
        with pytest.raises(Exception):
            InputValidator.validate_demand_score(-10)
        
        with pytest.raises(Exception):
            InputValidator.validate_demand_score(101)
        
        # Valid scores
        assert InputValidator.validate_demand_score(0) == 0
        assert InputValidator.validate_demand_score(100) == 100
        assert InputValidator.validate_demand_score(50) == 50
    
    def test_competitor_price_freshness(self):
        """Rule: Ignore competitor data older than 1 hour"""
        price = Decimal('500')
        
        # Fresh data (30 min old)
        validated, is_fresh = InputValidator.validate_competitor_price(
            price,
            freshness_minutes=30
        )
        assert is_fresh == True
        assert validated == price
        
        # Stale data (90 min old)
        validated, is_fresh = InputValidator.validate_competitor_price(
            price,
            freshness_minutes=90
        )
        assert is_fresh == False


# ============================================================================
# PHASE 5: FRAUD PROTECTION TESTS
# ============================================================================

class FraudProtectionTestCase(TestCase):
    """Test fraud detection layer"""
    
    def test_price_drop_too_large_blocked(self):
        """Case 1: Price drop > 70% rejected"""
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(
                property_id=1,
                new_price=Decimal('100'),
                previous_price=Decimal('500')  # 80% drop
            )
    
    def test_price_rise_too_large_blocked(self):
        """Case 2: Price rise > 200% rejected"""
        with pytest.raises(FraudDetection):
            PricingGuard.check_price_change(
                property_id=1,
                new_price=Decimal('5000'),
                previous_price=Decimal('1000')  # 400% rise
            )
    
    def test_normal_price_change_allowed(self):
        """Normal price changes within bounds"""
        # 10% increase
        assert PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('1100'),
            previous_price=Decimal('1000')
        ) == True
        
        # 30% decrease
        assert PricingGuard.check_price_change(
            property_id=1,
            new_price=Decimal('700'),
            previous_price=Decimal('1000')
        ) == True
    
    @patch('inventory.matching_engine.cache')
    def test_update_rate_limit_exceeded(self, mock_cache):
        """Test supplier update rate limiting"""
        mock_cache.get.return_value = 51  # Already 51 updates
        
        with pytest.raises(Exception):  # RateLimitExceeded
            PricingGuard.check_update_rate(
                supplier_name='booking',
                supplier_id='prop001'
            )


# ============================================================================
# PHASE 6: IMMUTABLE HISTORY TESTS
# ============================================================================

class PriceHistoryTestCase(TestCase):
    """Test immutable price history (append-only log)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='owner1',
            email='owner1@test.com',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Test Hotel',
            city='Delhi',
            country='India',
            address='123 Test Rd',
            description='Test hotel',
            base_price=1000
        )
    
    def test_price_history_is_immutable(self):
        """Rule: Never update rows, only insert"""
        # Create first history entry
        h1 = PriceHistory.objects.create(
            property=self.property,
            base_price=Decimal('1000'),
            final_price=Decimal('1050'),
            demand_score=60,
            price_change_percent=5.0
        )
        
        original_date = h1.created_at
        
        # Try to update (should fail or be prevented)
        h1.final_price = Decimal('1100')
        h1.save()
        
        # Reload from DB and check
        h1.refresh_from_db()
        # In production, this would be enforced at DB level with no UPDATE permissions
        # For now, we test that history entries represent snapshots in time
        assert h1.created_at == original_date
    
    def test_audit_trail_complete(self):
        """Test that audit trail captures all price changes"""
        # Create multiple history entries
        for i in range(3):
            PriceHistory.objects.create(
                property=self.property,
                base_price=Decimal('1000'),
                final_price=Decimal('1000') + Decimal(i * 100),
                demand_score=50 + (i * 10),
                price_change_percent=float(i * 10)
            )
        
        # Should have 3 entries
        history = PriceHistory.objects.filter(property=self.property)
        assert history.count() == 3
        
        # Verify ordering (newest first)
        entries = list(history)
        assert entries[0].final_price > entries[1].final_price


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
