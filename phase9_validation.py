#!/usr/bin/env python
"""PHASE 9: Integration Stabilization Validation Script"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.db import connection
from django.conf import settings
from apps.booking.models import Booking
from apps.payments.models import Payment
from apps.booking.settlement_models import Settlement, SettlementLineItem

def test_database_connection():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("[PASS] Database connection OK")
        return True
    except Exception as e:
        print("[FAIL] Database connection: " + str(e))
        return False

def test_debug_mode():
    if settings.DEBUG:
        ssl_ok = not settings.SECURE_SSL_REDIRECT
        cookies_ok = not settings.SESSION_COOKIE_SECURE
        hsts_ok = settings.SECURE_HSTS_SECONDS == 0
        
        print("[PASS] DEBUG mode: " + str(settings.DEBUG))
        print("  [OK] SSL redirect disabled: " + str(ssl_ok))
        print("  [OK] Secure cookies disabled: " + str(cookies_ok))
        print("  [OK] HSTS disabled: " + str(hsts_ok))
        
        return ssl_ok and cookies_ok and hsts_ok
    else:
        print("[PASS] DEBUG mode: production")
        return True

def test_celery_settings():
    eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    beat_empty = len(getattr(settings, 'CELERY_BEAT_SCHEDULE', {})) == 0 if settings.DEBUG else True
    
    print("[PASS] Celery eager (DEBUG=" + str(settings.DEBUG) + "): " + str(eager))
    print("  [OK] Beat schedule disabled: " + str(beat_empty))
    
    return eager == settings.DEBUG and beat_empty

def test_model_registration():
    try:
        Booking.objects.count()
        print("[PASS] Booking model OK")
    except Exception as e:
        print("[FAIL] Booking: " + str(e))
        return False
    
    try:
        Payment.objects.count()
        print("[PASS] Payment model OK")
    except Exception as e:
        print("[FAIL] Payment: " + str(e))
        return False
    
    try:
        Settlement.objects.count()
        print("[PASS] Settlement model OK")
    except Exception as e:
        print("[FAIL] Settlement: " + str(e))
        return False
    
    try:
        SettlementLineItem.objects.count()
        print("[PASS] SettlementLineItem model OK")
    except Exception as e:
        print("[FAIL] SettlementLineItem: " + str(e))
        return False
    
    return True

def test_url_configuration():
    from django.urls import get_resolver, reverse, NoReverseMatch
    resolver = get_resolver()
    all_patterns = [str(p.pattern) for p in resolver.url_patterns]
    
    # Check for specific patterns we care about
    checks = {
        'admin': 'admin/' in all_patterns,
        'hotels': 'hotels/' in all_patterns,
        'booking': 'booking/' in all_patterns,
        'payments (invoice)': 'invoice/' in all_patterns,
        'dashboard_owner': 'owner/dashboard/' in all_patterns,
        'dashboard_admin': 'admin/dashboard/' in all_patterns,
        'dashboard_finance': 'finance/dashboard/' in all_patterns,
    }
    
    # Check for health via core app
    try:
        health_url = reverse('core:health_check')
        checks['health'] = True
    except NoReverseMatch:
        checks['health'] = False
    
    print("[PASS] URL patterns:")
    for key, status in checks.items():
        label = "[OK]" if status else "[X]"
        print("  " + label + " " + key)
    
    return all(checks.values())

def test_static_files():
    static_url_ok = settings.STATIC_URL == "/static/"
    static_root_ok = settings.STATIC_ROOT is not None
    
    print("[PASS] Static files:")
    print("  [OK] STATIC_URL: /static/" if static_url_ok else "[X]")
    print("  [OK] STATIC_ROOT configured" if static_root_ok else "[X]")
    
    return static_url_ok and static_root_ok

def test_migrations():
    from django.core.management import call_command
    from io import StringIO
    
    try:
        out = StringIO()
        call_command('showmigrations', stdout=out, verbosity=0)
        output = out.getvalue()
        
        applied = output.count("[X]")
        unapplied = output.count("[ ]")
        
        if unapplied == 0:
            print("[PASS] Migrations: All " + str(applied) + " applied")
            return True
        else:
            print("[WARN] Migrations: " + str(applied) + " applied, " + str(unapplied) + " pending")
            return False
    except Exception as e:
        print("[FAIL] Migration check: " + str(e))
        return False

def main():
    print("=" * 70)
    print("PHASE 9: INTEGRATION STABILIZATION VALIDATION")
    print("=" * 70)
    print("")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Debug Mode Settings", test_debug_mode),
        ("Celery Configuration", test_celery_settings),
        ("Model Registration", test_model_registration),
        ("URL Configuration", test_url_configuration),
        ("Static Files", test_static_files),
        ("Migrations", test_migrations),
    ]
    
    results = {}
    for name, test_func in tests:
        print("")
        print(name + ":")
        try:
            results[name] = test_func()
        except Exception as e:
            print("[FAIL] Error: " + str(e))
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print("")
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        label = "[PASS]" if result else "[FAIL]"
        print(label + " " + name)
    
    print("")
    print("Result: " + str(passed) + "/" + str(total) + " tests passed")
    
    if passed == total:
        print("")
        print("PHASE 9 VALIDATION COMPLETE - SYSTEM READY")
        return 0
    else:
        print("")
        print("ISSUES FOUND: " + str(total - passed) + " test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
