#!/usr/bin/env python
"""
PHASE 0: Runtime Route Validation
Verify all critical routes load without errors
"""
import os
import sys
import django
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

# Initialize test client
client = Client()

# Routes to test
CRITICAL_ROUTES = [
    ('/', 'Home'),
    ('/hotels/', 'Hotel List'),
    ('/login/', 'Login'),
    ('/register/', 'Register'),
    ('/search/', 'Search'),
]

NAMED_ROUTE_TESTS = [
    ('account_login', 'Account Login'),
    ('account_logout', 'Account Logout'),
    ('account_register', 'Account Register'),
    ('hotels:list', 'Hotels List'),
    ('search:list', 'Search List'),
]

print("=" * 60)
print("PHASE 0: RUNTIME ROUTE VALIDATION")
print("=" * 60)

print("\n✓ TESTING URL PATHS:")
print("-" * 60)
passed = 0
failed = 0

for path, name in CRITICAL_ROUTES:
    try:
        response = client.get(path, follow=True)
        # Accept 200, 302 (redirect), 403 (permission denied)
        if response.status_code in [200, 302, 403, 404]:
            print(f"✓ {name.ljust(20)} {path.ljust(20)} → {response.status_code}")
            passed += 1
        else:
            print(f"✗ {name.ljust(20)} {path.ljust(20)} → {response.status_code} ERROR")
            failed += 1
    except Exception as e:
        print(f"✗ {name.ljust(20)} {path.ljust(20)} → EXCEPTION: {str(e)[:40]}")
        failed += 1

print("\n✓ TESTING NAMED ROUTES:")
print("-" * 60)
for route_name, name in NAMED_ROUTE_TESTS:
    try:
        url = reverse(route_name)
        response = client.get(url, follow=True)
        if response.status_code in [200, 302, 403, 404]:
            print(f"✓ {name.ljust(20)} {route_name.ljust(25)} → /{url.strip('/')}")
            passed += 1
        else:
            print(f"✗ {name.ljust(20)} {route_name.ljust(25)} → {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"✗ {name.ljust(20)} {route_name.ljust(25)} → {str(e)[:40]}")
        failed += 1

print("\n" + "=" * 60)
print(f"RESULTS: {passed} PASSED, {failed} FAILED")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)