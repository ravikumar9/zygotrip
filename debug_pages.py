#!/usr/bin/env python3
"""Debug script for buses, cabs, packages pages"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        for route, name in [("/buses/", "Buses"), ("/cabs/", "Cabs"), ("/packages/", "Packages")]:
            print(f"\n{'='*60}")
            print(f"Testing {name} page: {route}")
            print(f"{'='*60}")
            
            await page.goto(f"http://127.0.0.1:8000{route}", wait_until="domcontentloaded", timeout=5000)
            await page.wait_for_timeout(500)
            
            # Check for cards with different selectors
            card_count_1 = await page.locator("[class*='card']").count()
            card_count_2 = await page.locator("[class*='Card']").count()
            card_count_3 = await page.locator("div[class*='item']").count()
            
            print(f"Cards (class*='card'): {card_count_1}")
            print(f"Cards (class*='Card'): {card_count_2}")
            print(f"Items (class*='item'): {card_count_3}")
            
            # Check HTML content
            html = await page.content()
            print(f"HTML length: {len(html)}")
            
            # Look for elements
            divs = await page.locator("div").count()
            print(f"Total divs: {divs}")
            
            # Check for specific classes
            if "card" in html.lower():
                print("[OK] Page contains 'card' in HTML")
            else:
                print("[NO] Page does NOT contain 'card' in HTML")
            
            # Get first 3000 chars of important divs
            print("\nFirst 2000 chars of page content:")
            print(html[:2000])
        
        await page.wait_for_timeout(5000)
        await browser.close()

asyncio.run(main())