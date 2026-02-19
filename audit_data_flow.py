import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from hotels.models import Property
from apps.search.engine import search_engine

print("DATA FLOW TRACE: HOTEL ENTITY")
print("=" * 70)

# Find a hotel in DB
hotel = Property.objects.first()  # Use first hotel, we know it exists

if hotel:
    print(f"\n[DB] Hotel in database:")
    print(f"  ID: {hotel.id}")
    print(f"  Name: {hotel.name}")
    print(f"  City: {hotel.city.name if hotel.city else 'None'}")
    print(f"  Locality: {hotel.locality.name if hotel.locality else 'None'}")
    print(f"  Rating: {hotel.rating}")
    print(f"  Review Count: {hotel.review_count}")
    
    print(f"\n[ORM] Accessing through ORM:")
    print(f"  Type: {type(hotel).__name__}")
    print(f"  Fields: {[f.name for f in hotel._meta.fields[:6]]}")
    
    # Get through service
    print(f"\n[SERVICE] Through SearchService:")
    service = SearchService()
    results = service.search_hotels(city_code='BANGALORE', limit=1)
    
    if results:
        result = results[0]
        print(f"  Result type: {type(result).__name__}")
        print(f"  Fields returned: {list(result.keys())}")
        print(f"  Field values:")
        for k, v in list(result.items())[:6]:
            print(f"    - {k}: {v} (type: {type(v).__name__})")
        
        # Check for None values
        null_fields = [k for k, v in result.items() if v is None]
        if null_fields:
            print(f"\n  WARNING - Null fields: {null_fields}")
        
        # Check if matches DB
        print(f"\n[VALIDATION] Service vs DB:")
        print(f"  Name matches: {result.get('name') == hotel.name}")
        print(f"  City ID matches: {result.get('city_id') == hotel.city_id}")
        print(f"  Rating matches: {result.get('rating') == hotel.rating}")
    else:
        print(f"  [ERROR] No results from service")
    
    # Try API directly
    print(f"\n[API] Through HTTP:")
    from django.test import Client
    client = Client()
    response = client.get(f'/api/search/hotels/?city={hotel.city_id}&limit=1')
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            api_result = data['results'][0]
            print(f"  API returns: {list(api_result.keys())[:6]}")
            null_api_fields = [k for k, v in api_result.items() if v is None]
            if null_api_fields:
                print(f"  WARNING - Null in API: {null_api_fields}")
    else:
        print(f"  Status: {response.status_code}")
    
    # Check template rendering
    print(f"\n[TEMPLATE] Safe for template access:")
    critical_fields = ['id', 'name', 'rating', 'review_count', 'city', 'locality']
    for field in critical_fields:
        has_field = hasattr(hotel, field)
        print(f"  hotel.{field}: {has_field}")

else:
    print("[ERROR] No hotels found in Bangalore")
