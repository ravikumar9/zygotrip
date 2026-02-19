#!/usr/bin/env python3
"""Debug script to inspect actual page content"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        await page.goto("http://localhost:8000/hotels/", wait_until="domcontentloaded", timeout=3000)
        await page.wait_for_timeout(1500)
        
        # Get all links on page
        links = await page.locator("a").all()
        print(f"Total links found: {len(links)}")
        for i, link in enumerate(links[:15]):
            text = await link.text_content()
            href = await link.get_attribute("href")
            print(f"  {i}: text='{text}' href='{href}'")
        
        # Check for header/nav
        header_count = await page.locator("header").count()
        main_count = await page.locator("main").count()
        footer_count = await page.locator("footer").count()
        print(f"\nLayout elements: header={header_count}, main={main_count}, footer={footer_count}")
        
        # Check for gradient
        html = await page.content()
        has_gradient = "gradient" in html.lower()
        print(f"\nGradient in HTML: {has_gradient}")
        
        # Check for cards
        cards = await page.locator("[class*='card']").count()
        print(f"Cards found (class*='card'): {cards}")
        
        # Let me also check the overall HTML structure
        print("\n--- First 2000 chars of HTML ---")
        print(html[:2000])
        
        await page.wait_for_timeout(5000)
        await browser.close()

asyncio.run(main())
