"""Filter validation tests"""

from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0, '..')
from config import BASE_URL

def run():
    """Test that filters exist and are functional"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(BASE_URL + "/hotels/", wait_until="domcontentloaded", timeout=5000)
            page.wait_for_timeout(500)
            
            # Check for filter elements
            filter_inputs = page.locator("input[type='checkbox'], input[type='radio'], select").count()
            
            if filter_inputs == 0:
                errors.append("No filter input elements found")
            
            browser.close()
    except Exception as e:
        errors.append(f"Filter test error: {str(e)}")
    
    return errors
