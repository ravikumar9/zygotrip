"""Auth diagnostics"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Role, UserRole
from django.conf import settings

User = get_user_model()

print("=" * 70)
print("AUTH SYSTEM DIAGNOSTIC")
print("=" * 70)

# Users
print(f"\n1. USERS: {User.objects.count()} total")
for user in User.objects.all()[:2]:
    roles = list(UserRole.objects.filter(user=user).values_list('role__code', flat=True))
    print(f"   - {user.email}: {roles or 'No roles'}")

# Roles
print(f"\n2. ROLES: {Role.objects.count()} total")
for role in Role.objects.all():
    print(f"   - {role.code}: {role.name}")

# Security
print(f"\n3. SECURITY SETTINGS:")
print(f"   DEBUG: {settings.DEBUG}")
print(f"   CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
print(f"   SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")

# Forms
from accounts.forms import RegisterForm
form = RegisterForm()
print(f"\n4. REGISTER FORM FIELDS: {list(form.fields.keys())}")

print("\n✓ Complete")
