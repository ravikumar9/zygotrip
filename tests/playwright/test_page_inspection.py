"""Detailed HTML inspection test"""
import pytest
from playwright.sync_api import Page

BASE_URL = "https://127.0.0.1:8000"

class TestPageInspection:
    """Detailed page content inspection"""
    
    def test_inspect_registration_html(self, page: Page):
        """Inspect the complete HTML of registration page"""
        page.goto(f"{BASE_URL}/register/property-owner/")
        page.wait_for_load_state("networkidle")
        
        # Get full HTML
        html = page.content()
        
        # Write to file for inspection
        with open("registration_page_html.txt", "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"\n{'='*80}")
        print(f"HTML saved to registration_page_html.txt")
        print(f"HTML length: {len(html)}")
        print(f"{'='*80}\n")
        
        # Print key parts
        if "error" in html.lower():
            print("ERROR DETECTED IN PAGE")
            # Extract error message
            error_start = html.lower().find("something went wrong")
            if error_start >= 0:
                print(f"Found error at position {error_start}")
        
        # Print first 2000 chars
        print("FIRST 2000 CHARS OF HTML:")
        print(html[:2000])
        print("\n\n")
        
        print("LAST 2000 CHARS OF HTML:")
        print(html[-2000:])
    
    def test_login_page_works(self, page: Page):
        """Check if login page works"""
        page.goto(f"{BASE_URL}/login/")
        page.wait_for_load_state("networkidle")
        
        forms = page.locator("form").count()
        inputs = page.locator("input").count()
        
        print(f"\nLOGIN PAGE:")
        print(f"Forms: {forms}, Inputs: {inputs}, URL: {page.url}")
        
        # Should have form and inputs
        assert forms > 0 or inputs > 0, "Login page should have form"
    
    def test_home_page_loads(self, page: Page):
        """Check if home page loads"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path="screenshots/home_page.png")
        
        print(f"\nHOME PAGE:")
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")
        
        assert page.url == BASE_URL
