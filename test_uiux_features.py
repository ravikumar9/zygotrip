#!/usr/bin/env python
"""Test UI/UX improvements: calendar, auto-suggestion, property counts"""
import requests
import re
from datetime import datetime, timedelta

requests.packages.urllib3.disable_warnings()

BASE_URL = "https://localhost:8000"

print("=" * 70)
print("UI/UX IMPROVEMENTS TEST SUITE")
print("=" * 70)

# Test 1: Calendar - Check if min attribute is set to disable past dates
print("\n1. CALENDAR TEST - Past dates should be disabled")
print("-" * 70)
response = requests.get(f"{BASE_URL}/hotels/", verify=False, timeout=10)
today = datetime.now().strftime("%Y-%m-%d")

if f'min="{today}"' in response.text or f"min='{today}'" in response.text:
    print(f"✅ PASS: Calendar has min attribute set to {today}")
else:
    print(f"❌ FAIL: Calendar min attribute not found or not set correctly")
    
if "min=" in response.text:
    print("✅ PASS: min attribute is present in date inputs")
else:
    print("❌ FAIL: min attribute not found in date inputs")

# Test 2: Auto-suggestion - Check if property count is displayed
print("\n2. AUTO-SUGGESTION TEST - Property counts should be displayed")
print("-" * 70)

response = requests.get(f"{BASE_URL}/api/hotels/suggest/?q=bangalore", verify=False, timeout=10)
if response.status_code == 200:
    data = response.json()
    
    # Check if cities have property_count
    if data.get('cities'):
        city = data['cities'][0]
        if 'property_count' in city:
            print(f"✅ PASS: Cities have property_count field: {city.get('property_count')} properties")
        else:
            print(f"❌ FAIL: Cities missing property_count field")
            print(f"  City data: {city}")
    
    # Check if areas have property_count
    if data.get('areas'):
        area = data['areas'][0]
        if 'property_count' in area:
            print(f"✅ PASS: Areas have property_count field: {area.get('property_count')} properties")
        else:
            print(f"❌ FAIL: Areas missing property_count field")
            print(f"  Area data: {area}")
else:
    print(f"❌ FAIL: API returned status {response.status_code}")

# Test 3: Auto-suggestion dropdown - Check if it's wide enough
print("\n3. AUTO-SUGGESTION DROPDOWN WIDTH TEST")
print("-" * 70)

response = requests.get(f"{BASE_URL}/hotels/", verify=False, timeout=10)
if "min-width: 280px" in response.text or "width: 100%" in response.text:
    print("✅ PASS: Dropdown has width styling")
else:
    print("❌ FAIL: Dropdown styling not found")

if "autosuggest-count" in response.text:
    print("✅ PASS: Property count display element present")
else:
    print("❌ FAIL: Property count display element not found")

# Test 4: Form action - Check if it uses new route
print("\n4. FORM ACTION TEST - Should use /hotels/hotel-listing/")
print("-" * 70)

response = requests.get(f"{BASE_URL}/hotels/", verify=False, timeout=10)
if '/hotels/hotel-listing' in response.text:
    print("✅ PASS: Form action uses new /hotels/hotel-listing/ route")
else:
    print("❌ FAIL: Form action not using new route")

print("\n" + "=" * 70)
print("UI/UX TESTS COMPLETE")
print("=" * 70)
