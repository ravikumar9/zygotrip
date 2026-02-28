import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip.settings')
django.setup()

from apps.hotels.models import Property, City

print('=== ALL CITIES ===')
for c in City.objects.all():
    state = getattr(c, 'state', 'N/A')
    print(f'  ID={c.id} name={repr(c.name)} state={state}')

print()
print('=== ALL PROPERTIES ===')
for p in Property.objects.select_related('city').all():
    print(f'  ID={p.id} name={repr(p.name)} status={p.status} agreement={p.agreement_signed} city={p.city} area={repr(p.area)} lat={p.latitude} lng={p.longitude}')

print()
print('=== OTA VISIBLE ===')
from apps.hotels.ota_selectors import ota_visible_properties
qs = ota_visible_properties()
print(f'  count={qs.count()}')
for p in qs:
    print(f'  - {p.id}: {p.name}')

print()
print('=== SEARCH LOGIC (location=Bangalore) ===')
from apps.hotels.ota_selectors import get_ota_context
try:
    result = get_ota_context({'location': 'Bangalore', 'checkin': '2026-02-28', 'checkout': '2026-03-01', 'adults': '1', 'rooms': '1'})
    print(f"  properties count: {len(result.get('properties', []))}")
    print(f"  total_count: {result.get('total_count')}")
    print(f"  base_count: {result.get('base_count')}")
    print(f"  search_location: {result.get('search_location')}")
except Exception as e:
    import traceback
    print(f"  ERROR: {e}")
    traceback.print_exc()
