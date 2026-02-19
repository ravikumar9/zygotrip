#!/usr/bin/env python
"""Auth system authentication backend test"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

# Test 1: Authenticate with valid credentials
print('[TEST 1] Authenticate with valid email and password')
user = authenticate(username='test@example.com', password='TestPass123!')
print(f'  User authenticated: {user is not None}')
if user:
    print(f'  User email: {user.email}')
    print(f'  ✓ PASS')
else:
    print(f'  ✗ FAIL')

# Test 2: Authenticate with invalid credentials
print()
print('[TEST 2] Authenticate with invalid password')
user = authenticate(username='test@example.com', password='WrongPassword')
print(f'  User authenticated: {user is not None}')
print(f'  ✓ PASS - Correctly rejected' if user is None else f'  ✗ FAIL - Should have rejected')

# Test 3: Check user exists
print()
print('[TEST 3] User exists in database')
user = User.objects.filter(email='test@example.com').first()
print(f'  User found: {user is not None}')
if user:
    print(f'  Email: {user.email}')
    print(f'  Full name: {user.full_name}')
    print(f'  ✓ PASS')
else:
    print(f'  ✗ FAIL')

# Test 4: Custom AuthenticationForm test
print()
print('[TEST 4] CustomAuthenticationForm validates email')
from accounts.forms import CustomAuthenticationForm

form = CustomAuthenticationForm(data={
    'username': 'TEST@EXAMPLE.COM',  # uppercase
    'password': 'TestPass123!'
})
print(f'  Form valid: {form.is_valid()}')
if form.is_valid():
    print(f'  ✓ PASS - Form normalizes email to lowercase')
else:
    print(f'  Form errors: {form.errors}')
    print(f'  ✗ FAIL')
