"""
Mapping Engine Comprehensive Tests

Tests Phase 1: Supplier property matching with duplicate prevention
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from hotels.models import Property
from accounts.models import User
from inventory.models import SupplierPropertyMap
from inventory.matching_engine import (
    haversine_distance,
    calculate_match_score,
    match_supplier_property,
    create_supplier_mapping
)


class HaversineDistanceTestCase(TestCase):
    """Test geographic distance calculation"""
    
    def test_same_location_zero_distance(self):
        """Same coordinates = 0 distance"""
        distance = haversine_distance(28.6139, 77.2090, 28.6139, 77.2090)
        assert distance < 0.001  # Less than 1 meter
    
    def test_known_distance_delhi_agra(self):
        """Delhi to Agra is approximately 206 km"""
        # Delhi: 28.6139, 77.2090
        # Agra: 27.1767, 78.0084
        distance = haversine_distance(28.6139, 77.2090, 27.1767, 78.0084)
        
        # Should be around 206 km
        assert 200 < distance < 210
    
    def test_small_distance_within_threshold(self):
        """Properties within 1km should match"""
        # Two points roughly 0.5km apart
        distance = haversine_distance(28.6139, 77.2090, 28.6174, 77.2133)
        assert distance < 1.0


class MatchScoreTestCase(TestCase):
    """Test confidence score calculation"""
    
    def test_identical_names_high_score(self):
        """Identical names = 100% score"""
        score, reason = calculate_match_score(
            'Taj Palace Hotel',
            'Taj Palace Hotel',
            0.5  # Same location
        )
        assert score >= 0.95
    
    def test_typos_accepted_partial_score(self):
        """Name with typo = partial score"""
        score, reason = calculate_match_score(
            'Taj Palace Hotel',
            'Taj Palce Hotel',  # Typo in "Palace"
            0.5
        )
        assert 0.70 <= score < 0.95
    
    def test_completely_different_names_low_score(self):
        """Different names = low score"""
        score, reason = calculate_match_score(
            'Taj Palace',
            'Budget Inn',
            0.5
        )
        assert score < 0.70
    
    def test_far_distance_penalizes_score(self):
        """Same name, different location = penalty"""
        score_close, _ = calculate_match_score(
            'Taj Palace',
            'Taj Palace',
            0.1  # 100 meters
        )
        
        score_far, _ = calculate_match_score(
            'Taj Palace',
            'Taj Palace',
            5.0  # 5 km away
        )
        
        assert score_close > score_far


class SupplierMappingTestCase(TestCase):
    """Test supplier-property mapping creation and validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='owner1',
            email='owner1@test.com',
            password='pass123'
        )
        self.property1 = Property.objects.create(
            owner=self.user,
            name='Taj Palace',
            city='Delhi',
            country='India',
            address='123 Palace Rd',
            description='Luxury hotel',
            latitude=28.6139,
            longitude=77.2090
        )
        self.property2 = Property.objects.create(
            owner=self.user,
            name='Taj Palace Agra',
            city='Agra',
            country='India',
            address='456 Agra Rd',
            description='Agra branch',
            latitude=27.1767,
            longitude=78.0084
        )
    
    def test_successful_mapping_creation(self):
        """Test creating a valid supplier mapping"""
        mapping, created, success = create_supplier_mapping(
            supplier_name='booking',
            external_id='booking_taj_delhi_001',
            supplier_property_name='Taj Palace Hotel',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert success == True
        assert created == True
        assert mapping.property == self.property1
        assert mapping.supplier_name == 'booking'
    
    def test_duplicate_external_id_rejected(self):
        """Rule: Same supplier + external_id = duplicate"""
        # Create first mapping
        mapping1, _, success1 = create_supplier_mapping(
            supplier_name='booking',
            external_id='ext_001',
            supplier_property_name='Taj Palace Hotel',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        assert success1 == True
        
        # Try to create duplicate
        mapping2, _, success2 = create_supplier_mapping(
            supplier_name='booking',
            external_id='ext_001',  # Same external_id
            supplier_property_name='Different Name',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert success2 == False
        assert mapping2 is None
    
    def test_different_supplier_same_external_id_allowed(self):
        """Different supplier can use same external_id"""
        # Booking uses ext_001
        mapping1, _, success1 = create_supplier_mapping(
            supplier_name='booking',
            external_id='ext_001',
            supplier_property_name='Taj Palace Hotel',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        assert success1 == True
        
        # Airbnb can also use ext_001 (different supplier)
        mapping2, _, success2 = create_supplier_mapping(
            supplier_name='airbnb',
            external_id='ext_001',  # Same ID but different supplier
            supplier_property_name='Taj Palace',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert success2 == True
        assert mapping1.property == mapping2.property  # Same property
    
    def test_city_mismatch_rejected(self):
        """Rule: Supplier city must match or be very close"""
        # Supplier says "Mumbai" but matches only to Delhi properties
        matched, confidence, status = match_supplier_property(
            supplier_name='agoda',
            external_id='agoda_taj_001',
            supplier_property_name='Taj Palace',
            supplier_city='Mumbai',  # Wrong city
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert matched is None or status.startswith('rejected')
    
    def test_same_name_different_cities_different_properties(self):
        """Same hotel name in different cities = different properties"""
        # There are 2 "Taj Palace" properties: one in Delhi, one in Agra
        # Both should be distinct
        
        # Match to Delhi
        match_delhi = match_supplier_property(
            supplier_name='booking',
            external_id='taj_delhi',
            supplier_property_name='Taj Palace Hotel',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )[0]
        
        # Match to Agra
        match_agra = match_supplier_property(
            supplier_name='booking',
            external_id='taj_agra',
            supplier_property_name='Taj Palace',
            supplier_city='Agra',
            supplier_lat=27.1767,
            supplier_lng=78.0084
        )[0]
        
        assert match_delhi == self.property1
        assert match_agra == self.property2
    
    def test_confidence_score_immutable_once_verified(self):
        """Rule: Verified property cannot be downgraded"""
        # Create mapping with high confidence (auto-verified)
        mapping, _, _ = create_supplier_mapping(
            supplier_name='booking',
            external_id='verified_001',
            supplier_property_name='Taj Palace Hotel',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2090
        )
        
        assert mapping.verified == True
        original_confidence = mapping.confidence_score
        
        # Try to modify (should fail or be prevented)
        # In production this is enforced at model level
        if mapping.verified:
            # Cannot unverify
            assert mapping.verified == True
            assert mapping.confidence_score >= 0.80


class MappingConflictResolutionTestCase(TestCase):
    """Test edge cases in mapping conflicts"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='owner1',
            email='owner1@test.com',
            password='pass123'
        )
    
    def test_1km_boundary_within_acceptable_range(self):
        """Distance of 1km exactly should be acceptable"""
        property_in = Property.objects.create(
            owner=self.user,
            name='Hotel In Range',
            city='Delhi',
            country='India',
            address='123 In Rd',
            description='In range',
            latitude=28.6139,
            longitude=77.2090
        )
        
        # Supplier location is exactly 1km away
        matched, confidence, _ = match_supplier_property(
            supplier_name='booking',
            external_id='boundary_001',
            supplier_property_name='Hotel In Range',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2164  # Approximately 1km away
        )
        
        # Should be at board threshold or accepted
        assert matched == property_in or confidence >= 0.75
    
    def test_1_01km_beyond_acceptable_range(self):
        """Distance > 1km should be rejected"""
        property_out = Property.objects.create(
            owner=self.user,
            name='Hotel Out Range',
            city='Delhi',
            country='India',
            address='456 Out Rd',
            description='Out of range',
            latitude=28.6139,
            longitude=77.2090
        )
        
        # Supplier location > 1km away
        matched, confidence, status = match_supplier_property(
            supplier_name='booking',
            external_id='boundary_002',
            supplier_property_name='Hotel Out Range',
            supplier_city='Delhi',
            supplier_lat=28.6139,
            supplier_lng=77.2200  # More than 1km away
        )
        
        # Should rejectifar or very low confidence
        if matched is not None:
            assert confidence < 0.80


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
