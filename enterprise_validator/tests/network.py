"""Network performance validation tests"""

from playwright.sync_api import sync_playwright
import sys
import time
sys.path.insert(0, '..')
from config import BASE_URL, MAX_LOAD_MS

def run():
    """Test page load performance"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            
            start_time = time.time()
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=5000)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if elapsed_ms > MAX_LOAD_MS:
                errors.append(f"Page load too slow: {elapsed_ms:.0f}ms > {MAX_LOAD_MS}ms")
            
            browser.close()
    except Exception as e:
        errors.append(f"Network test error: {str(e)}")
    
    return errors