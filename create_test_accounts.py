#!/usr/bin/env python
"""
Create test accounts with proper roles for Phase 2 validation.
Run: python manage.py shell < create_test_accounts.py
"""

from apps.accounts.models import User, UserRole, Role
from django.db import IntegrityError

# Test credentials to create
TEST_ACCOUNTS = [
    {
        'email': 'customer@test.com',
        'username': 'customer',
        'password': 'TestPass123',
        'first_name': 'Test',
        'last_name': 'Customer',
        'roles': ['customer']
    },
    {
        'email': 'owner@test.com',
        'username': 'owner',
        'password': 'TestPass123',
        'first_name': 'Test',
        'last_name': 'Owner',
        'roles': ['property_owner']
    },
    {
        'email': 'bus_operator@test.com',
        'username': 'bus_operator',
        'password': 'TestPass123',
        'first_name': 'Test',
        'last_name': 'BusOp',
        'roles': ['bus_owner']
    },
    {
        'email': 'cab_operator@test.com',
        'username': 'cab_operator',
        'password': 'TestPass123',
        'first_name': 'Test',
        'last_name': 'CabOp',
        'roles': ['cab_owner']
    },
    {
        'email': 'admin@test.com',
        'username': 'admin',
        'password': 'AdminPass123',
        'first_name': 'Admin',
        'last_name': 'User',
        'roles': ['admin']
    }
]

print("[*] Creating test accounts for Phase 2 validation...")

for account in TEST_ACCOUNTS:
    email = account['email']
    username = account['username']
    password = account['password']
    
    try:
        # Create user if not exists
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'first_name': account['first_name'],
                'last_name': account['last_name'],
                'is_active': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"[+] Created user: {email}")
        else:
            print(f"[*] User already exists: {email}")
        
        # Assign roles
        for role_name in account['roles']:
            try:
                role = Role.objects.get(name=role_name)
                user_role, created = UserRole.objects.get_or_create(
                    user=user,
                    role=role
                )
                if created:
                    print(f"    [+] Assigned role: {role_name}")
                else:
                    print(f"    [*] Role already assigned: {role_name}")
            except Role.DoesNotExist:
                print(f"    [!] Role not found: {role_name} (skipping)")
                
    except Exception as e:
        print(f"[!] Error creating account {email}: {str(e)}")

print("\n[✓] Test account creation complete!")
print("\nWorking credentials:")
for account in TEST_ACCOUNTS:
    print(f"  - {account['email']} / {account['password']} ({', '.join(account['roles'])})")