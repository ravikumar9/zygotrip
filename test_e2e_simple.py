"""
Simple E2E test with browser automation
"""
import os
import sys
import django
from pathlib import Path
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.db import connection
from accounts.models import User, UserRole, Role
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:8000"
HEADLESS = False

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    safe_msg = ''.join(c for c in msg if ord(c) < 128)
    print(f"[{timestamp}] {safe_msg}")

def execute_sql(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        if query.strip().upper().startswith('SELECT'):
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

def create_test_accounts():
    log("Creating test accounts...")
    customer_role, _ = Role.objects.get_or_create(code='customer', defaults={'name': 'Customer'})
    
    customer_user, _ = User.objects.get_or_create(
        email='e2e_customer@test.com',
        defaults={'full_name': 'E2E Customer', 'is_active': True}
    )
    customer_user.set_password('TestPass123')
    customer_user.save()
    UserRole.objects.get_or_create(user=customer_user, role=customer_role)
    
    log("[OK] Created test account")
    return {
        'email': 'e2e_customer@test.com',
        'password': 'TestPass123',
    }

async def test_login_flow():
    log("STARTING LOGIN TEST")
    
    # Check server
    try:
        import urllib.request
        urllib.request.urlopen(f"{BASE_URL}/", timeout=2)
        log("[OK] Django server running")
    except:
        log("[ERROR] Django server NOT running")
        return False
    
    # Start browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()
        
        try:
            # Go to login
            log("Opening login page...")
            await page.goto(f"{BASE_URL}/login/", wait_until='networkidle', timeout=10000)
            log("[OK] Login page loaded")
            await page.screenshot(path="screenshot_login.png")
            
            # Check what fields exist
            email_field = await page.query_selector('input[id="id_username"]')
            if email_field:
                log("[OK] Found email field (id_username)")
            else:
                log("[ERROR] Email field not found")
                content = await page.content()
                if 'name="username"' in content:
                    log("[DEBUG] Found form with name='username'")
                return False
            
            # Fill form
            log("Filling login form...")
            await page.fill('input[id="id_username"]', 'e2e_customer@test.com', timeout=5000)
            await page.fill('input[id="id_password"]', 'TestPass123', timeout=5000)
            log("[OK] Form filled")
            
            # Submit
            log("Submitting login...")
            await page.click('button[type="submit"]', timeout=5000)
            log("[OK] Form submitted")
            
            # Wait for redirect
            await page.wait_for_url(f"{BASE_URL}/**", timeout=10000)
            log(f"[OK] Redirected to {page.url}")
            
            # Check cookies
            cookies = await page.context.cookies()
            has_session = any('session' in c['name'] for c in cookies)
            if has_session:
                log("[OK] Session cookie present")
            else:
                log("[ERROR] No session cookie")
                return False
            
            await page.screenshot(path="screenshot_after_login.png")
            log("[OK] LOGIN TEST PASSED")
            return True
            
        except Exception as e:
            log(f"[ERROR] Exception: {str(e)}")
            await page.screenshot(path="screenshot_error.png")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    try:
        creds = create_test_accounts()
        result = asyncio.run(test_login_flow())
        log("FINAL RESULT: PASS" if result else "FINAL RESULT: FAIL")
        sys.exit(0 if result else 1)
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
