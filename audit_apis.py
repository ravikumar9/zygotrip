import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

import json
from django.test import Client
from django.urls import reverse

client = Client()

print("API ENDPOINT VALIDATION")
print("=" * 70)

# Test endpoints
endpoints = [
    ('/api/search/hotels/?city=1&check_in=2026-02-18', 'Hotel Search'),
    ('/api/search/autocomplete/?q=Ban', 'Autocomplete'),
    ('/api/search/map/?ne_lat=12.5&ne_lng=77.6&sw_lat=12.3&sw_lng=77.4', 'Map Search'),
    ('/api/search/city/BANGALORE/', 'City Context'),
]

for endpoint, name in endpoints:
    print(f"\n[TEST] {name}")
    print(f"  URL: {endpoint}")
    
    try:
        response = client.get(endpoint)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  Valid JSON: YES")
                print(f"  Response type: {type(data).__name__}")
                
                if isinstance(data, dict):
                    print(f"  Top-level keys: {list(data.keys())[:5]}")
                    
                    # Check for null values in critical fields
                    if 'results' in data and isinstance(data['results'], list):
                        if data['results']:
                            first_item = data['results'][0]
                            print(f"  Sample result: {list(first_item.keys())[:3]}")
                            
                            # Check for None values
                            none_fields = [k for k, v in first_item.items() if v is None]
                            if none_fields:
                                print(f"  WARNING: Null fields: {none_fields[:3]}")
                    
                    print(f"  [PASS] Valid JSON schema")
                else:
                    print(f"  [OK] List response with {len(data)} items")
                    
            except json.JSONDecodeError:
                print(f"  Valid JSON: NO")
                print(f"  [FAIL] Invalid JSON response")
        else:
            print(f"  [FAIL] Status {response.status_code}")
            
    except Exception as e:
        print(f"  [FAIL] Exception: {str(e)[:60]}")

print("\n" + "=" * 70)
