#!/usr/bin/env python
"""
AUDIT PHASE 0: TEST ACTUAL BEHAVIOR
Tests the real behavior of current routes
"""
import requests
import json
from urllib.parse import urljoin, urlparse

# Disable SSL warnings for dev
requests.packages.urllib3.disable_warnings()

BASE_URL = "https://127.0.0.1:8000"

def test_route(method, path, params=None):
    """Test a route and report results"""
    url = urljoin(BASE_URL, path)
    if params:
        url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    try:
        resp = requests.get(url, verify=False, allow_redirects=True)
        print(f"\nTEST: {method} {path}")
        if params:
            print(f"PARAMS: {params}")
        print(f"Status: {resp.status_code}, Final URL: {resp.url}")
        
        # Check for redirects
        if resp.history:
            print(f"Redirects: {len(resp.history)}")
        
        return {
            'status': resp.status_code,
            'final_url': resp.url,
            'redirects': len(resp.history),
            'has_form': '<form' in resp.text,
            'html_length': len(resp.text),
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {'error': str(e)}

# TESTS
print("\n" + "="*70)
print("AUDIT: TESTING ACTUAL ROUTE BEHAVIOR")
print("="*70)

print("\n\nTEST 1: LANDING PAGE (/hotels/)")
result = test_route("GET", "/hotels/")
print(f"Result: {result}")

print("\n\nTEST 2: SEARCH PAGE (/hotels/search/)")
search_params = {
    'location': 'coorg',
    'checkin': '2026-02-26',
    'checkout': '2026-02-28',
    'adults': '2',
    'children': '0',
    'rooms': '1'
}
result = test_route("GET", "/hotels/search/", search_params)
print(f"Result: {result}")

print("\n\nTEST 3: PROPERTY DETAIL")
result = test_route("GET", "/hotels/test-grand-hotel/", {
    'checkin': '2026-02-26',
    'checkout': '2026-02-28',
    'adults': '2',
    'children': '0',
    'rooms': '1'
})
print(f"Result: {result}")

print("\n\nTEST 4: BOOKING PAGE")
result = test_route("GET", "/hotels/test-grand-hotel/booking/", {
    'room_type': '1',
    'checkin': '2026-02-26',
    'checkout': '2026-02-28',
    'adults': '2',
    'children': '0',
    'rooms': '1'
})
print(f"Result: {result}")

print("\n" + "="*70)
print("AUDIT COMPLETE")
print("="*70)
