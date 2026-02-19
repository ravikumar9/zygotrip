#!/usr/bin/env python
"""Debug auth test responses"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

client = Client()

# Test invalid login
print('[DEBUG] Testing invalid login response')
response = client.post('/login/', {
    'username': 'test@example.com',
    'password': 'WrongPassword123!'
})
print(f'Status: {response.status_code}')
print(f'Has context: {response.context is not None}')
print(f'Content type: {response.get("Content-Type", "unknown")}')
print(f'Content length: {len(response.content) if response.content else 0}')

# Print first 500 chars of response
if response.content:
    content_str = response.content.decode('utf-8', errors='ignore')[:500]
    print(f'Response preview: {content_str}')
    
    if 'error' in content_str.lower() or 'login' in content_str.lower():
        print('✓ Response contains form data')
    else:
        print('✗ Response does not seem to contain login form')

