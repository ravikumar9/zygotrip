#!/usr/bin/env python
"""Verify login form displays validation errors"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client

client = Client()

print('[TEST] Login with invalid credentials - check HTML response')
response = client.post('/login/', {
    'username': 'test@example.com',
    'password': 'WrongPassword'
})

print(f'Status: {response.status_code}')

# Check if response contains error message
content = response.content.decode('utf-8')

if 'correct email and password' in content.lower() or 'invalid' in content.lower():
    print('[PASS] Form displays validation error')
else:
    print('[FAIL] No error message in response')
    
# Look for form elements
if 'Please enter a correct email and password' in content:
    print('[PASS] Found exact Django error message')
elif 'form' in content.lower() and 'password' in content.lower():
    print('[PASS] Form is rendered with password field')
    
    # Check for error display area
    if 'alert' in content.lower() or 'error' in content.lower():
        print('[PASS] Error display area found in template')

