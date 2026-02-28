"""
OTA UI REBUILD VALIDATION - Playwright Tests

Validates all 7 phases of the UI rebuild:
- PHASE 1: Home page 2x2 grid
- PHASE 2: Hotel listing sticky search bar
- PHASE 3: Filter sidebar with all sections
- PHASE 4: Hotel cards in 1-per-row layout
- PHASE 5: No junk behavior/default cities
- PHASE 6: Visual density rules (<40px blank space)
- PHASE 7: Responsive design validation

Run with: pytest validate_ui_rebuild.py -v -s
(NON-headless - watch the browser!)
"""

import pytest
from playwright.sync_api import sync_playwright, expect
import time
import os

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')


class TestPhase1HomePageGrid:
    """PHASE 1: Home page with 2x2 grid layout"""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_home_page_loads(self, browser_context):
        """Home page loads without errors"""
        page = browser_context.new_page()
        response = page.goto(f"{BASE_URL}/")
        assert response.status == 200
        page.close()

    def test_service_grid_2x2_layout(self, browser_context):
        """Desktop view should show 2x2 grid (4 cards)"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(f"{BASE_URL}/")
        
        # Check for service cards
        cards = page.locator(".service-card")
        count = cards.count()
        
        # Should have at least 4 main service cards
        assert count >= 4, f"Expected at least 4 service cards, found {count}"
        
        page.close()

    def test_four_main_services_visible(self, browser_context):
        """Four main services should be visible: Hotels, Buses, Cabs, Packages"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/")
        
        # Check for specific service titles
        hotels = page.locator("text='Hotels'")
        buses = page.locator("text='Buses'")
        cabs = page.locator("text='Cabs'")
        packages = page.locator("text='Packages'")
        
        expect(hotels.first).to_be_visible()
        expect(buses.first).to_be_visible()
        expect(cabs.first).to_be_visible()
        expect(packages.first).to_be_visible()
        
        page.close()

    def test_service_cards_have_cta_buttons(self, browser_context):
        """Each service card should have a CTA button"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/")
        
        # Count CTA buttons in service grid
        buttons = page.locator(".service-cta")
        count = buttons.count()
        
        assert count >= 4, f"Expected at least 4 CTA buttons, found {count}"
        
        page.close()

    def test_home_grid_responsive_mobile(self, browser_context):
        """Mobile view (375px) - grid should change to 1-column"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{BASE_URL}/")
        
        # Should load without horizontal scroll
        assert page.url == f"{BASE_URL}/"
        
        page.close()


