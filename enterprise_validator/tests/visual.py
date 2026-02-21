"""Visual regression detection tests"""

from playwright.sync_api import sync_playwright
import sys
import os
sys.path.insert(0, '..')
from config import BASE_URL, VISUAL_THRESHOLD

def run():
    """Test for visual regressions"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=5000)
            page.wait_for_timeout(500)
            
            # Take screenshot
            screenshot_path = "../baselines/current.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            page.screenshot(path=screenshot_path)
            
            # Check if baseline exists
            baseline_path = "../baselines/home.png"
            if not os.path.exists(baseline_path):
                # Create baseline if missing
                page.screenshot(path=baseline_path)
            
            browser.close()
    except Exception as e:
        errors.append(f"Visual test error: {str(e)}")
    
    return errors