"""
AUTH FLOW TEST - End-to-end validation
Tests: login, register, session persistence, logout
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

User = get_user_model()
client = Client()

print("=" * 70)
print("AUTH FLOW INTEGRATION TESTS")
print("=" * 70)

# TEST 1: Login with existing user
print("\n[TEST 1] Login with valid credentials")
response = client.post('/login/', {
    'username': 'product_owner@test.com',
    'password': 'password123'
}, follow=True)
print(f"  Status: {response.status_code}")
print(f"  Redirected: {response.redirect_chain}")
if response.status_code == 200:
    print(f"  ✓ Page loaded")
else:
    print(f"  ✗ Failed: {response.status_code}")

# TEST 2: Session check
print("\n[TEST 2] Session persistence")
user_id = client.session.get('_auth_user_id')
print(f"  Session user_id: {user_id}")
if user_id:
    print(f"  ✓ Session active")
else:
    print(f"  ✗ No session")

# TEST 3: Invalid login
print("\n[TEST 3] Invalid credentials")
response = client.post('/login/', {
    'username': 'wrong@email.com',
    'password': 'wrongpass'
})
print(f"  Status: {response.status_code}")
print(f"  Has form errors: {'form' in response.context if response.context else False}")
if response.context and 'form' in response.context:
    errors = response.context['form'].errors
    print(f"  Errors: {dict(errors) if errors else 'None'}")

# TEST 4: Register
print("\n[TEST 4] Register new user")
response = client.post('/register/', {
    'email': 'testuser@test.com',
    'full_name': 'Test User',
    'password1': 'SecurePass123!',
    'password2': 'SecurePass123!'
}, follow=True)
print(f"  Status: {response.status_code}")
print(f"  Redirected: {response.redirect_chain}")

# Check if user created
new_user = User.objects.filter(email='testuser@test.com').first()
if new_user:
    print(f"  ✓ User created: {new_user.email}")
else:
    print(f"  ✗ User not created")
    if response.context and 'form' in response.context:
        print(f"  Form errors: {response.context['form'].errors}")

# TEST 5: CSRF token
print("\n[TEST 5] CSRF protection")
response = client.get('/login/')
csrf_token = response.context.get('csrf_token') if response.context else None
print(f"  CSRF token in template: {bool(csrf_token)}")
if csrf_token:
    print(f"  ✓ CSRF protected")
else:
    print(f"  ✗ No CSRF token")

# TEST 6: Form rendering
print("\n[TEST 6] Login form fields")
response = client.get('/login/')
if response.context and 'form' in response.context:
    form = response.context['form']
    print(f"  Fields: {list(form.fields.keys())}")
    for field_name, field in form.fields.items():
        print(f"    - {field_name}: {field.__class__.__name__}")
else:
    print("  ✗ Could not retrieve form from context")

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)