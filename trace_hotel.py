import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.hotels.models import Property
from django.test import Client

print("DATA FLOW TRACE: HOTEL ENTITY")
print("=" * 70)

# Get a real hotel
hotel = Property.objects.first()

print(f"\n[LAYER 1 - DATABASE]")
print(f"  Hotel ID: {hotel.id}")
print(f"  Name: {hotel.name}")
print(f"  City ID: {hotel.city_id}")
print(f"  City Name: {hotel.city.name if hotel.city else 'NULL'}")
print(f"  Rating: {hotel.rating}")
print(f"  Review Count: {hotel.review_count}")
print(f"  Locality: {hotel.locality if hotel.locality else 'NULL'}")

# Key DB issue: locality is None
if hotel.locality is None:
    print(f"  [ISSUE] Hotel has no locality assigned")

print(f"\n[LAYER 2 - SERIALIZATION (API)]")
client = Client()

# Test the actual API being used in views
response = client.get(f'/api/search/hotels/?city={hotel.city_id}&limit=1')
print(f"  Status: {response.status_code}")

if response.status_code == 200:
    import json
    data = response.json()
    if data.get('results'):
        api_item = data['results'][0]
        print(f"  Sample fields from API:")
        print(f"    - id: {api_item.get('id')}")
        print(f"    - name: {api_item.get('name')}")
        print(f"    - rating: {api_item.get('rating')}")
        print(f"    - city_id: {api_item.get('city_id')}")
        
        # Check for null values
        null_fields = {k: v for k, v in api_item.items() if v is None}
        if null_fields:
            print(f"  [ISSUE] Null fields in API response: {list(null_fields.keys())}")

print(f"\n[LAYER 3 - TEMPLATE ACCESS]")
# Check if template can safely access fields
safe_fields = ['id', 'name', 'rating', 'review_count', 'city']
unsafe_fields = []

for field_name in safe_fields:
    has_it = hasattr(hotel, field_name) and getattr(hotel, field_name) is not None
    status = "OK" if has_it else "NULL/MISSING"
    print(f"  hotel.{field_name}: {status}")
    if not has_it:
        unsafe_fields.append(field_name)

if unsafe_fields:
    print(f"\n  [ISSUE] Template would crash on: {unsafe_fields}")
else:
    print(f"\n  [SAFE] All fields accessible")

print("\n" + "=" * 70)