import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.hotels.models import Property
from apps.core.models import City

# Check if any hotels exist
hotel_count = Property.objects.count()
print(f"Total hotels in system: {hotel_count}")

if hotel_count > 0:
    # Get first hotel
    hotel = Property.objects.first()
    print(f"First hotel: {hotel.name}")
    if hotel.city:
        print(f"City: {hotel.city.name}")
    print(f"Hotel ID: {hotel.id}")
else:
    # Check cities
    city_count = City.objects.count()
    print(f"Total cities: {city_count}")
    cities = City.objects.all().values_list('name', 'code')[:5]
    print(f"Sample cities: {list(cities)}")