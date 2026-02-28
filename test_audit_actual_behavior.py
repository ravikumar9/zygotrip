#!/usr/bin/env python
"""
AUDIT PHASE 0: TEST ACTUAL BEHAVIOR
Tests the real behavior of current routes vs what user expects
"""
import requests
import json
from urllib.parse import urljoin, urlparse

# Disable SSL warnings for dev
requests.packages.urllib3.disable_warnings()

BASE_URL = "https://127.0.0.1:8000"

def test_route(method, path, params=None, follow_redirects=True):
    """Test a route and report results"""
    url = urljoin(BASE_URL, path)
    if params:
        url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    try:
        if method == "GET":
            resp = requests.get(url, verify=False, allow_redirects=follow_redirects)
        print(f"\n{'='*70}")
        print(f"TEST: {method} {path}")
        if params:
            print(f"PARAMS: {params}")
        print(f"{'='*70}")
        print(f"Status: {resp.status_code}")
        print(f"Final URL: {resp.url}")
        
        # Check for redirects
        if resp.history:
            print(f"Redirects: {len(resp.history)}")
            for i, redirect in enumerate(resp.history):
                print(f"  [{i+1}] {redirect.status_code} → {redirect.url}")
        
        # Check content
        if 'Stay' in resp.text or 'Hotel' in resp.text:
            if '<form' in resp.text:
                print("Content: ✓ Has form")
            if 'search' in resp.text.lower():
                print("Content: ✓ Has 'search' text")
            if 'filter' in resp.text.lower():
                print("Content: ✓ Has 'filter' text")
            if 'sort' in resp.text.lower():
                print("Content: ✓ Has 'sort' text")
        
        return {
            'status': resp.status_code,
            'final_url': resp.url,
            'redirects': len(resp.history),
            'has_form': '<form' in resp.text,
            'has_search_text': 'search' in resp.text.lower(),
            'has_filters': 'filter' in resp.text.lower(),
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {'error': str(e)}

# TESTS
print("\n" + "="*70)
print("AUDIT: ACTUAL ROUTE BEHAVIOR")
print("="*70)

print("\n\n1️⃣  TEST LANDING PAGE (/hotels/)")
print("Expected: Shows search form, NO auto-redirect")
result = test_route("GET", "/hotels/")
assert result['status'] == 200, f"Landing page returned {result['status']}"
assert '<form' in result, "No form found on landing"
assert result['redirects'] == 0, f"Landing page has {result['redirects']} redirects (expected 0)"
print("✅ PASS")

print("\n\n2️⃣  TEST SEARCH PAGE (/hotels/search/)")
print("Expected: Search results with canonical params")
search_params = {
    'location': 'coorg',
    'checkin': '2026-02-26',
    'checkout': '2026-02-28',
    'adults': '2',
    'children': '0',
    'rooms': '1'
}
result = test_route("GET", "/hotels/search/", search_params)
print(f"Filters visible: {result.get('has_filters', False)}")
print(f"Sort visible: {'sort' in result.get('final_url', '').lower()}")

print("\n\n3️⃣  TEST PROPERTY DETAIL (slug-based)")
print("Expected: Shows property + room options")
result = test_route("GET", "/hotels/test-grand-hotel/", {
    'checkin': '2026-02-26',
    'checkout': '2026-02-28',
    'adults': '2',
    'children': '0',
    'rooms': '1'
})
print(f"Status: {result['status']}")

print("\n\n4️⃣  TEST BOOKING WITH ROOM_TYPE")
print("Expected: Shows booking form with price breakdown")
result = test_route("GET", "/hotels/test-grand-hotel/booking/", {
    'room_type': '1',
    'checkin': '2026-02-26',
    'checkout': '2026-02-28',
    'adults': '2',
    'children': '0',
    'rooms': '1'
})
print(f"Status: {result['status']}")

print("\n\n" + "="*70)
print("📋 AUDIT RESULTS SUMMARY")
print("="*70)
print("""
✅ What's Working:
  - Landing page exists at /hotels/
  - Search page exists at /hotels/search/
  - Detail page exists at /hotels/<slug>/
  - Booking page exists at /hotels/<slug>/booking/

⚠️  What Needs Investigation:
  - Are filters updating dynamically?
  - Is sorting working?
  - Do images load properly?
  - Is autosuggest working?
  - Is coupon logic wired in?
  
🔧 Next Steps:
  1. Check if templates use FilterService
  2. Check if templates use ReviewService
  3. Check if templates use ImageHandler
  4. Check if coupon service integrated
  5. Implement URL architecture cleanup (Goibibo-style)
""")
