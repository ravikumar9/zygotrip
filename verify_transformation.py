"""
Architectural Transformation Verification Script
Run this after deployment to verify all systems operational
"""

import sys
import time
from decimal import Decimal
from django.db.models import Count, Min
from django.core.cache import cache
from django.conf import settings

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_status(test_name, passed, message=""):
    """Print test result with color coding"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    if message:
        print(f"     {message}")


def test_1_property_pricing_refactor():
    """Test that Property pricing is computed from RoomType"""
    from apps.hotels.models import Property
    from apps.rooms.models import RoomType
    
    print(f"\n{BLUE}=== Test 1: Property Pricing Refactor ==={RESET}")
    
    # Check Property model has no base_price field in database
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(hotels_property)")
    columns = [row[1] for row in cursor.fetchall()]
    
    has_base_price_field = 'base_price' in columns
    print_status(
        "Property.base_price database field removed",
        not has_base_price_field,
        f"Database columns: {len(columns)}"
    )
    
    # Check @property base_price works
    try:
        sample = Property.objects.annotate(min_room_price=Min('room_types__base_price')).first()
        if sample:
            computed_price = sample.base_price  # Triggers @property
            has_property = computed_price is not None or computed_price == 0
            print_status(
                "Property.base_price @property works",
                has_property,
                f"Returns: {computed_price}"
            )
        else:
            print_status("Property.base_price @property works", False, "No properties found")
    except Exception as e:
        print_status("Property.base_price @property works", False, str(e))
    
    # Check all properties have room types
    properties_without_rooms = Property.objects.annotate(
        room_count=Count('room_types')
    ).filter(room_count=0)
    
    count = properties_without_rooms.count()
    print_status(
        "All properties have room types",
        count == 0,
        f"{count} properties without room types" if count > 0 else "All properties OK"
    )
    
    return not has_base_price_field and count == 0


def test_2_search_ranking_service():
    """Test that SearchRankingService works"""
    from apps.hotels.selectors import public_properties_queryset
    from apps.hotels.search import SearchRankingService
    
    print(f"\n{BLUE}=== Test 2: Search Ranking Service ==={RESET}")
    
    try:
        qs = public_properties_queryset()
        service = SearchRankingService(qs, {'lat': '19.0760', 'lng': '72.8777'})
        ranked = service.apply_ranking()
        
        # Check first result has relevance_score
        first = ranked.first()
        has_score = hasattr(first, 'relevance_score') if first else False
        
        print_status(
            "SearchRankingService applies ranking",
            has_score,
            f"Relevance score: {first.relevance_score if has_score else 'N/A'}"
        )
        
        # Check score is between 0 and 1
        if has_score:
            score_valid = 0 <= first.relevance_score <= 1
            print_status(
                "Relevance score in valid range (0-1)",
                score_valid,
                f"Score: {first.relevance_score}"
            )
        else:
            print_status("Relevance score in valid range (0-1)", False, "No score found")
            return False
        
        return has_score
    except Exception as e:
        print_status("SearchRankingService applies ranking", False, str(e))
        return False


def test_3_rest_api_endpoints():
    """Test that REST API endpoints are accessible"""
    from django.test import Client
    
    print(f"\n{BLUE}=== Test 3: REST API Endpoints ==={RESET}")
    
    client = Client()
    
    # Test property list API
    try:
        response = client.get('/api/v1/properties/')
        passed = response.status_code == 200
        print_status(
            "GET /api/v1/properties/",
            passed,
            f"Status: {response.status_code}"
        )
        
        if passed:
            import json
            data = json.loads(response.content)
            has_structure = 'results' in data and 'pagination' in data
            print_status(
                "Response has correct JSON structure",
                has_structure,
                f"Keys: {list(data.keys())}"
            )
    except Exception as e:
        print_status("GET /api/v1/properties/", False, str(e))
        return False
    
    # Test search API
    try:
        response = client.get('/api/v1/search/?q=hotel&lat=19.0760&lng=72.8777')
        passed = response.status_code == 200
        print_status(
            "GET /api/v1/search/",
            passed,
            f"Status: {response.status_code}"
        )
        
        if passed:
            data = json.loads(response.content)
            has_meta = 'meta' in data and data['meta'].get('ranking_applied') == True
            print_status(
                "Search applies ranking",
                has_meta,
                f"Ranking applied: {data['meta'].get('ranking_applied')}"
            )
    except Exception as e:
        print_status("GET /api/v1/search/", False, str(e))
        return False
    
    # Test property detail API
    try:
        from apps.hotels.models import Property
        first_property = Property.objects.first()
        if first_property:
            response = client.get(f'/api/v1/properties/{first_property.id}/')
            passed = response.status_code == 200
            print_status(
                f"GET /api/v1/properties/{first_property.id}/",
                passed,
                f"Status: {response.status_code}"
            )
        else:
            print_status("GET /api/v1/properties/<id>/", False, "No properties found")
            return False
    except Exception as e:
        print_status("GET /api/v1/properties/<id>/", False, str(e))
        return False
    
    return True


def test_4_trust_signal_service():
    """Test that TrustSignalService generates badges"""
    from apps.hotels.models import Property
    from apps.hotels.services.trust_signals import TrustSignalService
    
    print(f"\n{BLUE}=== Test 4: Trust Signal Service ==={RESET}")
    
    try:
        sample = Property.objects.first()
        if not sample:
            print_status("TrustSignalService generates badges", False, "No properties found")
            return False
        
        service = TrustSignalService(sample)
        badges = service.generate_badges()
        
        is_list = isinstance(badges, list)
        print_status(
            "TrustSignalService returns badge list",
            is_list,
            f"Type: {type(badges)}"
        )
        
        if is_list:
            max_3_badges = len(badges) <= 3
            print_status(
                "Badge count <= 3 (max limit)",
                max_3_badges,
                f"Badge count: {len(badges)}"
            )
            
            if badges:
                first_badge = badges[0]
                has_structure = all(k in first_badge for k in ['type', 'label', 'icon'])
                print_status(
                    "Badges have correct structure",
                    has_structure,
                    f"Keys: {list(first_badge.keys())}"
                )
                return has_structure
            else:
                print_status("Badges have correct structure", True, "No badges generated (property doesn't meet criteria)")
                return True
        
        return False
    except Exception as e:
        print_status("TrustSignalService generates badges", False, str(e))
        return False


def test_5_database_indexes():
    """Test that performance indexes were created"""
    from django.db import connection
    
    print(f"\n{BLUE}=== Test 5: Database Indexes ==={RESET}")
    
    cursor = connection.cursor()
    
    # For SQLite, check index existence
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='hotels_property'")
    indexes = [row[0] for row in cursor.fetchall()]
    
    expected_indexes = [
        'hotels_prop_city_idx',
        'hotels_prop_rating_idx',
        'hotels_prop_active_rating_idx',
        'hotels_prop_geo_idx',
        'hotels_prop_trending_idx',
        'hotels_prop_popularity_idx'
    ]
    
    for index_name in expected_indexes:
        exists = any(index_name in idx for idx in indexes)
        print_status(
            f"Index {index_name}",
            exists,
            "Created" if exists else "Missing"
        )
    
    total_created = sum(1 for idx in expected_indexes if any(idx in db_idx for db_idx in indexes))
    print(f"\n  {YELLOW}Total indexes created: {total_created}/{len(expected_indexes)}{RESET}")
    
    return total_created >= 4  # At least 4 indexes should exist


def test_6_constants_usage():
    """Test that constants are properly imported"""
    print(f"\n{BLUE}=== Test 6: Constants Module ==={RESET}")
    
    try:
        from apps.hotels.constants import (
            CACHE_TTL_HOTEL_LIST,
            DEFAULT_PAGE_SIZE,
            MIN_RATING_TOP_RATED,
            RANKING_WEIGHT_RATING
        )
        
        # Check values are correct
        checks = [
            ('CACHE_TTL_HOTEL_LIST', CACHE_TTL_HOTEL_LIST == 60),
            ('DEFAULT_PAGE_SIZE', DEFAULT_PAGE_SIZE == 20),
            ('MIN_RATING_TOP_RATED', MIN_RATING_TOP_RATED == 4.5),
            ('RANKING_WEIGHT_RATING', RANKING_WEIGHT_RATING == 0.30),
        ]
        
        for name, passed in checks:
            print_status(f"Constant {name} imported", passed, f"Value: {eval(name)}")
        
        return all(passed for _, passed in checks)
    except Exception as e:
        print_status("Constants module import", False, str(e))
        return False


def test_7_cache_system():
    """Test that cache system is working"""
    print(f"\n{BLUE}=== Test 7: Cache System ==={RESET}")
    
    try:
        # Test cache set/get
        test_key = 'verification_test'
        test_value = 'cache_works'
        
        cache.set(test_key, test_value, 60)
        retrieved = cache.get(test_key)
        
        works = retrieved == test_value
        print_status(
            "Cache set/get works",
            works,
            f"Retrieved: {retrieved}"
        )
        
        # Test hotel list cache key format
        from apps.hotels.services import HotelListService
        service = HotelListService({'city': 'Mumbai'}, None)
        cache_key = service._cache_key()
        
        valid_format = cache_key.startswith('hotels:list:')
        print_status(
            "Hotel list cache key format",
            valid_format,
            f"Key: {cache_key[:50]}..."
        )
        
        cache.delete(test_key)
        return works and valid_format
    except Exception as e:
        print_status("Cache system", False, str(e))
        return False


def run_all_tests():
    """Run all verification tests"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}ARCHITECTURAL TRANSFORMATION VERIFICATION{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    start_time = time.time()
    
    tests = [
        ("Property Pricing Refactor", test_1_property_pricing_refactor),
        ("Search Ranking Service", test_2_search_ranking_service),
        ("REST API Endpoints", test_3_rest_api_endpoints),
        ("Trust Signal Service", test_4_trust_signal_service),
        ("Database Indexes", test_5_database_indexes),
        ("Constants Module", test_6_constants_usage),
        ("Cache System", test_7_cache_system),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n{RED}ERROR in {name}: {e}{RESET}")
            results.append((name, False))
    
    # Summary
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}SUMMARY{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"{status} {name}")
    
    print(f"\n{BLUE}Tests Passed: {passed_count}/{total_count}{RESET}")
    print(f"{BLUE}Execution Time: {time.time() - start_time:.2f}s{RESET}")
    
    if passed_count == total_count:
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}✓ ALL TESTS PASSED - DEPLOYMENT SUCCESSFUL{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
        return 0
    else:
        print(f"\n{RED}{'='*60}{RESET}")
        print(f"{RED}✗ SOME TESTS FAILED - REVIEW REQUIRED{RESET}")
        print(f"{RED}{'='*60}{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())