"""
OTA BACKEND VALIDATION - STRICT 8 RULES TEST SUITE

Tests that the hotel listing backend ENFORCES all 8 rules:
1. ZERO hardcoded counts - all from database
2. URL-stateful search with request.GET binding
3. Sort pills modify queryset with order_by()
4. Hotel card data from database, no placeholders
5. Filter counts dynamic from filtered queryset
6. Empty state checked against actual result count
7. All GET parameters persisted for stateful URLs
8. Real data ONLY - no seeding fake values

NO PASSING TESTS IF ANY RULE IS VIOLATED.
"""
import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.hotels.models import Property, PropertyAmenity
from apps.core.models import City
from apps.hotels.ota_selectors import (
    ota_visible_properties,
    get_filter_counts,
    apply_search_filters,
    apply_sorting,
    serialize_hotel_card,
    get_ota_context
)

User = get_user_model()


class OTABackendRulesTest(TestCase):
    """Enforces all 8 OTA backend rules"""
    
    @classmethod
    def setUpTestData(cls):
        """Create real test data - NO FAKES"""
        from apps.core.models import LocationSearchIndex
        
        # Create state first
        from apps.core.location_models import State, Country
        
        cls.country = Country.objects.create(name='India', code='IN')
        cls.state = State.objects.create(
            country=cls.country,
            code='MH',
            name='Maharashtra'
        )
        
        # Create cities with required fields
        cls.city_mumbai = City.objects.create(
            state=cls.state,
            code='MUM',
            name='Mumbai',
            display_name='Mumbai, Maharashtra',
            latitude=Decimal('19.0761'),
            longitude=Decimal('72.8724')
        )
        cls.city_delhi = City.objects.create(
            state=cls.state,
            code='DEL',
            name='Delhi',
            display_name='Delhi, India',
            latitude=Decimal('28.7041'),
            longitude=Decimal('77.1025')
        )
        
        # Create property owner
        cls.owner = User.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            role='property_owner'
        )
        
        # Create APPROVED property with agreement signed
        cls.property1 = Property.objects.create(
            owner=cls.owner,
            name='Luxury Hotel Mumbai',
            property_type='Hotel',
            city=cls.city_mumbai,
            address='123 Main St',
            description='5-star luxury hotel',
            
            # CRITICAL: Must be approved AND agreement_signed (Rule 8: real data)
            status='approved',
            agreement_signed=True,
            
            # Pricing
            rating=Decimal('4.5'),
            review_count=25,
            
            # Signals
            has_free_cancellation=True,
            is_trending=False,
            bookings_today=5,
            bookings_this_week=12,
            
            latitude=Decimal('19.0761'),
            longitude=Decimal('72.8724'),
        )
        
        # Create another approved property
        cls.property2 = Property.objects.create(
            owner=cls.owner,
            name='Budget Hotel Delhi',
            property_type='Hotel',
            city=cls.city_delhi,
            address='456 Second Ave',
            description='Budget-friendly hotel',
            
            status='approved',
            agreement_signed=True,
            
            rating=Decimal('3.8'),
            review_count=12,
            
            has_free_cancellation=False,
            is_trending=True,
            bookings_today=3,
            bookings_this_week=8,
            
            latitude=Decimal('28.7041'),
            longitude=Decimal('77.1025'),
        )
        
        # Create UNAPPROVED property (should NOT appear)
        cls.property_unapproved = Property.objects.create(
            owner=cls.owner,
            name='Secret Hotel',
            property_type='Resort',
            city=cls.city_mumbai,
            address='Hidden location',
            description='Not yet approved',
            
            status='pending',  # NOT approved
            agreement_signed=False,  # NOT signed
            
            rating=Decimal('5.0'),
            review_count=100,
            latitude=Decimal('19.0761'),
            longitude=Decimal('72.8724'),
        )
        
        # Add amenities to property1
        PropertyAmenity.objects.create(property=cls.property1, name='WiFi', icon='wifi')
        PropertyAmenity.objects.create(property=cls.property1, name='AC', icon='ac')
        PropertyAmenity.objects.create(property=cls.property2, name='WiFi', icon='wifi')
    
    
    # ===== RULE 1: ZERO HARDCODED COUNTS =====
    def test_rule_1_filter_counts_from_database(self):
        """RULE 1: All filter counts come from database, not hardcoded"""
        qs = ota_visible_properties()
        counts = get_filter_counts(qs)
        
        # Property Type counts MUST match queryset
        self.assertIn('property_types', counts)
        property_types = counts['property_types']
        self.assertEqual(property_types.get('Hotel'), 2)
        self.assertNotIn('Resort', property_types)  # Unapproved resort excluded
        
        # Amenity counts MUST match database
        self.assertIn('amenities', counts)
        amenities = counts['amenities']
        self.assertEqual(amenities.get('WiFi'), 2)
        self.assertEqual(amenities.get('AC'), 1)
        
        # City counts MUST match database
        self.assertIn('cities', counts)
        cities = counts['cities']
        self.assertEqual(cities.get('Mumbai'), 1)
        self.assertEqual(cities.get('Delhi'), 1)
    
    def test_rule_1_counts_exclude_unapproved(self):
        """RULE 1: Unapproved properties excluded from all counts"""
        qs = ota_visible_properties()
        counts = get_filter_counts(qs)
        
        # Resort count should be 0 (only unapproved resort exists)
        property_types = counts['property_types']
        self.assertEqual(property_types.get('Resort', 0), 0)
    
    
    # ===== RULE 2: URL-STATEFUL SEARCH =====
    def test_rule_2_location_filter_binds_to_request_get(self):
        """RULE 2: Location filter binds to request GET param"""
        factory = RequestFactory()
        
        # Search for Mumbai
        request = factory.get('/', {'location': 'Mumbai'})
        context = get_ota_context(request)
        
        self.assertEqual(len(context['hotels']), 1)
        self.assertEqual(context['hotels'][0]['name'], 'Luxury Hotel Mumbai')
    
    def test_rule_2_price_filter_binds_to_request_get(self):
        """RULE 2: Price range filters bind to request GET"""
        factory = RequestFactory()
        
        # Min price filter should exclude cheaper hotels
        request = factory.get('/', {'min_price': '5000'})
        context = get_ota_context(request)
        
        # Both properties should be included (no room prices set yet)
        # But test parameter binding works
        self.assertEqual(context['selected_filters']['min_price'], '5000')
    
    def test_rule_2_free_cancellation_filter_binds(self):
        """RULE 2: Free cancellation checkbox binds to request"""
        factory = RequestFactory()
        
        request = factory.get('/', {'free_cancellation': 'on'})
        context = get_ota_context(request)
        
        # Only property1 has free cancellation
        self.assertEqual(len(context['hotels']), 1)
        self.assertEqual(context['hotels'][0]['name'], 'Luxury Hotel Mumbai')
        self.assertTrue(context['selected_filters']['free_cancellation'])
    
    def test_rule_2_parameter_persistence(self):
        """RULE 2: All GET params persist in context"""
        factory = RequestFactory()
        
        request = factory.get('/', {
            'location': 'Mumbai',
            'min_price': '1000',
            'free_cancellation': 'on',
            'sort': 'rating'
        })
        context = get_ota_context(request)
        
        # All params must be in current_query
        current_query = context['current_query']
        self.assertIn('location', current_query)
        self.assertIn('min_price', current_query)
        self.assertIn('free_cancellation', current_query)
        self.assertIn('sort', current_query)
    
    
    # ===== RULE 3: SORT PILLS MODIFY QUERYSET =====
    def test_rule_3_sort_by_rating_modifies_order(self):
        """RULE 3: Sort 'rating' orders by avg_rating DESC"""
        factory = RequestFactory()
        
        request = factory.get('/', {'sort': 'rating'})
        context = get_ota_context(request)
        
        # Property1 has 4.5 rating, property2 has 3.8
        # Should be ordered 4.5 first
        hotels = context['hotels']
        self.assertEqual(hotels[0]['rating'], 4.5)
        self.assertEqual(hotels[1]['rating'], 3.8)
    
    def test_rule_3_sort_by_price_asc(self):
        """RULE 3: Sort 'price_asc' orders min_room_price ASC"""
        # Create properties with RoomType pricing
        from apps.rooms.models import RoomType
        
        RoomType.objects.create(
            property=self.property1,
            name='Standard',
            base_price=Decimal('5000')
        )
        RoomType.objects.create(
            property=self.property2,
            name='Economy',
            base_price=Decimal('2000')
        )
        
        factory = RequestFactory()
        request = factory.get('/', {'sort': 'price_asc'})
        context = get_ota_context(request)
        
        hotels = context['hotels']
        # Property2 (₹2000) should come before Property1 (₹5000)
        self.assertEqual(hotels[0]['min_price'], 2000)
        self.assertEqual(hotels[1]['min_price'], 5000)
    
    def test_rule_3_sort_by_price_desc(self):
        """RULE 3: Sort 'price_desc' orders min_room_price DESC"""
        from apps.rooms.models import RoomType
        
        RoomType.objects.all().delete()
        
        RoomType.objects.create(
            property=self.property1,
            name='Standard',
            base_price=Decimal('5000')
        )
        RoomType.objects.create(
            property=self.property2,
            name='Economy',
            base_price=Decimal('2000')
        )
        
        factory = RequestFactory()
        request = factory.get('/', {'sort': 'price_desc'})
        context = get_ota_context(request)
        
        hotels = context['hotels']
        # Property1 (₹5000) should come before Property2 (₹2000)
        self.assertEqual(hotels[0]['min_price'], 5000)
        self.assertEqual(hotels[1]['min_price'], 2000)
    
    def test_rule_3_default_sort_is_popular(self):
        """RULE 3: Default sort is 'popular' when not specified"""
        factory = RequestFactory()
        
        request = factory.get('/')
        context = get_ota_context(request)
        
        self.assertEqual(context['current_sort'], 'popular')
    
    
    # ===== RULE 4: CARD DATA FROM DATABASE =====
    def test_rule_4_card_has_db_fields(self):
        """RULE 4: Hotel card contains only database-sourced fields"""
        card = serialize_hotel_card(self.property1)
        
        # All these must come from Property model, not hardcoded
        self.assertEqual(card['name'], self.property1.name)
        self.assertEqual(card['property_type'], self.property1.property_type)
        self.assertEqual(card['city'], self.property1.city.name)
        self.assertEqual(card['rating'], float(self.property1.rating))
        self.assertEqual(card['review_count'], self.property1.review_count)
        self.assertEqual(card['has_free_cancellation'], self.property1.has_free_cancellation)
        self.assertEqual(card['is_trending'], self.property1.is_trending)
    
    def test_rule_4_no_placeholder_pricing(self):
        """RULE 4: Card pricing comes from database, no defaults like '999'"""
        from apps.rooms.models import RoomType
        
        RoomType.objects.create(
            property=self.property1,
            name='Standard',
            base_price=Decimal('3500')
        )
        
        card = serialize_hotel_card(self.property1)
        
        # Pricing must be from RoomType, not '999'
        self.assertEqual(card['min_price'], 3500)
        self.assertNotEqual(card['min_price'], 999)
    
    def test_rule_4_amenities_from_m2m(self):
        """RULE 4: Amenities list comes from PropertyAmenity objects"""
        card = serialize_hotel_card(self.property1)
        
        amenities = card['amenities']
        self.assertIn('WiFi', amenities)
        self.assertIn('AC', amenities)
        self.assertEqual(len(amenities), 2)
    
    
    # ===== RULE 5: FILTER COUNTS DYNAMIC =====
    def test_rule_5_counts_change_with_filters(self):
        """RULE 5: Filter counts update when filters applied"""
        factory = RequestFactory()
        
        # Initial counts: 2 properties
        qs_all = ota_visible_properties()
        counts_all = get_filter_counts(qs_all)
        total_initial = counts_all['property_types'].get('Hotel', 0)
        self.assertEqual(total_initial, 2)
        
        # After filtering by city=Mumbai: 1 property
        qs_filtered = apply_search_filters(qs_all, {'location': 'Mumbai'})
        counts_filtered = get_filter_counts(qs_filtered)
        total_filtered = counts_filtered['property_types'].get('Hotel', 0)
        self.assertEqual(total_filtered, 1)
    
    def test_rule_5_amenity_counts_recalculate(self):
        """RULE 5: Amenity counts recalculate for filtered results"""
        qs_all = ota_visible_properties()
        counts_all = get_filter_counts(qs_all)
        wifi_all = counts_all['amenities'].get('WiFi', 0)
        self.assertEqual(wifi_all, 2)  # Both props have WiFi
        
        # Filter to Delhi only (property2)
        qs_delhi = apply_search_filters(qs_all, {'location': 'Delhi'})
        counts_delhi = get_filter_counts(qs_delhi)
        wifi_delhi = counts_delhi['amenities'].get('WiFi', 0)
        self.assertEqual(wifi_delhi, 1)  # Only property2 in Delhi
    
    
    # ===== RULE 6: EMPTY STATE VALIDITY =====
    def test_rule_6_empty_state_when_no_results(self):
        """RULE 6: Empty state flag set when queryset count is 0"""
        factory = RequestFactory()
        
        # Filter for impossible criteria
        request = factory.get('/', {'location': 'Atlantis'})
        context = get_ota_context(request)
        
        self.assertTrue(context['empty_state'])
        self.assertEqual(context['total_count'], 0)
        self.assertEqual(len(context['hotels']), 0)
    
    def test_rule_6_empty_state_false_with_results(self):
        """RULE 6: Empty state flag false when results exist"""
        factory = RequestFactory()
        
        request = factory.get('/')
        context = get_ota_context(request)
        
        self.assertFalse(context['empty_state'])
        self.assertEqual(context['total_count'], 2)
        self.assertEqual(len(context['hotels']), 2)
    
    
    # ===== RULE 7: PARAMETER PERSISTENCE =====
    def test_rule_7_all_get_params_tracked(self):
        """RULE 7: All GET parameters preserved in current_query"""
        factory = RequestFactory()
        
        request = factory.get('/', {
            'location': 'Mumbai',
            'min_price': '2000',
            'max_price': '10000',
            'free_cancellation': 'on',
            'sort': 'rating'
        })
        context = get_ota_context(request)
        
        current_query = context['current_query']
        self.assertEqual(current_query.get('location'), 'Mumbai')
        self.assertEqual(current_query.get('min_price'), '2000')
        self.assertEqual(current_query.get('max_price'), '10000')
        self.assertEqual(current_query.get('free_cancellation'), 'on')
        self.assertEqual(current_query.get('sort'), 'rating')
    
    
    # ===== RULE 8: REAL DATA ONLY =====
    def test_rule_8_unapproved_excluded(self):
        """RULE 8: Unapproved properties never appear"""
        qs = ota_visible_properties()
        
        # Should only have 2 approved properties
        self.assertEqual(qs.count(), 2)
        
        # Unapproved property must not appear
        self.assertNotIn(self.property_unapproved, qs)
    
    def test_rule_8_unsigned_agreement_excluded(self):
        """RULE 8: Unsigned agreement properties excluded"""
        # Create property with approved but unsigned agreement
        property_unsigned = Property.objects.create(
            owner=self.owner,
            name='Unsigned Agreement Hotel',
            property_type='Hotel',
            city=self.city_mumbai,
            address='789 Third St',
            description='Not signed',
            
            status='approved',
            agreement_signed=False,  # NOT signed
            
            rating=Decimal('4.0'),
            latitude=Decimal('19.0761'),
            longitude=Decimal('72.8724'),
        )
        
        qs = ota_visible_properties()
        
        # Still only 2 (the signed ones)
        self.assertEqual(qs.count(), 2)
        self.assertNotIn(property_unsigned, qs)
    
    def test_rule_8_context_contains_real_data_only(self):
        """RULE 8: get_ota_context returns only approved+signed properties"""
        factory = RequestFactory()
        
        request = factory.get('/')
        context = get_ota_context(request)
        
        hotels = context['hotels']
        
        # Both visible properties
        self.assertEqual(len(hotels), 2)
        
        # Names must match real properties
        names = [h['name'] for h in hotels]
        self.assertIn('Luxury Hotel Mumbai', names)
        self.assertIn('Budget Hotel Delhi', names)
        
        # Secret Hotel (unapproved) must NOT appear
        self.assertNotIn('Secret Hotel', names)


