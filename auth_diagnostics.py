#!/usr/bin/env python3
"""
PHASE 1 DIAGNOSIS: AUTH SYSTEM ROOT CAUSE INVESTIGATION
Test register/login/logout flows with detailed error reporting
"""

import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
import django
django.setup()

from django.contrib.auth import authenticate
from django.test import Client
from django.db import connection
from accounts.models import User
from accounts.forms import RegisterForm, CustomAuthenticationForm

print("\n" + "="*80)
print("PHASE 1: AUTH SYSTEM DIAGNOSTICS")
print("="*80)

# TEST 1: Check if User can be created manually
print("\n[TEST 1] Manual User Creation")
print("-" * 80)

test_email = "manual_test@example.com"
test_password = "TestPass123!@#"
test_name = "Manual Test User"

# Clean slate
User.objects.filter(email=test_email).delete()

try:
    user = User.objects.create_user(
        email=test_email,
        password=test_password,
        full_name=test_name
    )
    print(f"[PASS] User created: {user.email}")
    print(f"  ID: {user.id}")
    print(f"  Full name: {user.full_name}")
    print(f"  Password hash set: {bool(user.password)}")
    
    # Query DB to verify
    db_user = User.objects.get(email=test_email)
    print(f"[DB CHECK] User exists in database: {db_user.email}")
except Exception as e:
    print(f"[FAIL] User creation failed: {e}")
    traceback.print_exc()

# TEST 2: Test authentication
print("\n[TEST 2] Authentication Backend")
print("-" * 80)

try:
    auth_user = authenticate(username=test_email, password=test_password)
    if auth_user:
        print(f"[PASS] Authentication successful: {auth_user.email}")
    else:
        print(f"[FAIL] Authentication returned None")
        
        # Diagnose why
        print("\n[DIAGNOSIS] Checking authentication issue:")
        user_exists = User.objects.filter(email=test_email).exists()
        print(f"  - User exists: {user_exists}")
        
        if user_exists:
            db_user = User.objects.get(email=test_email)
            print(f"  - User ID: {db_user.id}")
            print(f"  - Password is set: {bool(db_user.password)}")
            print(f"  - Is active: {db_user.is_active if hasattr(db_user, 'is_active') else 'N/A'}")
            
            # Try checking password directly
            pwd_check = db_user.check_password(test_password)
            print(f"  - Password check result: {pwd_check}")
except Exception as e:
    print(f"[FAIL] Authentication test failed: {e}")
    traceback.print_exc()

# TEST 3: Register form
print("\n[TEST 3] RegisterForm Validation")
print("-" * 80)

form_email = "form_test@example.com"
form_password = "FormPass123!@#"
form_name = "Form Test User"

# Clean slate
User.objects.filter(email=form_email).delete()

form_data = {
    'email': form_email,
    'full_name': form_name,
    'password1': form_password,
    'password2': form_password,
}

try:
    form = RegisterForm(data=form_data)
    if form.is_valid():
        print(f"[PASS] RegisterForm is valid")
        
        # Save the form
        user = form.save()
        print(f"[PASS] User saved from form: {user.email}")
        print(f"  ID: {user.id}")
        
        # Check DB
        db_user = User.objects.get(email=form_email)
        print(f"[DB CHECK] User in database: {db_user.email}")
    else:
        print(f"[FAIL] RegisterForm validation failed")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
except Exception as e:
    print(f"[FAIL] RegisterForm test failed: {e}")
    traceback.print_exc()

# TEST 4: Client login/register flow
print("\n[TEST 4] Django Client HTTP Flow")
print("-" * 80)

client = Client()

# First, test register POST
register_email = "client_test@example.com"
register_password = "ClientPass123!@#"
register_name = "Client Test User"

User.objects.filter(email=register_email).delete()

print("\n[SUB-TEST 4A] Register via POST")
register_data = {
    'email': register_email,
    'full_name': register_name,
    'password1': register_password,
    'password2': register_password,
}

try:
    response = client.post('/register/', register_data, follow=False)
    print(f"  Response status: {response.status_code}")
    print(f"  Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")
    print(f"  Response redirect location: {response.get('Location', 'No redirect')}")
    
    # Check if user was created
    user_exists = User.objects.filter(email=register_email).exists()
    print(f"  User in DB after POST: {user_exists}")
    
    if user_exists:
        user = User.objects.get(email=register_email)
        print(f"  [PASS] User created: {user.email} (ID: {user.id})")
    else:
        print(f"  [FAIL] User NOT created after register POST")
        
except Exception as e:
    print(f"  [FAIL] Register POST failed: {e}")
    traceback.print_exc()

# TEST 5: Login flow
print("\n[SUB-TEST 4B] Login via POST")

# Create user first
login_email = "login_test@example.com"
login_password = "LoginPass123!@#"
login_name = "Login Test User"

User.objects.filter(email=login_email).delete()
login_user = User.objects.create_user(email=login_email, password=login_password, full_name=login_name)
print(f"  Test user created: {login_user.email}")

# Clear cookies
client = Client()

# Now login
login_data = {
    'username': login_email,
    'password': login_password,
}

try:
    response = client.post('/login/', login_data, follow=False)
    print(f"  Response status: {response.status_code}")
    print(f"  Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")
    
    # Check session
    if 'sessionid' in client.cookies:
        print(f"  [PASS] Session cookie created: {client.cookies['sessionid'].value[:30]}...")
    else:
        print(f"  [FAIL] No session cookie after login POST")
    
    # Check if user is in session
    if response.wsgi_request and hasattr(response.wsgi_request, 'user'):
        print(f"  User in request: {response.wsgi_request.user}")
    
except Exception as e:
    print(f"  [FAIL] Login POST failed: {e}")
    traceback.print_exc()

# TEST 6: Database check
print("\n[TEST 6] Database Integrity")
print("-" * 80)

with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM accounts_user")
    user_count = cursor.fetchone()[0]
    print(f"Total users in DB: {user_count}")
    
    # Show recent users
    cursor.execute("SELECT id, email, full_name FROM accounts_user ORDER BY created_at DESC LIMIT 5")
    print("\nMost recent users:")
    for row in cursor.fetchall():
        print(f"  ID: {row[0]}, Email: {row[1]}, Name: {row[2]}")

print("\n" + "="*80)
print("DIAGNOSTICS COMPLETE")
print("="*80 + "\n")
