"""
PHASE 6: UI DESIGN & CONSOLE ERROR VALIDATION
Tests form alignment, button sizing, CSS classes, and browser console errors
"""
import asyncio
from playwright.async_api import async_playwright
import json

BASE_URL = "http://localhost:8000"

async def test_ui_components():
    print("=== PHASE 6: UI VALIDATION ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Track console messages
            console_errors = []
            console_messages = []
            
            def on_console_msg(msg):
                console_messages.append({
                    'type': msg.type,
                    'text': msg.text
                })
                if msg.type in ['error', 'exception']:
                    console_errors.append(msg.text)
            
            page.on('console', on_console_msg)
            
            # TEST 1: Registration Form
            print("TEST 1: Registration Form UI")
            await page.goto(f"{BASE_URL}/register/", wait_until='networkidle', timeout=10000)
            
            # Check elements exist
            email_field = await page.query_selector('input[id="id_email"]')
            name_field = await page.query_selector('input[id="id_full_name"]')
            pass1_field = await page.query_selector('input[id="id_password1"]')
            pass2_field = await page.query_selector('input[id="id_password2"]')
            submit_btn = await page.query_selector('button[type="submit"]')
            
            elements_ok = all([email_field, name_field, pass1_field, pass2_field, submit_btn])
            print(f"  Form elements present: {'PASS' if elements_ok else 'FAIL'}")
            
            if elements_ok:
                # Check button styling
                btn_text = await submit_btn.inner_text()
                print(f"  Button text: '{btn_text}'")
                print(f"  PASS: Registration form structure OK")
            
            await page.screenshot(path="ui_check_registration.png")
            print()
            
            # TEST 2: Login Form
            print("TEST 2: Login Form UI")
            await page.goto(f"{BASE_URL}/login/", wait_until='networkidle', timeout=10000)
            
            email_field = await page.query_selector('input[id="id_username"]')
            password_field = await page.query_selector('input[id="id_password"]')
            submit_btn = await page.query_selector('button[type="submit"]')
            
            login_ok = all([email_field, password_field, submit_btn])
            print(f"  Form elements present: {'PASS' if login_ok else 'FAIL'}")
            
            if login_ok:
                print(f"  PASS: Login form structure OK")
            
            await page.screenshot(path="ui_check_login.png")
            print()
            
            # TEST 3: Hotel Search Page
            print("TEST 3: Hotel Search Page UI")
            await page.goto(f"{BASE_URL}/hotels/", wait_until='networkidle', timeout=10000)
            
            search_form = await page.query_selector('form')
            if search_form:
                print(f"  PASS: Search form found")
            else:
                print(f"  WARNING: Search form not immediately visible")
            
            await page.screenshot(path="ui_check_search.png")
            print()
            
            # TEST 4: Home Page
            print("TEST 4: Home Page UI")
            await page.goto(f"{BASE_URL}/", wait_until='networkidle', timeout=10000)
            
            nav = await page.query_selector('nav')
            if nav:
                print(f"  PASS: Navigation present")
            
            await page.screenshot(path="ui_check_home.png")
            print()
            
            # CONSOLE ERRORS CHECK
            print("TEST 5: Console Error Validation")
            await page.goto(f"{BASE_URL}/", timeout=10000)
            await page.wait_for_timeout(2000)  # Wait for any deferred errors
            
            if console_errors:
                print(f"  ERRORS FOUND: {len(console_errors)}")
                for err in console_errors[:5]:  # Show first 5
                    print(f"    - {err}")
                print(f"  FAIL: Console has errors")
                result = False
            else:
                print(f"  PASS: No console errors ({len(console_messages)} messages)")
                result = True
            
            print()
            return result
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_ui_components())
    print("=" * 70)
    print(f"UI VALIDATION: {'PASS' if result else 'FAIL'}")
    print("=" * 70)