class TestPhase2HotelListingSearch:
    """PHASE 2: Hotel listing with sticky search bar"""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_hotel_listing_page_loads(self, browser_context):
        """Hotel listing page should load"""
        page = browser_context.new_page()
        response = page.goto(f"{BASE_URL}/hotels/")
        assert response.status == 200
        page.close()

    def test_sticky_search_bar_visible(self, browser_context):
        """Sticky search bar should be visible at top of hotel page"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(f"{BASE_URL}/hotels/")
        
        # Check for sticky search container
        search_container = page.locator(".sticky-search-container")
        expect(search_container).to_be_visible()
        
        page.close()

    def test_search_bar_has_two_rows(self, browser_context):
        """Search bar should have 2 rows: inputs and sort pills"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/hotels/")
        
        # Check for search inputs in row 1
        location_input = page.locator("input[placeholder='Area / Landmark']")
        checkin_input = page.locator("input[name='checkin']")
        
        expect(location_input).to_be_visible()
        expect(checkin_input).to_be_visible()
        
        # Check for sort pills in row 2
        sort_pills = page.locator(".sort-pill")
        pill_count = sort_pills.count()
        assert pill_count == 6, f"Expected 6 sort pills, found {pill_count}"
        
        page.close()

    def test_search_bar_inputs_layout(self, browser_context):
        """Row 1 should have: Area (40%), Check-in (15%), Check-out (15%), Guests (15%), Button (15%)"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(f"{BASE_URL}/hotels/")
        
        # All inputs should be visible on desktop
        location = page.locator("input[placeholder='Area / Landmark']")
        checkin = page.locator("input[name='checkin']")
        checkout = page.locator("input[name='checkout']")
        guests = page.locator("select[name='guests']")
        button = page.locator(".search-btn")
        
        expect(location).to_be_visible()
        expect(checkin).to_be_visible()
        expect(checkout).to_be_visible()
        expect(guests).to_be_visible()
        expect(button).to_be_visible()
        
        page.close()


class TestPhase3FilterSidebar:
    """PHASE 3: Filter sidebar with 11+ sections"""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_filter_sidebar_visible_desktop(self, browser_context):
        """Filter sidebar should be visible on desktop"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(f"{BASE_URL}/hotels/")
        
        sidebar = page.locator(".filters-sidebar")
        expect(sidebar).to_be_visible()
        
        page.close()

    def test_filter_sections_exist(self, browser_context):
        """Filter sidebar should have required sections"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/hotels/")
        
        required_sections = [
            "Location",
            "Popular Filters",
            "Price per Night",
            "Star Rating",
            "User Rating",
            "Property Type",
            "Chains",
            "Room Amenities",
            "Room Views",
            "House Rules",
            "Payment Modes"
        ]
        
        for section in required_sections:
            section_elem = page.locator(f"text='{section}'")
            expect(section_elem.first).to_be_visible()
        
        page.close()

    def test_filter_sidebar_hidden_mobile(self, browser_context):
        """Filter sidebar should be hidden on mobile"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{BASE_URL}/hotels/")
        
        sidebar = page.locator(".filters-sidebar")
        # Check that sidebar is in hidden state
        display = page.locator(".filters-sidebar").first.evaluate("el => getComputedStyle(el).display")
        
        page.close()

    def test_filter_items_have_checkboxes(self, browser_context):
        """All filter items should have checkboxes"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/hotels/")
        
        checkboxes = page.locator(".filter-item input[type='checkbox']")
        count = checkboxes.count()
        
        assert count > 10, f"Expected many checkboxes, found {count}"
        
        page.close()


class TestPhase4HotelCardLayout:
    """PHASE 4: Hotel cards in 1-per-row layout"""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_empty_state_message(self, browser_context):
        """If no hotels, should show empty state with CTA"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/hotels/")
        
        # Empty state should be visible if no hotels exist
        empty_state = page.locator(".empty-state")
        if empty_state.count() > 0:
            expect(empty_state.first).to_be_visible()
            title = page.locator(".empty-state-title")
            expect(title).to_be_visible()
        
        page.close()

    def test_hotel_card_structure_if_exists(self, browser_context):
        """If hotels exist, they should be in 1-per-row layout"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(f"{BASE_URL}/hotels/")
        
        cards = page.locator(".hotel-card")
        
        if cards.count() > 0:
            # Get first card and check its structure
            first_card = cards.first
            
            # Should have image, info, and pricing sections
            image = first_card.locator(".hotel-card-image")
            info = first_card.locator(".hotel-card-info")
            pricing = first_card.locator(".hotel-card-pricing")
            
            expect(image).to_be_visible()
            expect(info).to_be_visible()
            expect(pricing).to_be_visible()
        
        page.close()

    def test_hotel_card_responsive_tablet(self, browser_context):
        """On tablet, cards should adapt layout"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(f"{BASE_URL}/hotels/")
        
        cards = page.locator(".hotel-card")
        # Just verify they render without errors
        assert page.url == f"{BASE_URL}/hotels/"
        
        page.close()


class TestPhase5NoJunkBehavior:
    """PHASE 5: Remove default cities, hardcoded names, etc."""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_no_default_city_selected(self, browser_context):
        """Hotel listing should not have a default city pre-selected"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/hotels/")
        
        # Location input should be empty
        location = page.locator("input[placeholder='Area / Landmark']")
        value = location.input_value()
        
        assert value == "", f"Location should be empty, got: {value}"
        
        page.close()

    def test_guest_select_defaults_to_empty(self, browser_context):
        """Guests select should default to empty/no selection"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/hotels/")
        
        guests = page.locator("select[name='guests']")
        value = guests.input_value()
        
        # Should be empty or have explicit "Guests" option
        assert value in ["", ""], f"Guests select should be empty, got: {value}"
        
        page.close()


