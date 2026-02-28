#!/usr/bin/env python
"""Create test user accounts"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import UserProfile

# Create test user (traveler)
if not User.objects.filter(email='traveler@example.com').exists():
    user = User.objects.create_user(
        username='traveler',
        email='traveler@example.com',
        password='Test@123456',
        first_name='Test',
        last_name='User'
    )
    profile = UserProfile.objects.create(
        user=user,
        phone='+91-9876543210',
        role='traveler',
        is_active=True
    )
    print("✓ Traveler account created")
else:
    print("✓ Traveler account already exists")

# Create test owner
if not User.objects.filter(email='owner@example.com').exists():
    owner = User.objects.create_user(
        username='owner',
        email='owner@example.com',
        password='Owner@123456',
        first_name='Property',
        last_name='Owner'
    )
    profile = UserProfile.objects.create(
        user=owner,
        phone='+91-9876543211',
        role='property_owner',
        is_active=True
    )
    print("✓ Property owner account created")
else:
    print("✓ Property owner account already exists")

# Create test admin
if not User.objects.filter(email='admin@example.com').exists():
    admin = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='Admin@123456',
        first_name='System',
        last_name='Admin'
    )
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    profile = UserProfile.objects.create(
        user=admin,
        phone='+91-9876543212',
        role='admin',
        is_active=True
    )
    print("✓ Admin account created")
else:
    print("✓ Admin account already exists")

print("\n=== TEST CREDENTIALS ===")
print("Traveler: traveler@example.com / Test@123456")
print("Owner:    owner@example.com / Owner@123456")
print("Admin:    admin@example.com / Admin@123456")
