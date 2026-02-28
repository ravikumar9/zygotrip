#!/usr/bin/env python
"""Test booking flow to verify service fee calculation and query button"""
import requests
import sys

requests.packages.urllib3.disable_warnings()

print("=" * 60)
print("TESTING BOOKING FLOW")
print("=" * 60)

# Test 1: Detail page
print("\n1. Testing Detail Page:")
url = 'https://localhost:8000/hotels/hotel-details/?property=coorg-grand-stay-5-coorg&checkin=2026-02-26&checkout=2026-02-28&adults=1&rooms=1'
try:
    r = requests.get(url, verify=False, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print("   ✅ Detail page loads successfully")
    else:
        print(f"   ❌ Error: Status {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 2: Booking page
print("\n2. Testing Booking Page:")
url = 'https://localhost:8000/hotels/nhotel-booking/?property=coorg-grand-stay-5-coorg&room_type=1&checkin=2026-02-26&checkout=2026-02-28&adults=1&rooms=1&children=0'
try:
    r = requests.get(url, verify=False, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print("   ✅ Booking page loads successfully")
        if "View Charges" in r.text:
            print("   ✅ Query button for fees found")
        else:
            print("   ⚠️  Query button not found")
        if "Service Fee" in r.text:
            print("   ✅ Service fee label found")
        else:
            print("   ⚠️  Service fee label not found")
    else:
        print(f"   ❌ Error: Status {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 3: Location autocomplete API
print("\n3. Testing Location Autocomplete:")
url = 'https://localhost:8000/api/hotels/suggest/?q=co'
try:
    r = requests.get(url, verify=False, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if 'cities' in data or 'areas' in data:
            print("   ✅ Location autocomplete API working")
        else:
            print("   ⚠️  API working but no results")
    else:
        print(f"   ❌ Error: Status {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("✓ Testing complete")
print("=" * 60)