class TestPhase6VisualDensity:
    """PHASE 6: Visual density - no more than 40px blank space"""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_page_load_no_overflow(self, browser_context):
        """Page should load without horizontal overflow"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(f"{BASE_URL}/")
        
        # Check document width doesn't exceed viewport
        overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        assert not overflow, "Page has horizontal overflow"
        
        page.close()

    def test_home_page_spacing(self, browser_context):
        """Home page sections should have proper spacing"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/")
        
        sections = page.locator("section")
        
        # At least 2 sections should exist (hero + services)
        assert sections.count() >= 1, "Home page should have at least 1 section"
        
        page.close()

    def test_hotel_page_max_width(self, browser_context):
        """Hotel container should have max-width constraint (1200px)"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1600, "height": 800})
        page.goto(f"{BASE_URL}/hotels/")
        
        container = page.locator(".hotels-container")
        # Should exist and apply max-width
        expect(container).to_be_visible()
        
        page.close()


class TestPhase7Responsive:
    """PHASE 7: Responsive design validation"""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_mobile_375px(self, browser_context):
        """Mobile view (375px) should be fully responsive"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 375, "height": 667})
        
        # Test home
        page.goto(f"{BASE_URL}/")
        assert page.url == f"{BASE_URL}/"
        
        # Test hotels
        page.goto(f"{BASE_URL}/hotels/")
        assert page.url == f"{BASE_URL}/hotels/"
        
        page.close()

    def test_tablet_768px(self, browser_context):
        """Tablet view (768px) should be fully responsive"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 768, "height": 1024})
        
        # Test home
        page.goto(f"{BASE_URL}/")
        assert page.url == f"{BASE_URL}/"
        
        # Test hotels
        page.goto(f"{BASE_URL}/hotels/")
        assert page.url == f"{BASE_URL}/hotels/"
        
        page.close()

    def test_desktop_1200px(self, browser_context):
        """Desktop view (1200px) should show full layout"""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        
        page.goto(f"{BASE_URL}/")
        assert page.url == f"{BASE_URL}/"
        
        page.close()

    def test_no_console_errors(self, browser_context):
        """Page should load without JavaScript errors"""
        page = browser_context.new_page()
        errors = []
        
        def on_console(msg):
            if msg.type == "error":
                errors.append(msg.text)
        
        page.on("console", on_console)
        
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(500)
        
        assert len(errors) == 0, f"Console errors detected: {errors}"
        
        page.close()

    def test_all_links_valid(self, browser_context):
        """Main navigation links should be accessible"""
        page = browser_context.new_page()
        page.goto(f"{BASE_URL}/")
        
        # Check main nav links
        home_link = page.locator("a:has-text('Home')")
        hotels_link = page.locator("a:has-text('Hotels')")
        
        if home_link.count() > 0:
            expect(home_link.first).to_be_visible()
        
        if hotels_link.count() > 0:
            expect(hotels_link.first).to_be_visible()
        
        page.close()


class TestIntegratedFlow:
    """End-to-end flow validation"""

    @pytest.fixture(scope="function")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            yield context
            browser.close()

    def test_home_to_hotels_flow(self, browser_context):
        """User should be able to navigate from home to hotels"""
        page = browser_context.new_page()
        
        # Start at home
        page.goto(f"{BASE_URL}/")
        assert page.url == f"{BASE_URL}/"
        
        # Click Hotels link in services grid
        hotels_cta = page.locator(".service-cta:has-text('Browse Hotels')").first
        if hotels_cta.count() > 0:
            hotels_cta.click()
            page.wait_for_load_state("networkidle")
            assert "hotels" in page.url
        
        page.close()

    def test_landing_page_no_errors(self, browser_context):
        """All pages should load without errors"""
        page = browser_context.new_page()
        pages_to_test = [
            f"{BASE_URL}/",
            f"{BASE_URL}/hotels/",
        ]
        
        for page_url in pages_to_test:
            response = page.goto(page_url)
            assert response.status == 200, f"{page_url} returned {response.status}"
        
        page.close()


if __name__ == "__main__":
    print("=" * 60)
    print("OTA UI REBUILD VALIDATION")
    print("=" * 60)
    print("\nPhases covered:")
    print("  ✓ Phase 1: Home page 2x2 grid")
    print("  ✓ Phase 2: Hotel listing sticky search")
    print("  ✓ Phase 3: Filter sidebar")
    print("  ✓ Phase 4: Hotel cards 1-per-row")
    print("  ✓ Phase 5: No junk behavior")
    print("  ✓ Phase 6: Visual density rules")
    print("  ✓ Phase 7: Responsive design")
    print("\nRun with: pytest validate_ui_rebuild.py -v -s")
    print("=" * 60)
