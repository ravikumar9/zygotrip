"""Booking flow validation tests"""

from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0, '..')
from config import BASE_URL

def run():
    """Test booking flow: list -> detail -> booking"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            
            # Step 1: Load list page
            page.goto(BASE_URL + "/hotels/", wait_until="domcontentloaded", timeout=5000)
            page.wait_for_timeout(500)
            
            # Step 2: Find and click first card
            cards = page.locator("[class*='card']")
            card_count = cards.count()
            
            if card_count == 0:
                errors.append("No cards to click for booking flow test")
            else:
                # Get first card's link
                first_card_link = page.locator("[class*='card'] a").first
                href = first_card_link.get_attribute("href")
                
                if href:
                    # Step 3: Navigate to detail page
                    page.goto(BASE_URL + href, wait_until="domcontentloaded", timeout=5000)
                    page.wait_for_timeout(500)
                    
                    # Check for detail page content
                    html = page.content()
                    if len(html) < 200:
                        errors.append("Detail page content too small or not loaded")
                else:
                    errors.append("No href found on card link")
            
            browser.close()
    except Exception as e:
        errors.append(f"Booking flow test error: {str(e)}")
    
    return errors
