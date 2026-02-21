import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

client = Client()

print("UI REALITY TEST")
print("=" * 70)

# Test pages
test_pages = [
    ('/', 'Home'),
    ('/hotels/', 'Hotels'),
    ('/login/', 'Login'),
    ('/register/', 'Register'),
]

print("\n[TEST] Public Pages")
for url, name in test_pages:
    response = client.get(url)
    status = "OK" if response.status_code in [200, 301, 302] else "ERROR"
    print(f"  {name:20} - Status: {response.status_code:3} ({status})")

# Authenticated test
print("\n[TEST] Authenticated Pages")
user = User.objects.first()
if user:
    client.login(username=user.email, password='TestPass123!')  # Won't work, just test
    
    # Try some authenticated pages
    auth_pages = [
        ('/accounts/profile/', 'Profile'),
    ]
    
    for url, name in auth_pages:
        response = client.get(url)
        status = "OK" if response.status_code in [200] else "LOGIN_REQUIRED" if response.status_code == 302 else "ERROR"
        print(f"  {name:20} - Status: {response.status_code:3} ({status})")

print("\n[TEST] API Endpoints")
api_pages = [
    ('/api/search/hotels/?city_id=1', 'Hotels API'),
    ('/api/search/autocomplete/?q=taj', 'Autocomplete API'),
]

for url, name in api_pages:
    response = client.get(url)
    status = "OK" if response.status_code == 200 else "ERROR"
    print(f"  {name:20} - Status: {response.status_code:3} ({status})")
    
    if response.status_code == 200:
        import json
        try:
            data = response.json()
            if isinstance(data, dict):
                if 'results' in data:
                    count = len(data['results'])
                    print(f"    -> {count} results returned")
        except:
            pass

print("\n" + "=" * 70)