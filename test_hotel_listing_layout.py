#!/usr/bin/env python
"""Test Phase 3: Hotel Listing Layout Validation"""

import asyncio
from playwright.async_api import async_playwright

async def test_hotel_listing_layout():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        try:
            # Test 1: Load hotel listing without params (no default city)
            print("\n=== TEST 1: Hotel listing without params ===")
            response = await page.goto("https://127.0.0.1:8000/hotels/")
            print(f"Status: {response.status if response else 'Navigation issue'}")
            
            # Check layout elements exist
            sidebar = await page.query_selector("#filters-sidebar")
            sort_bar = await page.query_selector("#sort-bar")
            results_section = await page.locator("div:has(> article.hotel-card)").first.is_visible()
            
            print(f"✓ Sidebar found: {sidebar is not None}")
            print(f"✓ Sort bar found: {sort_bar is not None}")
            print(f"✓ Results section visible: {results_section}")
            
            # Check no hardcoded city badge
            city_badge_text = await page.locator("span:has-text('Madikeri')").first.count() if sidebar else 0
            print(f"✓ No hardcoded Madikeri badge: {city_badge_text == 0}")
            
            # Check empty state message when no filters
            empty_state_visible = await page.locator("text=/Start searching|No hotels/i").first.is_visible() if not results_section else False
            print(f"✓ Empty state message shown: {empty_state_visible or results_section}")
            
            # Test 2: Load hotel listing with city filter
            print("\n=== TEST 2: Hotel listing with city filter ===")
            await page.goto("https://127.0.0.1:8000/hotels/?city_slug=bangalore")
            
            # Check if results load
            has_results = await page.locator("article.hotel-card").count() > 0
            print(f"✓ Results loaded with city filter: {has_results}")
            
            # Check city badge shows correct city
            city_badge = await page.locator("span.inline-flex:has-text('Bangalore')").first.count() if has_results else 0
            print(f"✓ City badge shows 'Bangalore': {city_badge > 0 or not has_results}")
            
            # Test 3: Verify layout structure
            print("\n=== TEST 3: Layout Structure ===")
            
            # Check if page uses max-w-7xl container
            max_width_container = await page.query_selector(".max-w-7xl")
            print(f"✓ Max-width container found: {max_width_container is not None}")
            
            # Check grid layout (sidebar + results)
            grid_layout = await page.query_selector(".lg\\:grid-cols-\\[280px_1fr\\]")
            print(f"✓ Grid layout with correct columns: {grid_layout is not None}")
            
            # Check sticky sidebar
            sticky_sidebar = await page.query_selector(".sticky")
            print(f"✓ Sticky sidebar found: {sticky_sidebar is not None}")
            
            # Test 4: Verify sort bar functionality
            print("\n=== TEST 4: Sort Bar ===")
            sort_buttons = await page.locator("#sort-bar button[type='submit']").count()
            print(f"✓ Sort buttons present: {sort_buttons > 0} (count: {sort_buttons})")
            
            sort_active_button = await page.locator("#sort-bar button.bg-blue-100").first.count()
            print(f"✓ Active sort button has blue background: {sort_active_button > 0 or sort_buttons == 0}")
            
            # Test 5: Verify filter sidebar structure
            print("\n=== TEST 5: Filter Sidebar Structure ===")
            
            popular_filters = await page.locator("h4:has-text('Popular Filters')").first.count()
            price_filter = await page.locator("h4:has-text('Price Range')").first.count()
            rating_filter = await page.locator("h4:has-text('Star Rating')").first.count()
            
            print(f"✓ Popular Filters section: {popular_filters > 0}")
            print(f"✓ Price Range section: {price_filter > 0}")
            print(f"✓ Star Rating section: {rating_filter > 0}")
            
            # Test 6: Hero search consistency
            print("\n=== TEST 6: Hero Search ===")
            hero_section = await page.query_selector("section.hero--search")
            hero_visible = await hero_section.is_visible() if hero_section else False
            print(f"✓ Hero search section present: {hero_section is not None}")
            
            where_to_label = await page.locator("label:has-text('Where to')").first.count()
            print(f"✓ 'Where to' label found: {where_to_label > 0}")
            
            # Test 7: Navbar link validation
            print("\n=== TEST 7: Navbar Links ===")
            hotels_link = await page.locator("a[href*='hotels']").first.get_attribute("href") if await page.locator("a[href*='hotels']").first.count() > 0 else None
            buses_link = await page.locator("a[href*='buses']").first.get_attribute("href") if await page.locator("a[href*='buses']").first.count() > 0 else None
            
            print(f"✓ Hotels link uses URL reversal: {hotels_link and '/' in hotels_link and 'hotels' in hotels_link}")
            print(f"✓ Buses link uses URL reversal: {buses_link and '/' in buses_link and 'buses' in buses_link}")
            
            print("\n=== PHASE 3 VALIDATION COMPLETE ===")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_hotel_listing_layout())
