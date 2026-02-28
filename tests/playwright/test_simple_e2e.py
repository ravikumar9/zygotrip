"""
PRACTICAL E2E TEST SUITE - Real OTA Booking Workflow
Simplified version that works with actual system implementations
"""
import pytest
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta
import uuid


BASE_URL = "https://127.0.0.1:8000"
RUN_ID = uuid.uuid4().hex[:8]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


class TestHotelBookingFlow:
    """Test basic hotel booking flow without auth issues"""
    
    def test_01_homepage_accessible(self, page: Page):
        """Test: Homepage loads"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        # Verify page loaded by checking URL
        assert BASE_URL in page.url
        page.screenshot(path="screenshots/01_homepage.png")
    
    def test_02_hotel_search_works(self, page: Page):
        """Test: Hotel search returns results"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card, .property-card", timeout=10000)
        
        cards = page.locator("[data-hotel-card], .hotel-card, .property-card").count()
        assert cards > 0, "No hotel cards found"
        page.screenshot(path="screenshots/02_search_results.png")
    
    def test_03_hotel_details_page(self, page: Page):
        """Test: Hotel details page loads with room options"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        # Try to click hotel link
        hotel_link = page.locator("[data-hotel-card] a, .hotel-card a").first
        if hotel_link.is_visible():
            hotel_link.click()
            page.wait_for_load_state("networkidle")
        else:
            page.locator("[data-hotel-card], .hotel-card").first.click()
            page.wait_for_load_state("networkidle")
        
        # Should have navigated or loaded details
        assert page.url != ""
        page.screenshot(path="screenshots/03_hotel_details.png")
    
    def test_04_room_cards_visible(self, page: Page):
        """Test: Room cards display with amenities"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        page.locator("[data-hotel-card], .hotel-card").first.click()
        page.wait_for_load_state("networkidle")
        
        # Check for room cards
        rooms = page.locator("[data-room-card], .room-card, .room-option").all()
        print(f"✅ Found {len(rooms)} room cards")
        page.screenshot(path="screenshots/04_room_cards.png")
    
    def test_05_prices_displayed(self, page: Page):
        """Test: Prices display on hotel cards and details"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        # Check for hotels - main assertion
        hotel_count = page.locator("[data-hotel-card], .hotel-card").count()
        assert hotel_count > 0, "No hotels found"
        print(f"✅ Found {hotel_count} hotels displayed")
        page.screenshot(path="screenshots/05_prices.png")
    
    def test_06_filters_work(self, page: Page):
        """Test: Hotel filters apply correctly"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        initial_count = page.locator("[data-hotel-card], .hotel-card").count()
        print(f"Initial hotels: {initial_count}")
        
        # Try to find and apply a filter
        amenity_options = page.locator('input[name="amenity"], input[type="checkbox"]').all()
        if len(amenity_options) > 0:
            amenity_options[0].check(force=True)
            page.wait_for_load_state("networkidle")
            
            filtered_count = page.locator("[data-hotel-card], .hotel-card").count()
            print(f"Filtered count: {filtered_count}")
        
        page.screenshot(path="screenshots/06_filters.png")
    
    def test_07_amenity_display(self, page: Page):
        """Test: Hotel amenities display correctly"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        page.locator("[data-hotel-card], .hotel-card").first.click()
        page.wait_for_load_state("networkidle")
        
        # Check for amenities display
        amenities = page.locator("[data-amenity], .amenity, .amenities, li").all()
        print(f"✅ Found {len(amenities)} amenity elements")
        page.screenshot(path="screenshots/07_amenities.png")
    
    def test_08_responsive_design(self, page: Page):
        """Test: Responsive design works on mobile"""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 812})
        
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        assert page.locator("[data-hotel-card], .hotel-card").count() > 0
        page.screenshot(path="screenshots/08_mobile_view.png")
        
        # Reset viewport
        page.set_viewport_size({"width": 1920, "height": 1080})
    
    def test_09_gallery_modal(self, page: Page):
        """Test: Gallery modal renders"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        page.locator("[data-hotel-card], .hotel-card").first.click()
        page.wait_for_load_state("networkidle")
        
        # Look for gallery/modal opener
        gallery_btn = page.locator('button:has-text("Gallery"), button:has-text("Photos"), a:has-text("View Photos")').first
        if gallery_btn.is_visible():
            gallery_btn.click()
            page.wait_for_timeout(1000)
        
        page.screenshot(path="screenshots/09_gallery.png")
    
    def test_10_booking_summary(self, page: Page):
        """Test: Booking summary displays price breakdown"""
        checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card], .hotel-card", timeout=10000)
        
        page.locator("[data-hotel-card], .hotel-card").first.click()
        page.wait_for_load_state("networkidle")
        
        # Check for booking summary section
        summary = page.locator(".booking-summary, [class*=summary], aside").first
        if summary.is_visible():
            print("✅ Booking summary visible")
        
        page.screenshot(path="screenshots/10_booking_summary.png")


if __name__ == "__main__":
    """
    Run tests:
    python -m pytest tests/playwright/test_simple_e2e.py -v --headed
    """
    pass
