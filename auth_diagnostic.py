"""
Auth System Diagnostic - Check login/register flow
"""
import os
import sys
import django

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
    django.setup()
    print("✓ Django setup complete", flush=True)
    
    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role, UserRole
    
    User = get_user_model()  # Use swapped user model
    
    print("=" * 60, flush=True)
    print("AUTH SYSTEM DIAGNOSTIC", flush=True)
    print("=" * 60, flush=True)
    
    # Check users
    user_count = User.objects.count()
    print(f"\n1. Users in system: {user_count}", flush=True)
    
    if user_count > 0:
        for user in User.objects.all()[:3]:
            roles = UserRole.objects.filter(user=user)
            role_list = ", ".join([r.role.code for r in roles])
            print(f"   - {user.username} ({user.email}): {role_list or 'No roles'}", flush=True)
    
    # Check roles
    roles = Role.objects.all()
    print(f"\n2. Available roles: {roles.count()}")
    for role in roles:
        print(f"   - {role.code}: {role.name}")
    
    # Check Django settings
    from django.conf import settings
    print(f"\n3. Security Settings:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SECRET_KEY configured: {bool(settings.SECRET_KEY and settings.SECRET_KEY != 'unsafe-dev-key')}")
    print(f"   CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
    print(f"   SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
    print(f"   AUTHENTICATION_BACKENDS: {settings.AUTHENTICATION_BACKENDS}")
    
    # Check RegisterForm
    from apps.accounts.forms import RegisterForm
    form = RegisterForm()
    print(f"\n4. Register Form Fields:")
    for field_name in form.fields:
        print(f"   - {field_name}")
    
    # Check LoginView
    print(f"\n5. LoginView Configuration:")
    from apps.accounts.views import LoginView
    print(f"   template_name: {LoginView.template_name}")
    print(f"   redirect_authenticated_user: {LoginView.redirect_authenticated_user}")
    
    print("\n✓ Diagnostics complete")
    
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()