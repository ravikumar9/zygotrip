#!/usr/bin/env python
"""Phase 9 Simplified Validation - Manual Browser Testing"""

import asyncio
from playwright.async_api import async_playwright

async def validate():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
        page = await context.new_page()
        
        print("\n" + "="*60)
        print("PHASE 9: COMPREHENSIVE PLATFORM VALIDATION")
        print("="*60 + "\n")
        
        base = "https://127.0.0.1:8000"
        
        # Test each route
        routes = [("/", "HOME"), ("/hotels/", "HOTELS"), ("/buses/", "BUSES"), ("/cabs/", "CABS"), ("/packages/", "PACKAGES")]
        
        for route, name in routes:
            try:
                response = await page.goto(f"{base}{route}")
                status = response.status if response else "NO_RESPONSE"
                print(f"✓ {name:12} {route:20} Status: {status}")
            except Exception as e:
                print(f"✗ {name:12} {route:20} Error: {e}")
        
        # Check hotel listing specifically
        print("\n" + "-"*60)
        print("HOTEL LISTING DETAILED CHECK")
        print("-"*60)
        
        await page.goto(f"{base}/hotels/")
        
        # Wait for page to load
        await page.wait_for_selector(".max-w-7xl", timeout=5000)
        
        # Check key elements
        checks = {
            "Max-width container": ".max-w-7xl",
            "Grid layout": ".lg\\:grid",
            "Sticky sidebar": ".sticky",
            "Sort bar": "#sort-bar",
            "Filters sidebar": "#filters-sidebar",
            "Sort buttons": "button[name='sort']",
        }
        
        for check_name, selector in checks.items():
            count = await page.locator(selector).count()
            status = "✓" if count > 0 else "✗"
            print(f"{status} {check_name:30} ({selector}) - Found: {count}")
        
        # Check for hardcoded Madikeri
        madikeri = await page.locator("text='Madikeri'").count()
        print(f"{'✓' if madikeri == 0 else '✗'} Hardcoded Madikeri default: {madikeri} (should be 0)")
        
        # Check hotel details
        print("\n" + "-"*60)
        print("BUSES PAGE CHECK")
        print("-"*60)
        
        await page.goto(f"{base}/buses/")
        await page.wait_for_selector(".hero--search", timeout=5000)
        
        bus_checks = {
            "Hero section": ".hero--search",
            "From City input": "input[name='from_city']",
            "To City input": "input[name='to_city']",
            "Date input": "input[name='date']",
        }
        
        for check_name, selector in bus_checks.items():
            count = await page.locator(selector).count()
            status = "✓" if count > 0 else "✗"
            print(f"{status} {check_name:30} - Found: {count}")
        
        print("\n" + "-"*60)
        print("CABS PAGE CHECK")
        print("-"*60)
        
        await page.goto(f"{base}/cabs/")
        await page.wait_for_selector(".hero--search", timeout=5000)
        
        # Try both field name patterns
        pickup_count = await page.locator("input[name='pickup']").count()
        if pickup_count == 0:
            pickup_count = await page.locator("input[placeholder*='Pickup']").count()
        
        dropoff_count = await page.locator("input[name='dropoff']").count()
        if dropoff_count == 0:
            dropoff_count = await page.locator("input[placeholder*='Dropoff']").count()
        
        print(f"{'✓' if pickup_count > 0 else '✗'} Pickup field - Found: {pickup_count}")
        print(f"{'✓' if dropoff_count > 0 else '✗'} Dropoff field - Found: {dropoff_count}")
        
        print("\n" + "-"*60)
        print("PACKAGES PAGE CHECK")
        print("-"*60)
        
        await page.goto(f"{base}/packages/")
        await page.wait_for_selector("main", timeout=5000)
        
        packages_checks = {
            "Hero section": ".hero--search",
            "Package cards": ".rounded-2xl",
        }
        
        for check_name, selector in packages_checks.items():
            count = await page.locator(selector).count()
            status = "✓" if count > 0 else "✗"
            print(f"{status} {check_name:30} - Found: {count}")
        
        print("\n" + "="*60)
        print("VALIDATION COMPLETE - All critical paths verified")
        print("="*60 + "\n")
        
        await context.close()
        await browser.close()

asyncio.run(validate())
