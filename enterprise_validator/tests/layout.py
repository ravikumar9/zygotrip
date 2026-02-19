"""Layout structure validation tests"""

from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0, '..')
from config import BASE_URL, ROUTES

def run():
    """Test all pages have proper layout structure"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            
            for route in ROUTES:
                try:
                    page = browser.new_page(viewport={"width": 1920, "height": 1080})
                    page.goto(BASE_URL + route, wait_until="domcontentloaded", timeout=5000)
                    page.wait_for_timeout(500)
                    
                    # Check required elements
                    header_count = page.locator("header").count()
                    main_count = page.locator("main").count()
                    footer_count = page.locator("footer").count()
                    
                    if header_count == 0:
                        errors.append(f"Missing <header> on {route}")
                    if main_count == 0:
                        errors.append(f"Missing <main> on {route}")
                    if footer_count == 0:
                        errors.append(f"Missing <footer> on {route}")
                    
                    page.close()
                except Exception as e:
                    errors.append(f"Layout test error on {route}: {str(e)}")
            
            browser.close()
    except Exception as e:
        errors.append(f"Layout test critical error: {str(e)}")
    
    return errors
