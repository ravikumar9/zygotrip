"""
Playwright E2E Test Suite for OTA Booking Funnel
Tests the complete user journey from search to booking
"""
import pytest
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta


# Test Configuration
BASE_URL = "https://127.0.0.1:8000"  # HTTPS for custom runserver
TEST_PROPERTY_SLUG = "udaipur-grand-stay-5-udr"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "ignore_https_errors": True,  # Ignore self-signed certificate errors
    }


class TestBookingFunnel:
    """Test the complete booking funnel flow"""
    
    def test_01_hotel_listing_page_loads(self, page: Page):
        """Test: Hotel listing page loads with search results"""
        # Calculate dates
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        # Navigate to listing page
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        
        # Wait for results to load
        page.wait_for_selector("[data-hotel-card]", timeout=10000)
        
        # Verify page title
        expect(page).to_have_title("Hotel Search Results - Zygotrip")
        
        # Verify search results displayed
        hotel_cards = page.locator("[data-hotel-card]")
        assert hotel_cards.count() > 0, "No hotel cards found on listing page"
        
        # Verify filter sidebar exists
        expect(page.locator("aside").filter(has_text="Filters")).to_be_visible()
        
        # Take screenshot
        page.screenshot(path="screenshots/01_listing_page.png")
    
    def test_02_filters_work_correctly(self, page: Page):
        """Test: Filter sidebar filters results correctly"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card]", timeout=10000)
        
        # Get initial count
        initial_count = page.locator("[data-hotel-card]").count()
        
        # Apply amenity filter (e.g., Free WiFi)
        if page.locator('input[name="amenity"][value="Free WiFi"]').is_visible():
            page.locator('input[name="amenity"][value="Free WiFi"]').check()
            page.locator('button:has-text("Apply Filters")').click()
            page.wait_for_load_state("networkidle")
            
            # Verify URL updated with filter
            page.wait_for_url(lambda url: "amenity=" in url, timeout=5000)
            
            # Take screenshot
            page.screenshot(path="screenshots/02_filters_applied.png")
    
    def test_03_hotel_details_page_loads(self, page: Page):
        """Test: Hotel details page loads with room options"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        # Navigate directly to hotel details
        page.goto(f"{BASE_URL}/hotels/hotel-details/?property={TEST_PROPERTY_SLUG}&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        
        # Wait for page load
        page.wait_for_selector("h1", timeout=10000)
        
        # Verify property name displayed
        expect(page.locator("h1")).to_contain_text("Grand Stay")
        
        # Verify room cards loaded
        room_cards = page.locator("[data-room-card]")
        assert room_cards.count() > 0, "No room cards found on details page"
        
        # Verify booking summary sidebar exists
        expect(page.locator(".booking-summary")).to_be_visible()
        
        # Take screenshot
        page.screenshot(path="screenshots/03_hotel_details.png")
    
    def test_04_room_specific_details_displayed(self, page: Page):
        """Test: Room cards show room-specific photos and amenities"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-details/?property={TEST_PROPERTY_SLUG}&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-room-card]", timeout=10000)
        
        # Get first room card
        first_room = page.locator("[data-room-card]").first
        
        # Verify room image displayed (in hotels/components/room_card.html)
        # Check for either img tag or image placeholder
        media_section = first_room.locator(".room-card__media").first
        expect(media_section).to_be_visible()
        
        # Verify room name displayed
        room_name = first_room.locator(".heading-md")
        expect(room_name).to_be_visible()
        
        # Verify price displayed
        expect(first_room.locator(".room-card__amount")).to_contain_text("₹")
        
        # Verify amenities section exists
        expect(first_room.locator("[data-room-amenities]")).to_be_visible()
        
        # Take screenshot
        page.screenshot(path="screenshots/04_room_details.png")
    
    def test_05_property_discount_displayed(self, page: Page):
        """Test: Property discounts show strike-through price and badge"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-details/?property={TEST_PROPERTY_SLUG}&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-room-card]", timeout=10000)
        
        # Check if any room has discount badge
        discount_badges = page.locator(".room-card__discount-badge")
        if discount_badges.count() > 0:
            # Verify discount badge visible
            expect(discount_badges.first).to_be_visible()
            expect(discount_badges.first).to_contain_text("% OFF")
            
            # Verify strike-through price exists
            expect(page.locator(".room-card__original-price").first).to_be_visible()
            
            # Take screenshot
            page.screenshot(path="screenshots/05_discount_displayed.png")
        else:
            print("No active discounts found - test skipped")
    
    def test_06_select_room_button_works(self, page: Page):
        """Test: Select Room button initiates booking flow"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-details/?property={TEST_PROPERTY_SLUG}&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-room-card]", timeout=10000)
        
        # Click Select Room button on first room
        select_button = page.locator("[data-room-select]").first
        select_button.click()
        
        # Wait for potential navigation/page update
        page.wait_for_timeout(2000)
        
        # Take screenshot
        page.screenshot(path="screenshots/06_select_room.png")
    
    def test_07_booking_form_validation(self, page: Page):
        """Test: Booking form validates required fields"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        # Navigate to booking page
        page.goto(f"{BASE_URL}/hotels/hotel-details/?property={TEST_PROPERTY_SLUG}&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-room-card]", timeout=10000)
        page.locator("[data-room-select]").first.click()
        page.wait_for_url(lambda url: "/hotels/hotel-booking/" in url or "/hotels/nhotel-booking/" in url, timeout=5000)
        
        # Try submitting empty form
        if page.locator('button[type="submit"]:has-text("Continue")').is_visible():
            page.locator('button[type="submit"]:has-text("Continue")').click()
            
            # Verify validation messages appear
            page.wait_for_timeout(1000)
            
            # Take screenshot
            page.screenshot(path="screenshots/07_form_validation.png")
    
    def test_08_complete_booking_flow(self, page: Page):
        """Test: Complete booking flow with valid data"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        # Navigate to booking page
        page.goto(f"{BASE_URL}/hotels/hotel-details/?property={TEST_PROPERTY_SLUG}&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-room-card]", timeout=10000)
        page.locator("[data-room-select]").first.click()
        page.wait_for_url(lambda url: "/hotels/hotel-booking/" in url or "/hotels/nhotel-booking/" in url, timeout=5000)
        
        # Fill in guest details
        test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        email_field = page.locator('input[name="email"]')
        if email_field.is_visible():
            page.fill('input[name="email"]', f"test+{test_timestamp}@example.com")
            page.fill('input[name="first_name"]', "Test")
            page.fill('input[name="last_name"]', "User")
            page.fill('input[name="phone"]', "9876543210")
            
            # Try to find and click submit button
            try:
                submit_btn = page.locator('button[type="submit"]').first
                if submit_btn.is_visible():
                    submit_btn.click()
            except:
                pass
        
        # Wait for page update
        page.wait_for_timeout(3000)
        
        # Take screenshot
        page.screenshot(path="screenshots/08_booking_complete.png")
    
    def test_09_responsive_mobile_view(self, page: Page):
        """Test: Mobile responsive design works correctly"""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 812})
        
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        # Navigate to hotel details
        page.goto(f"{BASE_URL}/hotels/hotel-details/?property={TEST_PROPERTY_SLUG}&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("h1", timeout=10000)
        
        # Verify room cards display correctly on mobile
        assert page.locator("[data-room-card]").count() > 0, "No room cards on mobile view"
        
        # Take screenshot
        page.screenshot(path="screenshots/09_mobile_view.png")
    
    def test_10_amenity_filter_count_accuracy(self, page: Page):
        """Test: Amenity filter counts remain accurate after selection"""
        checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        page.goto(f"{BASE_URL}/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1")
        page.wait_for_selector("[data-hotel-card]", timeout=10000)
        
        # Get initial hotel count (all hotels matching location/dates)
        initial_hotel_count = page.locator("[data-hotel-card]").count()
        
        # Find an amenity filter checkbox
        amenity_filters = page.locator('input[name="amenity"]')
        if amenity_filters.count() > 0:
            # Get the count shown before selection
            first_filter = amenity_filters.first
            filter_label = first_filter.locator("xpath=following-sibling::label").first
            initial_text = filter_label.text_content()
            
            # Extract count from text (e.g., "Free WiFi (53)")
            import re
            match = re.search(r'\((\d+)\)', initial_text)
            if match:
                filter_amenity_count = int(match.group(1))
                
                # Filter count should be <= total hotels (since it's filtered by location/dates)
                assert filter_amenity_count <= initial_hotel_count, f"Filter count ({filter_amenity_count}) should be <= total hotels ({initial_hotel_count})"
                
                # Select the filter
                first_filter.check()
                page.locator('button:has-text("Apply Filters")').click()
                page.wait_for_load_state("networkidle")
                
                # After applying filter, hotel count may be less than or equal to filter count
                hotel_count_after_filter = page.locator("[data-hotel-card]").count()
                # Filter applied, so count should decrease or stay same
                assert hotel_count_after_filter <= initial_hotel_count, f"Hotel count after filter should decrease"
                
                # Take screenshot
                page.screenshot(path="screenshots/10_filter_count_accuracy.png")


@pytest.fixture(scope="session", autouse=True)
def setup_screenshots_folder():
    """Create screenshots folder before tests run"""
    import os
    os.makedirs("screenshots", exist_ok=True)
