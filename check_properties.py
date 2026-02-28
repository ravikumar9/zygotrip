from apps.hotels.ota_selectors import ota_visible_properties
from django.db.models import Q
from apps.hotels.models import Property

# Check available properties
all_props = Property.objects.all().count()
udaipur_props = Property.objects.filter(city='Udaipur').count()
visible_props = ota_visible_properties().count()

print(f"Total properties: {all_props}")
print(f"Udaipur properties: {udaipur_props}")
print(f"Visible properties: {visible_props}")

# List first property
first_prop = Property.objects.first()
if first_prop:
    print(f"\nFirst property: {first_prop.name} ({first_prop.city})")
    print(f"Status: {first_prop.status}")
else:
    print("\nNo properties found!")
