#!/usr/bin/env python
"""Test auth system after fixes"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_login():
    """Test login with email-based authentication"""
    client = Client()
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={'full_name': 'Test User'}
    )
    if created:
        user.set_password('TestPass123!')
        user.save()
    
    print('[TEST 1] Login with valid email and password')
    response = client.post('/login/', {
        'username': 'test@example.com',  # CustomAuthenticationForm expects 'username' field with email value
        'password': 'TestPass123!'
    })
    print(f'  Status: {response.status_code}')
    print(f'  Redirected: {response.status_code in [301, 302, 303, 307, 308]}')
    
    # Check session
    session_user_id = client.session.get('_auth_user_id')
    print(f'  Session user_id: {session_user_id}')
    print(f'  ✓ PASS - Session created' if session_user_id == str(user.id) else f'  ✗ FAIL - No session')
    
    print()
    print('[TEST 2] Login with invalid credentials')
    client.logout()
    response = client.post('/login/', {
        'username': 'test@example.com',
        'password': 'WrongPassword123!'
    })
    print(f'  Status: {response.status_code}')
    
    # Check form errors
    if response.context:
        form = response.context.get('form')
        if form:
            print(f'  Form errors: {bool(form.errors)}')
            if form.errors:
                print(f'  Error messages: {form.errors}')
                print(f'  ✓ PASS - Form validation working')
            else:
                print(f'  ✗ FAIL - No form errors shown')
        else:
            print(f'  ✗ FAIL - No form in context')
    else:
        print(f'  ✗ FAIL - No context (redirect)')
    
    print()
    print('[TEST 3] Register new user')
    response = client.post('/register/', {
        'email': 'newuser@example.com',
        'full_name': 'New User',
        'password1': 'NewPass123!',
        'password2': 'NewPass123!'
    })
    print(f'  Status: {response.status_code}')
    
    # Check if redirect (successful registration)
    if response.status_code in [301, 302, 303, 307, 308]:
        print(f'  Redirected to: {response.get("Location", "unknown")}')
        print(f'  ✓ PASS - Registration successful')
    else:
        print(f'  Response type: {response.status_code}')
        if response.context:
            form = response.context.get('form')
            if form:
                print(f'  Form errors: {form.errors}')
        print(f'  ✗ FAIL - Registration failed')
    
    # Verify user was created
    new_user = User.objects.filter(email='newuser@example.com').first()
    if new_user:
        print(f'  User created: {new_user.email}')
        print(f'  ✓ PASS - User in database')
    else:
        print(f'  ✗ FAIL - User not created')
    
    print()
    print('[TEST 4] Check template field access (home page)')
    client.logout()
    client.login(username='test@example.com', password='TestPass123!')
    
    response = client.get('/')
    print(f'  Status: {response.status_code}')
    
    if response.status_code == 200:
        print(f'  ✓ PASS - Home page renders without 500 error')
    else:
        print(f'  ✗ FAIL - Home page error')
        if hasattr(response, 'content'):
            print(f'  Response: {response.content[:500]}')
    
    print()
    print('[TEST 5] Logout')
    response = client.get('/accounts/logout/')
    print(f'  Status: {response.status_code}')
    
    session_user_id = client.session.get('_auth_user_id')
    print(f'  Session cleared: {session_user_id is None}')
    print(f'  ✓ PASS - Logout successful' if session_user_id is None else f'  ✗ FAIL - Session still exists')

if __name__ == '__main__':
    test_login()