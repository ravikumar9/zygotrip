"""
Production OTA Architecture Fix - Verification Script
Tests all upgraded features
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.search.engine import UnifiedSearchEngine

def test_autocomplete_with_counts():
    """Test autocomplete returns property_count"""
    engine = UnifiedSearchEngine()
    results = engine.autocomplete("del")
    
    print("=== AUTOCOMPLETE WITH PROPERTY COUNTS ===")
    print(f"Query: 'del'")
    print(f"Results count: {len(results['results'])}")
    
    for item in results['results'][:5]:
        print(f"\n  Type: {item['type']}")
        print(f"  Label: {item['label']}")
        print(f"  Property Count: {item.get('property_count', 'N/A')}")
        print(f"  ID: {item.get('id', 'N/A')}")
        print(f"  URL: {item.get('url', 'N/A')}")
    
    # Verify all results have property_count
    has_counts = all('property_count' in item for item in results['results'])
    print(f"\n✓ All results have property_count: {has_counts}")
    
    return has_counts

def verify_components():
    """Verify components exist"""
    print("\n=== COMPONENT VERIFICATION ===")
    
    files = {
        "Enhanced Hotel Card": "templates/components/enhanced_hotel_card.html",
        "Search Bar": "templates/components/searchbar.html",
        "Base Layout": "templates/base.html",
        "UI CSS": "static/css/ui.css",
        "Placeholder Image": "static/img/placeholder-hotel.jpg",
    }
    
    for name, path in files.items():
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {path}")
    
    return all(os.path.exists(path) for path in files.values())

def check_css_utilities():
    """Verify CSS depth utilities exist"""
    print("\n=== CSS UTILITIES VERIFICATION ===")
    
    with open("static/css/ui.css", "r") as f:
        css_content = f.read()
    
    utilities = [
        ".surface",
        ".card-hover",
        ".shadow-xl",
        ".depth-1",
        "#location-suggestions",
        ".hotel-card:hover",
    ]
    
    for utility in utilities:
        exists = utility in css_content
        status = "✓" if exists else "✗"
        print(f"{status} {utility}")
    
    return all(utility in css_content for utility in utilities)

def main():
    print("PRODUCTION OTA ARCHITECTURE FIX - VERIFICATION\n")
    print("=" * 60)
    
    # Test 1: Autocomplete with property counts
    test1 = test_autocomplete_with_counts()
    
    # Test 2: Components exist
    test2 = verify_components()
    
    # Test 3: CSS utilities present
    test3 = check_css_utilities()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"✓ Autocomplete with counts: {test1}")
    print(f"✓ All components present: {test2}")
    print(f"✓ CSS utilities added: {test3}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED - PRODUCTION READY")
    else:
        print("\n⚠️  SOME TESTS FAILED - REVIEW REQUIRED")

if __name__ == "__main__":
    main()


