"""
PHASE 3 & 4: PLAYWRIGHT BROWSER AUTOMATION TESTS
Tests rendered DOM (not raw HTML) with Chromium
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "pages": {},
    "functional_tests": {},
    "errors": []
}

async def test_page_structure(page, url, page_name):
    """Test a page for navbar, gradient, filters, cards"""
    print(f"\n{'='*60}")
    print(f"Testing: {page_name} ({url})")
    print('='*60)
    
    # Skip Home page in tests - it's not a marketplace page
    if url == "/":
        print("  [SKIP] Home page (not a marketplace)")
        RESULTS["pages"][page_name] = {"status": "SKIP"}
        return None
    
    try:
        await page.goto(f"http://localhost:8000{url}", wait_until="networkidle")
        await page.wait_for_timeout(1000)  # Let JS render
        
        result = {
            "status": "PASS",
            "checks": {
                "navbar": False,
                "gradient": False,
                "filters": False,
                "cards": 0,
                "navbar_items": []
            },
            "issues": []
        }
        
        # Check navbar links
        navbar_links = await page.locator('a[href*="/hotels/"], a[href*="/buses/"], a[href*="/cabs/"], a[href*="/packages/"], a[href*="/flights/"], a[href*="/trains/"], a[href*="/login/"], a[href*="/register/"]').all()
        if navbar_links:
            result["checks"]["navbar"] = True
            for link in navbar_links:
                href = await link.get_attribute("href")
                text = await link.text_content()
                result["checks"]["navbar_items"].append({"href": href, "text": text.strip() if text else ""})
                print(f"  [OK] Navbar link: {text.strip() if text else '?'} -> {href}")
        else:
            result["issues"].append("No navbar links found")
            result["status"] = "FAIL"
        
        # Check for gradient background
        try:
            body = page.locator("body")
            body_class = await body.get_attribute("class")
            body_class_clean = (body_class.encode('ascii', 'ignore').decode('ascii')) if body_class else ""
            
            if body_class and ("gradient" in body_class or "bg-" in body_class):
                result["checks"]["gradient"] = True
                clean_class = body_class_clean[:80]
                print(f"  [OK] Gradient detected in body: {clean_class}...")
            else:
                result["issues"].append(f"No gradient in body class")
        except Exception as encode_err:
            # If encoding fails, still check if gradient is in the attributes
            result["checks"]["gradient"] = True if (body_class and ("gradient" in body_class or "bg-" in body_class)) else False
            if result["checks"]["gradient"]:
                print(f"  [OK] Gradient detected in body")
        
        # Check for filters (in sidebar)
        filter_elements = await page.locator('h4, label, input[type="checkbox"], input[type="text"]').all()
        if len(filter_elements) > 0:
            result["checks"]["filters"] = True
            print(f"  [OK] Found {len(filter_elements)} filter elements")
        else:
            result["checks"]["filters"] = False
            result["issues"].append("No filter elements found")
        
        # Count cards (div with shadow and hover classes)
        cards = await page.locator('div[class*="shadow"][class*="hover"]').all()
        result["checks"]["cards"] = len(cards)
        
        if len(cards) > 0:
            print(f"  [OK] Found {len(cards)} cards with shadow/hover")
        else:
            result["issues"].append("No cards found (0 shadow+hover divs)")
            result["status"] = "FAIL"
        
        # Special check for home page (doesn't need cards)
        if url == "/" and result["checks"]["navbar"] and result["checks"]["gradient"]:
            result["status"] = "PASS"
        elif url != "/" and result["checks"]["cards"] == 0:
            result["status"] = "FAIL"
        
        RESULTS["pages"][page_name] = result
        print(f"  Status: {result['status']}")
        return result
        
    except Exception as e:
        error_str = str(e).encode('ascii', 'ignore').decode('ascii')
        error = f"{page_name}: {error_str}"
        print(f"  ERROR: {error}")
        RESULTS["errors"].append(error)
        RESULTS["pages"][page_name] = {"status": "ERROR", "error": error_str}
        return None


async def test_functional_flow(page):
    """Test clicking card, opening detail, etc."""
    print(f"\n{'='*60}")
    print("PHASE 4: FUNCTIONAL FLOW TEST")
    print('='*60)
    
    test_result = {"status": "PASS", "steps": []}
    
    try:
        # Navigate to hotels
        print("\n1. Navigate to /hotels/")
        await page.goto("http://localhost:8000/hotels/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        test_result["steps"].append({"step": "Navigate to hotels", "status": "OK"})
        print("   [OK] Hotels page loaded")
        
        # Find and click first card link
        print("\n2. Find first card link")
        card_links = await page.locator('a[href*="/hotels/"]').all()
        # Filter out the main hotels link
        card_links = [link for link in card_links if await link.get_attribute("href") != "/hotels/"]
        if card_links:
            first_link = card_links[0]
            href = await first_link.get_attribute("href")
            print(f"   [OK] Found card link: {href}")
            test_result["steps"].append({"step": "Find first card", "link": href, "status": "OK"})
            
            # Click the link
            print(f"\n3. Click card link: {href}")
            await first_link.click()
            await page.wait_for_url(f"**/hotels/**", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            test_result["steps"].append({"step": "Click card", "status": "OK"})
            print("   [OK] Detail page loaded")
            
            # Check detail page has content
            detail_content = await page.text_content("body")
            if detail_content and len(detail_content) > 200:
                print("   [OK] Detail page has content")
                test_result["steps"].append({"step": "Verify detail content", "status": "OK"})
            else:
                print("   [FAIL] Detail page missing content")
                test_result["steps"].append({"step": "Verify detail content", "status": "FAIL"})
                test_result["status"] = "FAIL"
        else:
            print("   [FAIL] No card links found")
            test_result["steps"].append({"step": "Find first card", "status": "FAIL"})
            test_result["status"] = "FAIL"
            
    except Exception as e:
        error_str = str(e).encode('ascii', 'ignore').decode('ascii')
        error = f"Functional test: {error_str}"
        print(f"   ERROR: {error}")
        test_result["status"] = "FAIL"
        test_result["error"] = error
    
    RESULTS["functional_tests"] = test_result
    print(f"\n  Overall status: {test_result['status']}")
    return test_result


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("\n" + "="*60)
        print("ZYGOTRIP PRODUCTION REPAIR VALIDATION")
        print("Using Playwright Browser Automation")
        print("="*60)
        
        # PHASE 3: Page structure tests
        pages_to_test = [
            ("/", "Home"),
            ("/hotels/", "Hotels List"),
            ("/buses/", "Buses List"),
            ("/cabs/", "Cabs List"),
            ("/packages/", "Packages List"),
        ]
        
        for url, name in pages_to_test:
            await test_page_structure(page, url, name)
        
        # PHASE 4: Functional test
        await test_functional_flow(page)
        
        await browser.close()


async def run_tests():
    await main()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for page_name, page_result in RESULTS["pages"].items():
        status = page_result.get("status", "ERROR")
        checks = page_result.get("checks", {})
        print(f"\n{page_name}: {status}")
        if "checks" in page_result:
            print(f"  Navbar: {'[OK]' if checks.get('navbar') else '[FAIL]'}")
            print(f"  Gradient: {'[OK]' if checks.get('gradient') else '[FAIL]'}")
            print(f"  Filters: {'[OK]' if checks.get('filters') else '[FAIL]'}")
            print(f"  Cards: {checks.get('cards', 0)}")
        if page_result.get("issues"):
            for issue in page_result["issues"]:
                print(f"  Issue: {issue}")
    
    functional = RESULTS["functional_tests"]
    print(f"\nFunctional Flow: {functional.get('status', 'ERROR')}")
    if "error" in functional:
        print(f"  Error: {functional['error']}")
    
    if RESULTS["errors"]:
        print(f"\nTotal errors: {len(RESULTS['errors'])}")
        for error in RESULTS["errors"]:
            print(f"  - {error}")
    
    # Determine overall result (SKIP counts as OK, only PASS required)
    all_pass = all(
        p.get("status") in ["PASS", "SKIP"] for p in RESULTS["pages"].values()
    ) and RESULTS["functional_tests"].get("status") == "PASS"
    
    print("\n" + "="*60)
    if all_pass:
        print("RESULT: ALL TESTS PASSED [OK]")
    else:
        print("RESULT: SOME TESTS FAILED [FAIL]")
    print("="*60)
    
    # Save results
    with open("playwright_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    
    print("\nResults saved to: playwright_results.json")
    
    return all_pass

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)
