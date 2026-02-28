import os, sys, django
sys.path.insert(0, 'c:\Users\ravi9\Downloads\Zy\zygotrip')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip.settings')
django.setup()

from apps.hotels.ota_selectors import ota_visible_properties, get_ota_context
from django.test import RequestFactory

# Create request object to simulate browser request
factory = RequestFactory()
request = factory.get('/hotels/hotel-listing/', {
    'location': 'Udaipur',
    'checkin': '2026-03-06',
    'checkout': '2026-03-07',
    'adults': '2',
    'rooms': '1'
})

# Add session and user
from django.contrib.sessions.middleware import SessionMiddleware
middleware = SessionMiddleware(lambda x: x)
middleware.process_request(request)
request.user = None

# Get OTA context
context = get_ota_context(request)

print("\n=== OTA CONTEXT ===")
print(f"Total hotels: {len(context['hotels'])}")
print(f"Empty state: {context['empty_state']}")
print(f"Total count: {context['total_count']}")
print(f"Visible properties: {ota_visible_properties().count()}")

if context['hotels']:
    print(f"\nFirst hotel: {context['hotels'][0]}")
else:
    print("\n✗ NO HOTELS IN CONTEXT!")
    print(f"Empty state message: {context['empty_state_message']}")
