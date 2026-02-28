"""Diagnostic test to check registration pages"""
import pytest
from playwright.sync_api import Page
import uuid

BASE_URL = "https://127.0.0.1:8000"
RUN_ID = uuid.uuid4().hex[:8]

class TestRegistrationDiagnostic:
    """Diagnostic tests for registration pages"""
    
    def test_property_owner_registration_page_loads(self, page: Page):
        """Check if property owner registration page loads"""
        page.goto(f"{BASE_URL}/register/property-owner/")
        page.wait_for_load_state("networkidle")
        
        # Take screenshot to see page
        page.screenshot(path="screenshots/diag_owner_reg_page.png")
        
        # Check what's on the page
        print(f"\n{'='*60}")
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")
        
        # Look for form or input fields
        forms = page.locator("form").count()
        inputs = page.locator("input").count()
        
        print(f"Forms on page: {forms}")
        print(f"Input fields: {inputs}")
        
        # Try to find fields
        email_fields = page.locator('input[type="email"], input[name="email"], input[name="username"]').count()
        password_fields = page.locator('input[type="password"]').count()
        
        print(f"Email-like fields: {email_fields}")
        print(f"Password fields: {password_fields}")
        
        # Check HTML content
        html_content = page.content()
        print(f"\nHTML length: {len(html_content)}")
        print(f"Contains 'form': {'<form' in html_content}")
        print(f"Contains 'input': {'<input' in html_content}")
        print(f"Contains 'register': {'register' in html_content.lower()}")
        
        # Try to find any submit button
        buttons = page.locator("button").count()
        print(f"Buttons: {buttons}")
        
        # Look for headings
        headings = page.locator("h1, h2, h3").count()
        print(f"Headings: {headings}")
        if headings > 0:
            h1_text = page.locator("h1").first.text_content() if page.locator("h1").count() > 0 else "N/A"
            print(f"H1 text: {h1_text}")
        
        # Look for div with specific classes
        divs = page.locator("div[class*='form'], div[class*='register']").count()
        print(f"Form-like divs: {divs}")
        
        print(f"{'='*60}\n")
        
        assert page.url == f"{BASE_URL}/register/property-owner/"
    
    def test_traveler_registration_page_loads(self, page: Page):
        """Check if traveler registration page loads"""
        page.goto(f"{BASE_URL}/register/traveler/")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path="screenshots/diag_traveler_reg_page.png")
        
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")
        
        forms = page.locator("form").count()
        inputs = page.locator("input").count()
        
        print(f"Forms: {forms}, Inputs: {inputs}")
        
        assert page.url == f"{BASE_URL}/register/traveler/"
    
    def test_hotel_listing_page_loads(self, page: Page):
        """Check if hotel listing page loads"""
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin=2025-05-15&checkout=2025-05-17")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path="screenshots/diag_hotel_listing.png")
        
        print(f"URL: {page.url}")
        
        hotels = page.locator("[data-hotel-card], .hotel-card, .property-card").count()
        print(f"Hotels found: {hotels}")
        
        assert page.url.startswith(f"{BASE_URL}/hotels/hotel-listing/")
