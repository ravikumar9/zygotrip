"""
Seed missing latitude/longitude data for properties.
Run: python manage.py shell < seed_geolocation.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')

import django
django.setup()

from decimal import Decimal
from apps.hotels.models import Property
from apps.core.location_models import City

# Geolocation data for major Indian cities
CITY_COORDINATES = {
    'New Delhi': (28.7041, 77.1025),
    'Mumbai': (19.0760, 72.8777),
    'Bangalore': (12.9716, 77.5946),
    'Hyderabad': (17.3850, 78.4867),
    'Chennai': (13.0827, 80.2707),
    'Kolkata': (22.5726, 88.3639),
    'Pune': (18.5204, 73.8567),
    'Jaipur': (26.9124, 75.7873),
    'Lucknow': (26.8467, 80.9462),
    'Ahmedabad': (23.0225, 72.5714),
    'Coorg': (12.3382, 75.7273),
    'Madikeri': (12.4386, 75.7304),
}

PROPERTY_VARIATIONS = {
    'Coorg': [
        (12.3382 + 0.02, 75.7273 - 0.01),
        (12.3382 - 0.01, 75.7273 + 0.02),
        (12.3382 + 0.01, 75.7273 + 0.01),
    ],
    'Madikeri': [
        (12.4386 + 0.02, 75.7304 - 0.01),
        (12.4386 - 0.01, 75.7304 + 0.02),
    ],
}

print("[*] Seeding geolocation data...")

updated = 0
for prop in Property.objects.all():
    if prop.latitude and prop.longitude:
        continue
    
    # Ensure city is set
    try:
        city_obj = prop.city
    except:
        city_obj = None
    
    if not city_obj:
        city_name = prop.city_text or prop.area or 'Bangalore'
        try:
            city_obj = City.objects.filter(name__icontains=city_name).first() or City.objects.first()
            prop.city = city_obj
        except:
            prop.city = City.objects.first()
            city_obj = prop.city
    
    # Get coordinates based on city
    if city_obj:
        city_name = str(city_obj).split('(')[0].strip()
    else:
        city_name = 'Bangalore'
    
    # Check for specific property variations
    lat, lng = None, None
    for variation_city, coords_list in PROPERTY_VARIATIONS.items():
        if variation_city in city_name:
            lat, lng = coords_list[prop.id % len(coords_list)]
            break
    
    # Fall back to city coordinates
    if not lat or not lng:
        lat, lng = CITY_COORDINATES.get(city_name, (28.7041, 77.1025))
        # Add small variance for multiple properties in same city
        lat += (prop.id % 10) * 0.005
        lng += (prop.id % 10) * 0.005
    
    prop.latitude = Decimal(str(round(lat, 6)))
    prop.longitude = Decimal(str(round(lng, 6)))
    prop.save()
    updated += 1
    print(f"  [+] {prop.name}: {lat:.4f}, {lng:.4f}")

print(f"\n[OK] Updated {updated} properties with geolocation data")

# Verify
null_count = Property.objects.filter(latitude__isnull=True).count()
print(f"[CHECK] Properties with NULL latitude: {null_count}")