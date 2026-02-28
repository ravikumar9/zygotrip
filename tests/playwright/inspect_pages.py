"""
Page Structure Inspector - Inspect actual form elements on signup page
"""
from playwright.sync_api import sync_playwright
import json

def inspect_signup_page():
    """Inspect the signup page structure"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            page.goto("https://127.0.0.1:8000/accounts/signup/", timeout=10000)
            page.wait_for_load_state("networkidle")
            
            # Get form fields
            print("=" * 80)
            print("SIGNUP PAGE STRUCTURE")
            print("=" * 80)
            
            # Check for form tag
            if page.locator("form").first.is_visible():
                print("✅ Form found")
                
                # Get all input fields
                inputs = page.locator("input").all()
                print(f"\nTotal input fields: {len(inputs)}")
                for idx, inp in enumerate(inputs[:15]):  # First 15
                    try:
                        name = inp.get_attribute("name")
                        type_ = inp.get_attribute("type")
                        placeholder = inp.get_attribute("placeholder")
                        print(f"  {idx+1}. name='{name}' | type='{type_}' | placeholder='{placeholder}'")
                    except:
                        pass
                
                # Get all select fields
                selects = page.locator("select").all()
                print(f"\nTotal select fields: {len(selects)}")
                for idx, sel in enumerate(selects):
                    try:
                        name = sel.get_attribute("name")
                        print(f"  {idx+1}. name='{name}'")
                        # Get options
                        options = sel.locator("option").all()
                        for opt in options[:5]:
                            value = opt.get_attribute("value")
                            text = opt.text_content()
                            print(f"      - value='{value}' | text='{text}'")
                    except:
                        pass
                
                # Get all buttons
                buttons = page.locator("button").all()
                print(f"\nTotal button fields: {len(buttons)}")
                for idx, btn in enumerate(buttons[:5]):
                    try:
                        text = btn.text_content().strip()
                        type_ = btn.get_attribute("type")
                        print(f"  {idx+1}. type='{type_}' | text='{text}'")
                    except:
                        pass
                
                # Check for error messages area
                if page.locator(".error, .alert-danger, .form-error").first.is_visible():
                    print("\n✅ Error message area found: .error or .alert-danger or .form-error")
            
            # Check login page for comparison
            print("\n" + "=" * 80)
            print("LOGIN PAGE STRUCTURE")
            print("=" * 80)
            
            page.goto("https://127.0.0.1:8000/accounts/login/", timeout=10000)
            page.wait_for_load_state("networkidle")
            
            if page.locator("form").first.is_visible():
                print("✅ Form found")
                inputs = page.locator("input").all()
                print(f"\nTotal input fields: {len(inputs)}")
                for idx, inp in enumerate(inputs[:10]):
                    try:
                        name = inp.get_attribute("name")
                        type_ = inp.get_attribute("type")
                        print(f"  {idx+1}. name='{name}' | type='{type_}'")
                    except:
                        pass
            
            # Check homepage
            print("\n" + "=" * 80)
            print("HOME PAGE / LANDING")
            print("=" * 80)
            
            page.goto("https://127.0.0.1:8000/", timeout=10000)
            
            # Look for signup/login buttons
            nav_buttons = page.locator("a[href*='signup'], a[href*='login'], button:has-text('Sign'), button:has-text('Login')").all()
            print(f"\nNavigation buttons found: {len(nav_buttons)}")
            for btn in nav_buttons[:5]:
                text = btn.text_content().strip()
                href = btn.get_attribute("href")
                print(f"  - href='{href}' | text='{text}'")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    inspect_signup_page()