class IntegrationTest(TestCase):
    """Integration tests for full request/response cycle"""
    
    def setUp(self):
        """Set up test data"""
        from apps.core.location_models import Country, State
        
        self.factory = RequestFactory()
        
        country = Country.objects.create(name='India', code='IN')
        state = State.objects.create(country=country, code='KA', name='Karnataka')
        
        self.city = City.objects.create(
            state=state,
            code='BEN',
            name='Bangalore',
            display_name='Bangalore, Karnataka',
            latitude=Decimal('12.9716'),
            longitude=Decimal('77.5946')
        )
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='pass',
            role='property_owner'
        )
        
        self.property = Property.objects.create(
            owner=self.owner,
            name='Test Hotel',
            city=self.city,
            address='123 Test St',
            description='Test',
            status='approved',
            agreement_signed=True,
            rating=Decimal('4.0'),
            has_free_cancellation=True,
            latitude=Decimal('12.9716'),
            longitude=Decimal('77.5946'),
        )
    
    def test_full_request_cycle_no_hardcoded_strings(self):
        """Integration: Full request cycle returns no hardcoded values"""
        request = self.factory.get('/')
        context = get_ota_context(request)
        
        # Counts must not be hardcoded strings
        filter_options = context['filter_options']
        
        # No filter count should be the exact strings like "(24)", "(8)", "(5)"
        for section, items in filter_options.items():
            if isinstance(items, dict):
                for value in items.values():
                    # Value should be int from database, not string
                    self.assertIsInstance(value, int)
    
    def test_view_response_status_200(self):
        """Integration: View returns 200 for valid request"""
        from apps.hotels.views import hotel_list
        
        request = self.factory.get('/')
        response = hotel_list(request)
        
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    import unittest
    unittest.main()
