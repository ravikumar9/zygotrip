"""Console error validation tests"""

from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0, '..')
from config import BASE_URL

def run():
    """Test that there are no console errors"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            
            console_errors = []
            
            def on_console(msg):
                if "error" in msg.type.lower():
                    console_errors.append(str(msg.args))
            
            page.on("console", on_console)
            
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=5000)
            page.wait_for_timeout(1000)
            
            if console_errors:
                errors.append(f"Console errors detected: {len(console_errors)}")
            
            browser.close()
    except Exception as e:
        errors.append(f"Console test error: {str(e)}")
    
    return errors
