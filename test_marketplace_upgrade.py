"""
Test script to verify marketplace upgrade success conditions.
Run this after starting the server to validate implementation.
"""
import requests
import time
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoints():
    """Test that all API endpoints are accessible and return data."""
    print("\n🔍 Testing API Endpoints...")
    
    endpoints = {
        '/api/search-autocomplete?q=mumbai': 'Search Autocomplete',
        '/api/trending-destinations': 'Trending Destinations',
        '/api/categories': 'Categories',
        '/api/offers': 'Offers'
    }
    
    results = {}
    for path, name in endpoints.items():
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                results[name] = {
                    'status': 'PASS',
                    'data_size': len(str(data))
                }
                print(f"  ✓ {name}: PASS ({len(str(data))} bytes)")
            else:
                results[name] = {'status': 'FAIL', 'error': f'Status {response.status_code}'}
                print(f"  ✗ {name}: FAIL (Status {response.status_code})")
        except Exception as e:
            results[name] = {'status': 'ERROR', 'error': str(e)}
            print(f"  ✗ {name}: ERROR ({str(e)})")
    
    return results

def test_homepage_components():
    """Test that homepage contains all required sections."""
    print("\n🏠 Testing Homepage Components...")
    
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code != 200:
            print(f"  ✗ Homepage not accessible (Status {response.status_code})")
            return False
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for required components
        checks = {
            'search_bar': 'enhanced_search_bar' in html or 'location-autocomplete' in html,
            'category_tabs': 'category-tabs-section' in html or 'categories-container' in html,
            'destination_cards': 'destinations-section' in html or 'destinations-container' in html,
            'offers_slider': 'offers-section' in html or 'offers-carousel' in html,
        }
        
        all_passed = True
        for component, present in checks.items():
            status = "✓ PASS" if present else "✗ FAIL"
            print(f"  {status} {component.replace('_', ' ').title()}")
            if not present:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ✗ Error testing homepage: {str(e)}")
        return False

def test_hotel_list_page():
    """Test that hotel list page uses enhanced components."""
    print("\n🏨 Testing Hotel List Page...")
    
    try:
        response = requests.get(f"{BASE_URL}/hotels/", timeout=10)
        if response.status_code != 200:
            print(f"  ✗ Hotels page not accessible (Status {response.status_code})")
            return False
        
        html = response.text
        
        checks = {
            'enhanced_search_bar': 'enhanced_search_bar' in html or 'location-autocomplete' in html,
            'sidebar_filters': 'sidebar_filters' in html or 'sidebar-filters' in html,
            'hotel_card': 'hotel-card' in html or 'enhanced_hotel_card' in html,
        }
        
        all_passed = True
        for component, present in checks.items():
            status = "✓ PASS" if present else "✗ FAIL"
            print(f"  {status} {component.replace('_', ' ').title()}")
            if not present:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ✗ Error testing hotel page: {str(e)}")
        return False

def test_css_loaded():
    """Test that marketplace.css is loaded."""
    print("\n🎨 Testing CSS Files...")
    
    try:
        response = requests.get(f"{BASE_URL}/static/css/marketplace.css", timeout=5)
        if response.status_code == 200:
            css = response.text
            # Check for key color variables
            has_primary = '--color-primary' in css or '.primary-btn' in css
            has_accent = '--color-accent' in css
            size = len(css)
            
            if has_primary:
                print(f"  ✓ PASS marketplace.css loaded ({size} bytes)")
                return True
            else:
                print(f"  ✗ FAIL marketplace.css missing color system")
                return False
        else:
            print(f"  ✗ FAIL marketplace.css not found (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"  ✗ ERROR loading CSS: {str(e)}")
        return False

def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("MARKETPLACE UPGRADE VALIDATION TEST")
    print("=" * 60)
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server to start...")
    for i in range(10):
        try:
            requests.get(BASE_URL, timeout=2)
            print("✓ Server is ready")
            break
        except:
            time.sleep(1)
    else:
        print("✗ Server did not start in time")
        return
    
    # Run tests
    api_results = test_api_endpoints()
    homepage_ok = test_homepage_components()
    hotels_ok = test_hotel_list_page()
    css_ok = test_css_loaded()
    
    # Final report
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    api_pass = all(r['status'] == 'PASS' for r in api_results.values())
    
    overall_status = all([api_pass, homepage_ok, hotels_ok, css_ok])
    
    print(f"\nAPI Endpoints: {'✓ PASS' if api_pass else '✗ FAIL'}")
    print(f"Homepage Components: {'✓ PASS' if homepage_ok else '✗ FAIL'}")
    print(f"Hotel List Page: {'✓ PASS' if hotels_ok else '✗ FAIL'}")
    print(f"CSS Loading: {'✓ PASS' if css_ok else '✗ FAIL'}")
    
    print("\n" + "=" * 60)
    if overall_status:
        print("✓ SUCCESS - All conditions met!")
        print("Marketplace upgrade is fully operational.")
    else:
        print("✗ PARTIAL - Some components need attention")
        print("Review failed checks above.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")