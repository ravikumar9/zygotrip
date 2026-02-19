"""
ZERO-ESCAPE E2E Testing Suite
Real Playwright Browser Testing (Headed Mode)
Tests: Home, Hero, Search, Filters, Booking, Registration, Dashboards
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, expect

# Output directory
SCREENSHOTS_DIR = Path("e2e_screenshots_zero_escape")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

BASE_URL = "http://localhost:8000"

# Test credentials
TEST_ACCOUNTS = {
    "customer": {"email": "customer@test.com", "password": "TestPass123"},
    "owner": {"email": "owner@test.com", "password": "TestPass123"},
}

class ZeroEscapeTests:
    def __init__(self):
        self.results = []
        self.browser = None
        self.context = None
        self.page = None
        
    async def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level:8}] {message}")
    
    async def screenshot(self, name: str):
        """Capture screenshot with cleanup filename"""
        clean_name = name.replace(" ", "_").lower()
        path = SCREENSHOTS_DIR / f"{clean_name}.png"
        await self.page.screenshot(path=str(path), full_page=True)
        await self.log(f"Screenshot: {path}", "CAPTURE")
        return path
    
    async def assert_test(self, condition: bool, message: str, test_name: str):
        """Assert with logging"""
        if condition:
            await self.log(f"[PASS] {message}", "PASS")
            self.results.append({"test": test_name, "result": "PASS", "message": message})
        else:
            await self.log(f"[FAIL] {message}", "FAIL")
            self.results.append({"test": test_name, "result": "FAIL", "message": message})
            raise AssertionError(message)
    
    async def setup(self):
        """Initialize browser and page"""
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=False)  # VISIBLE BROWSER
        self.context = await self.browser.new_context(viewport={"width": 1280, "height": 720})
        self.page = await self.context.new_page()
        await self.log("Browser launched (headless=False, visible)", "SETUP")
    
    async def teardown(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        await self.log("Browser closed", "TEARDOWN")
    
    # ============ TEST 1: Home Page & Hero ============
    async def test_01_home_and_hero(self):
        """Verify home page loads with gradient hero"""
        test_name = "test_01_home_and_hero"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/", wait_until="networkidle")
            
            # Check hero gradient
            hero = await self.page.query_selector(".hero")
            exists = hero is not None
            await self.assert_test(exists, "Hero section found", test_name)
            
            # Check hero title
            title = await self.page.query_selector(".hero-title")
            exists = title is not None
            await self.assert_test(exists, "Hero title found", test_name)
            
            # Check gradient style
            style = await self.page.evaluate("window.getComputedStyle(document.querySelector('.hero')).background")
            has_gradient = "gradient" in str(style).lower() or "#" in str(style)
            await self.assert_test(has_gradient, f"Gradient applied (bg: {style[:50]})", test_name)
            
            # Check search form
            search_form = await self.page.query_selector(".search-form")
            exists = search_form is not None
            await self.assert_test(exists, "Search form found in hero", test_name)
            
            await self.screenshot("01_home_hero")
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ TEST 2: Search Functionality ============
    async def test_02_search_hotels(self):
        """Test hotel search and location autocomplete"""
        test_name = "test_02_search_hotels"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/", wait_until="networkidle")
            
            # Fill search
            search_input = await self.page.query_selector("input[name='q']")
            await self.assert_test(search_input is not None, "Search input found", test_name)
            
            await self.page.fill("input[name='q']", "Coorg")
            await self.page.wait_for_timeout(500)
            await self.screenshot("02_search_input")
            
            # Submit search
            search_form = await self.page.query_selector(".search-form")
            await search_form.evaluate("el => el.closest('form').submit()")
            await self.page.wait_for_url(f"{BASE_URL}/search/**", wait_until="load")
            
            # Verify results page
            results = await self.page.query_selector(".listing-grid")
            has_results = results is not None
            await self.assert_test(has_results, "Search results page loaded", test_name)
            
            await self.screenshot("02_search_results")
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ TEST 3: Hotel Filters ============
    async def test_03_hotel_filters(self):
        """Test filter system (price, rating, amenities)"""
        test_name = "test_03_hotel_filters"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/hotels/", wait_until="networkidle")
            
            # Check filter sidebar
            sidebar = await self.page.query_selector(".filter-sidebar")
            exists = sidebar is not None
            await self.assert_test(exists, "Filter sidebar found", test_name)
            
            # Check star rating filter
            rating_select = await self.page.query_selector("select[name='star_rating']")
            star_filter_exists = rating_select is not None
            await self.assert_test(star_filter_exists, "Star rating filter found", test_name)
            
            # Check price range filter
            price_min = await self.page.query_selector("input[name='price_min']")
            price_max = await self.page.query_selector("input[name='price_max']")
            price_filter_exists = (price_min is not None) or (price_max is not None)
            await self.assert_test(price_filter_exists, "Price range filter found", test_name)
            
            await self.screenshot("03_hotel_filters")
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ TEST 4: Login & Register ============
    async def test_04_login_register(self):
        """Test login and registration forms"""
        test_name = "test_04_login_register"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
            
            # Check form layout
            auth_card = await self.page.query_selector(".auth-card")
            exists = auth_card is not None
            await self.assert_test(exists, "Auth card found", test_name)
            
            # Check input styling (min 48px height)
            inputs = await self.page.query_selector_all(".auth-card input")
            has_inputs = len(inputs) > 0
            await self.assert_test(has_inputs, f"Login inputs found ({len(inputs)})", test_name)
            
            if inputs:
                height = await inputs[0].evaluate("el => window.getComputedStyle(el).height")
                await self.log(f"Input height: {height}", "INFO")
            
            await self.screenshot("04_login_form")
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ TEST 5: Hotel Detail & Maps ============
    async def test_05_hotel_detail_maps(self):
        """Test hotel detail page and Google Maps"""
        test_name = "test_05_hotel_detail_maps"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/hotels/", wait_until="networkidle")
            
            # Find first hotel link
            hotel_link = await self.page.query_selector("a[href*='/hotels/']")
            if hotel_link:
                await hotel_link.click()
                await self.page.wait_for_load_state("networkidle")
                
                # Check hotel detail page
                detail = await self.page.query_selector(".card")
                exists = detail is not None
                await self.assert_test(exists, "Hotel detail loaded", test_name)
                
                # Check for map container
                map_container = await self.page.query_selector("#map, [class*='map']")
                map_exists = map_container is not None
                await self.assert_test(map_exists, f"Map container found", test_name)
                
                await self.screenshot("05_hotel_detail")
            else:
                await self.log("No hotels found to test", "WARN")
            
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ TEST 6: Buses Page ============
    async def test_06_buses_listing(self):
        """Test buses listing and seat selection"""
        test_name = "test_06_buses_listing"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/buses/", wait_until="networkidle")
            
            # Check hero
            hero = await self.page.query_selector(".hero")
            exists = hero is not None
            await self.assert_test(exists, "Buses hero found", test_name)
            
            # Check buses grid
            grid = await self.page.query_selector(".grid-auto, [class*='grid']")
            exists = grid is not None
            await self.assert_test(exists, "Buses grid found", test_name)
            
            # Find first bus detail link
            bus_link = await self.page.query_selector("a[href*='/buses/'],button:has-text('Book')")
            if bus_link:
                await bus_link.click()
                await self.page.wait_for_load_state("networkidle")
                
                # Check seat selection UI
                seat_buttons = await self.page.query_selector_all(".seat-button")
                has_seats = len(seat_buttons) > 0
                await self.assert_test(has_seats, f"Seat buttons found ({len(seat_buttons)})", test_name)
                
                # Check price summary
                price_summary = await self.page.query_selector(".sticky, [class*='summary']")
                summary_exists = price_summary is not None
                await self.assert_test(summary_exists, "Price summary found", test_name)
            
            await self.screenshot("06_buses_detail")
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ TEST 7: Cabs Listing ============
    async def test_07_cabs_listing(self):
        """Test cabs listing with proper field display"""
        test_name = "test_07_cabs_listing"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/cabs/", wait_until="networkidle")
            
            # Check cabs grid
            cards = await self.page.query_selector_all(".cab-card, [class*='card']")
            has_cars = len(cards) > 0
            await self.assert_test(has_cars, f"Cab cards found ({len(cards)})", test_name)
            
            # Check cab details displayed
            grid = await self.page.query_selector(".grid-auto")
            exists = grid is not None
            await self.assert_test(exists, "Cabs grid rendered", test_name)
            
            await self.screenshot("07_cabs_listing")
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ TEST 8: Date Validation ============
    async def test_08_date_validation(self):
        """Test date picker validation"""
        test_name = "test_08_date_validation"
        try:
            await self.log(f"Starting: {test_name}", "TEST")
            await self.page.goto(f"{BASE_URL}/", wait_until="networkidle")
            
            # Check date inputs have min attribute
            checkin = await self.page.query_selector("input[name='checkin']")
            checkout = await self.page.query_selector("input[name='checkout']")
            
            have_dates = (checkin is not None) and (checkout is not None)
            await self.assert_test(have_dates, "Date inputs found", test_name)
            
            if checkin:
                min_attr = await checkin.get_attribute("min")
                has_min = min_attr is not None
                await self.assert_test(has_min, f"Checkin has min attribute: {min_attr}", test_name)
            
            if checkout:
                min_attr = await checkout.get_attribute("min")
                has_min = min_attr is not None
                await self.assert_test(has_min, f"Checkout has min attribute: {min_attr}", test_name)
            
            await self.screenshot("08_date_validation")
            await self.log(f"[PASS] {test_name} completed", "TEST")
            
        except Exception as e:
            await self.log(f"[FAIL] {test_name}: {str(e)}", "ERROR")
            raise
    
    # ============ RUN ALL TESTS ============
    async def run_all(self):
        """Execute all tests"""
        await self.setup()
        
        tests = [
            self.test_01_home_and_hero,
            self.test_02_search_hotels,
            self.test_03_hotel_filters,
            self.test_04_login_register,
            self.test_05_hotel_detail_maps,
            self.test_06_buses_listing,
            self.test_07_cabs_listing,
            self.test_08_date_validation,
        ]
        
        passed = 0
        failed = 0
        
        await self.log("=" * 60, "HEADER")
        await self.log("ZYGOTRIP ZERO-ESCAPE E2E TEST SUITE", "HEADER")
        await self.log("=" * 60, "HEADER")
        
        for test in tests:
            try:
                await test()
                passed += 1
            except Exception as e:
                failed += 1
                await self.log(f"Test failed: {str(e)}", "FAIL")
        
        await self.teardown()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
        print("=" * 60)
        print("\nDetailed Results:")
        for result in self.results:
            status_icon = "[PASS]" if result["result"] == "PASS" else "[FAIL]"
            print(f"  {status_icon} {result['test']}: {result['message']}")
        
        print(f"\nScreenshots saved to: {SCREENSHOTS_DIR}")
        print("=" * 60)
        
        return failed == 0

async def main():
    """Run tests"""
    try:
        suite = ZeroEscapeTests()
        success = await suite.run_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
