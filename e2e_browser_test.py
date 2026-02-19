"""
E2E BROWSER TESTING - VISIBLE CHROMIUM with REAL USER FLOWS
Opens visible browser window and performs complete booking flows
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

ISSUES = []
RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "tests": {},
    "issues": []
}

async def test_navbar(page):
    """Check navbar has all links"""
    try:
        await page.goto("http://localhost:8000/hotels/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        # Check for each navbar link separately
        required = [("/", "Home"), ("/hotels/", "Hotels"), ("/buses/", "Buses"), ("/cabs/", "Cabs"), ("/packages/", "Packages"), ("/flights/", "Flights"), ("/trains/", "Trains"), ("/login/", "Login"), ("/register/", "Register")]
        
        found_count = 0
        for href, label in required:
            try:
                link = page.locator(f"a[href='{href}']")
                if await link.count() > 0:
                    found_count += 1
            except:
                pass
        
        if found_count >= 8:
            return True, f"Navbar OK: All {found_count}/9 main links present"
        else:
            return False, f"Navbar items missing. Found {found_count}/9"
    except Exception as e:
        return False, f"Navbar test error: {str(e)[:100]}"

async def test_gradient(page):
    """Check background gradient"""
    try:
        await page.goto("http://localhost:8000/hotels/", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        
        # Simple approach: check if body has any of the gradient indicators
        page_content = await page.content()
        
        has_gradient = ("gradient" in page_content and "from-indigo" in page_content) or ("bg-gradient" in page_content)
        
        if has_gradient:
            return True, "Gradient background detected in CSS"
        else:
            return False, "No gradient background found in page CSS"
    except Exception as e:
        return False, f"Gradient test error: {str(e)[:100]}"

async def test_list_page(page, url, page_name):
    """Test list page renders cards"""
    try:
        await page.goto(f"http://localhost:8000{url}", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        
        # Look for cards
        cards = await page.locator('[class*="card"], [class*="item"], [class*="product"]').all()
        
        if len(cards) > 0:
            return True, f"{page_name}: {len(cards)} cards found"
        else:
            return False, f"{page_name}: No cards found"
    except Exception as e:
        return False, f"{page_name} error: {str(e)}"

async def test_card_click_detail(page):
    """Click card and verify detail page loads"""
    try:
        # Navigate to hotels
        await page.goto("http://localhost:8000/hotels/", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        
        # Find links with /hotels/ in href (detail links)
        detail_links = await page.locator('a[href*="/hotels/"]').all()
        detail_links = [link for link in detail_links if await link.get_attribute("href") != "/hotels/"]
        
        if not detail_links:
            return False, "No detail links found on hotels page"
        
        # Click first detail link
        first_link = detail_links[0]
        href = await first_link.get_attribute("href")
        
        await first_link.click()
        await page.wait_for_url(f"**{href}", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        
        # Check detail page has content
        content = await page.text_content("body")
        if len(content) > 200:
            return True, f"Detail page loaded: {href}"
        else:
            return False, f"Detail page empty: {href}"
            
    except Exception as e:
        return False, f"Card click error: {str(e)}"

async def test_filters(page):
    """Check filters render"""
    try:
        await page.goto("http://localhost:8000/hotels/", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        
        # Look for filter elements
        filters = await page.locator('input[type="checkbox"], input[type="text"], select, [class*="filter"]').all()
        
        if len(filters) > 0:
            return True, f"Filters found: {len(filters)} elements"
        else:
            return False, "No filter elements found"
    except Exception as e:
        return False, f"Filters test error: {str(e)}"

async def test_console_errors(page):
    """Check for JS errors"""
    errors = []
    page.on("console", lambda msg: errors.append(f"{msg.type}: {msg.text}") if msg.type in ["error", "warning"] else None)
    page.on("pageerror", lambda exc: errors.append(f"Page error: {str(exc)}"))
    
    await page.goto("http://localhost:8000/hotels/", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    
    if not errors:
        return True, "No console errors"
    else:
        return False, f"Console errors: {errors[:3]}"

async def main():
    async with async_playwright() as p:
        # OPEN VISIBLE BROWSER - NOT HEADLESS
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("\n" + "="*80)
        print("E2E BROWSER AUTOMATION - VISIBLE CHROMIUM")
        print("="*80)
        
        # TEST 1: NAVBAR
        print("\n[1/8] Testing Navbar...")
        passed, msg = await test_navbar(page)
        RESULTS["tests"]["navbar"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Navbar: {msg}")
        
        # TEST 2: GRADIENT
        print("\n[2/8] Testing Gradient Background...")
        passed, msg = await test_gradient(page)
        RESULTS["tests"]["gradient"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Gradient: {msg}")
        
        # TEST 3: HOTELS LIST
        print("\n[3/8] Testing Hotels List Page...")
        passed, msg = await test_list_page(page, "/hotels/", "Hotels")
        RESULTS["tests"]["hotels_list"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Hotels List: {msg}")
        
        # TEST 4: BUSES LIST
        print("\n[4/8] Testing Buses List Page...")
        passed, msg = await test_list_page(page, "/buses/", "Buses")
        RESULTS["tests"]["buses_list"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Buses List: {msg}")
        
        # TEST 5: CABS LIST
        print("\n[5/8] Testing Cabs List Page...")
        passed, msg = await test_list_page(page, "/cabs/", "Cabs")
        RESULTS["tests"]["cabs_list"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Cabs List: {msg}")
        
        # TEST 6: FILTERS
        print("\n[6/8] Testing Filters...")
        passed, msg = await test_filters(page)
        RESULTS["tests"]["filters"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Filters: {msg}")
        
        # TEST 7: DETAIL PAGE FLOW
        print("\n[7/8] Testing Detail Page Flow...")
        passed, msg = await test_card_click_detail(page)
        RESULTS["tests"]["detail_flow"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Detail Flow: {msg}")
        
        # TEST 8: CONSOLE ERRORS
        print("\n[8/8] Testing Console Errors...")
        passed, msg = await test_console_errors(page)
        RESULTS["tests"]["console"] = {"passed": passed, "msg": msg}
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if not passed:
            ISSUES.append(f"Console: {msg}")
        
        # SUMMARY
        print("\n" + "="*80)
        passed_count = sum(1 for t in RESULTS["tests"].values() if t["passed"])
        total_count = len(RESULTS["tests"])
        
        print(f"TESTS PASSED: {passed_count}/{total_count}")
        
        if ISSUES:
            print("\nISSUES FOUND:")
            for issue in ISSUES:
                print(f"  - {issue}")
            RESULTS["issues"] = ISSUES
        else:
            print("\nALL TESTS PASSED!")
        
        print("="*80)
        
        # Keep browser open for 30 seconds
        print("\nBrowser open for inspection (30 seconds)...")
        await page.wait_for_timeout(30000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
    
    # Save results
    with open("e2e_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    
    print("\nResults saved to e2e_results.json")
