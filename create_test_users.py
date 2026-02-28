#!/usr/bin/env python
"""Create test user accounts with correct custom User model"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.accounts.models import User

# Test credentials
test_accounts = [
    {
        'email': 'traveler@example.com',
        'password': 'Test@123456',
        'full_name': 'Test Traveler',
        'phone': '+91-9876543210',
        'role': 'traveler'
    },
    {
        'email': 'owner@example.com',
        'password': 'Owner@123456',
        'full_name': 'Property Owner',
        'phone': '+91-9876543211',
        'role': 'property_owner'
    },
    {
        'email': 'admin@example.com',
        'password': 'Admin@123456',
        'full_name': 'System Admin',
        'phone': '+91-9876543212',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True
    }
]

print("Creating test accounts...\n")

for account_data in test_accounts:
    email = account_data['email']
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        print(f"✓ {email} already exists")
        continue
    
    # Create the user
    user = User.objects.create_user(
        email=email,
        password=account_data['password'],
        full_name=account_data['full_name'],
        phone=account_data.get('phone', ''),
        role=account_data['role']
    )
    
    # Set staff/superuser if admin
    if account_data.get('is_staff'):
        user.is_staff = True
    if account_data.get('is_superuser'):
        user.is_superuser = True
        
    user.save()
    print(f"✓ Created {email} ({account_data['role']})")

print("\n" + "="*60)
print("TEST CREDENTIALS FOR MANUAL TESTING")
print("="*60)
print("Traveler: traveler@example.com / Test@123456")
print("Owner:    owner@example.com / Owner@123456")
print("Admin:    admin@example.com / Admin@123456")  
print("="*60)
