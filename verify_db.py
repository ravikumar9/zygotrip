import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.db import connection
from apps.hotels.models import Property

print('=== DATABASE VERIFICATION ===')
print()

# Check hotels using Django ORM
try:
    hotels = Property.objects.all()
    print(f'Total Properties: {hotels.count()}')
    
    # Check NULL slugs
    null_slug_count = Property.objects.filter(slug__isnull=True).count()
    print(f'Properties with NULL slugs: {null_slug_count}')
    
    # Check city_id
    null_city = Property.objects.filter(city_id__isnull=True).count()
    print(f'Properties with NULL city_id: {null_city}')
    
    # Show sample
    if hotels.exists():
        sample = hotels.first()
        print()
        print(f'Sample Property:')
        print(f'  Name: {sample.name}')
        print(f'  Slug: {sample.slug}')
        print(f'  City ID: {sample.city_id}')
        print(f'  Price: {sample.price if hasattr(sample, "price") else "N/A"}')
except Exception as e:
    print(f'Error checking properties: {e}')
    import traceback
    traceback.print_exc()

print()
print('[OK] Database check complete')