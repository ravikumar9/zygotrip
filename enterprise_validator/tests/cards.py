"""Card rendering validation tests"""

from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0, '..')
from config import BASE_URL

def run():
    """Test that cards render on all marketplace pages"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            
            test_routes = [
                ("/hotels/", "Hotels"),
                ("/buses/", "Buses"),
                ("/cabs/", "Cabs"),
                ("/packages/", "Packages")
            ]
            
            for route, page_name in test_routes:
                try:
                    page = browser.new_page(viewport={"width": 1920, "height": 1080})
                    page.goto(BASE_URL + route, wait_until="domcontentloaded", timeout=5000)
                    page.wait_for_timeout(800)
                    
                    # Count cards
                    card_count = page.locator("[class*='card']").count()
                    
                    if card_count == 0:
                        errors.append(f"No cards found on {page_name} page ({route})")
                    
                    page.close()
                except Exception as e:
                    errors.append(f"Card test error on {page_name}: {str(e)}")
            
            browser.close()
    except Exception as e:
        errors.append(f"Card test critical error: {str(e)}")
    
    return errors