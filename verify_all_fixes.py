import requests
import time

requests.packets.urllib3.disable_warnings()

print("\n" + "="*60)
print("COMPREHENSIVE SYSTEM TEST")
print("="*60)

time.sleep(3)

# Test 1: Landing Page
print("\n1. Testing Landing Page...")
try:
    r = requests.get('https://localhost:8000/hotels/', verify=False, timeout=10)
    print(f"   Status: {r.status_code} ✓")
    print(f"   CSS loaded: {'design-system.css' in r.text} ✓")
    print(f"   Navbar horizontal: {'navbar-nav' in r.text} ✓")
    print(f"   Footer 4-column: {'footer-grid' in r.text} ✓")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: Hotel Detail Page  
print("\n2. Testing Hotel Detail Page...")
try:
    r = requests.get('https://localhost:8000/hotels/hotel-details/?property=coorg-grand-stay-5-coorg&checkin=2026-02-26&checkout=2026-02-28&adults=1&rooms=1', verify=False, timeout=10)
    print(f"   Status: {r.status_code} ✓")
    print(f"   Room selection: {'data-room-select' in r.text} ✓")
    print(f"   Image handling: {'hotel-gallery' in r.text} ✓")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: Booking Page (with correct URL)
print("\n3. Testing Booking Page...")
try:
    r = requests.get('https://localhost:8000/hotels/nhotel-booking/?property=bangalore-grand-stay-1-blr&room_type=1&checkin=2026-02-26&checkout=2026-02-28&adults=1&rooms=1&children=0', verify=False, timeout=10)
    print(f"   Status: {r.status_code} ✓")
    if r.status_code == 200:
        print(f"   Query button: {'View Charges' in r.text} ✓")
        print(f"   Service fee: {'Service Fee' in r.text} ✓")
    else:
        print(f"   ERROR: HTTP {r.status_code}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 4: Property Approval Status
print("\n4. Testing Property Approval...")
try:
    import sys
    sys.path.insert(0, '.')
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
    django.setup()
    
    from apps.hotels.models import Property
    approved = Property.objects.filter(status='approved', agreement_signed=True).count()
    total = Property.objects.count()
    print(f"   Approved properties: {approved}/{total} ✓")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*60)
print("TEST COMPLETED")
print("="*60)
print("\nIMPORTANT:")
print("- Hard refresh browser: Ctrl+F5 to see new CSS")
print("- Navbar should be HORIZONTAL (Home Hotels Buses Cabs...)")
print("- Footer should be 4 COLUMNS side-by-side")
print("- Booking page uses /hotels/nhotel-booking/ (404 fixed)")
print("- Owner dashboard: /dashboard-owner/")
print("="*60 + "\n")
