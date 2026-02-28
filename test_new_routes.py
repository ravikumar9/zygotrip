#!/usr/bin/env python
"""Test new URL structure for hotels module"""
import requests
import time

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

BASE_URL = "https://localhost:8000"

tests = [
    {
        "name": "Landing Page",
        "url": f"{BASE_URL}/hotels/",
        "expected_content": ["Find Your Perfect Stay", "hotel-listing"],
        "expected_status": 200,
    },
    {
        "name": "Hotel Listing",
        "url": f"{BASE_URL}/hotels/hotel-listing/?location=bangalore&checkin=2026-02-26&checkout=2026-02-28&adults=1&rooms=1",
        "expected_content": ["hotel", "view", "rooms"],
        "expected_status": 200,
    },
    {
        "name": "Hotel Details",
        "url": f"{BASE_URL}/hotels/hotel-details/?property=bangalore-grand-stay-1-blr&checkin=2026-02-26&checkout=2026-02-28&adults=1&rooms=1",
        "expected_content": ["room", "booking"],
        "expected_status": 200,
    },
    {
        "name": "Hotel Booking",
        "url": f"{BASE_URL}/hotels/nhotel-booking/?property=bangalore-grand-stay-1-blr&room_type=1&checkin=2026-02-26&checkout=2026-02-28&adults=1&rooms=1&children=0",
        "expected_content": ["price", "checkout"],
        "expected_status": 200,
    },
]

print("=" * 70)
print("NEW ROUTES TEST SUITE")
print("=" * 70)

passed = 0
failed = 0

for test in tests:
    try:
        response = requests.get(test["url"], verify=False, timeout=10)
        status_ok = response.status_code == test["expected_status"]
        content_ok = any(content.lower() in response.text.lower() for content in test["expected_content"])
        
        test_passed = status_ok and content_ok
        
        status = "✅ PASS" if test_passed else "❌ FAIL"
        print(f"\n{status}: {test['name']}")
        print(f"  URL: {test['url'].split('?')[0]}")
        print(f"  Status Code: {response.status_code} (expected {test['expected_status']})")
        
        if not content_ok:
            print(f"  Content: Missing expected content")
        
        if test_passed:
            passed += 1
        else:
            failed += 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {test['name']}")
        print(f"  URL: {test['url']}")
        print(f"  Error: {str(e)}")
        failed += 1

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 70)
