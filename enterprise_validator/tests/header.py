"""Header validation tests"""

from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0, '..')
from config import BASE_URL, REQUIRED_HEADER_LINKS

def run():
    """Test all required header links"""
    errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=5000)
            page.wait_for_timeout(500)
            
            # Get all links on page
            all_links = page.locator("a").all()
            hrefs_on_page = []
            texts_on_page = []
            
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    text = link.text_content()
                    if href:
                        hrefs_on_page.append(href)
                    if text:
                        texts_on_page.append(text.strip())
                except:
                    pass
            
            # Check for required links
            for link_name in REQUIRED_HEADER_LINKS:
                href = f"/{link_name.lower()}/"
                found = False
                
                # Check by href
                if href in hrefs_on_page:
                    found = True
                
                # Check by text (for flexible display)
                if link_name in texts_on_page or link_name.lower() in [t.lower() for t in texts_on_page]:
                    found = True
                
                if not found:
                    errors.append(f"Missing header link: {link_name} ({href})")
            
            browser.close()
    except Exception as e:
        errors.append(f"Header test error: {str(e)}")
    
    return errors
