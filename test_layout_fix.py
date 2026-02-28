"""Test that navbar and footer are displaying correctly"""
import requests
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()

def test_landing_page():
    """Test landing page navbar and footer"""
    url = 'https://localhost:8000/hotels/'
    r = requests.get(url, verify=False, timeout=10)
    
    print(f"✓ Landing page status: {r.status_code}")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Check if CSS files are loaded
        css_links = soup.find_all('link', rel='stylesheet')
        print(f"✓ Found {len(css_links)} CSS files")
        for css in css_links:
            href = css.get('href', '')
            if 'base.css' in href or 'layout.css' in href:
                print(f"  - {href}")
        
        # Check navbar
        navbar = soup.find('ul', class_='navbar-nav')
        if navbar:
            print(f"✓ Navbar found with class 'navbar-nav'")
            nav_items = navbar.find_all('li')
            print(f"  - Contains {len(nav_items)} navigation items")
        else:
            print("✗ ERROR: Navbar not found")
        
        # Check footer
        footer_grid = soup.find('div', class_='footer-grid')
        if footer_grid:
            print(f"✓ Footer grid found")
            columns = footer_grid.find_all('div', class_='footer-column')
            print(f"  - Contains {len(columns)} columns")
        else:
            print("✗ ERROR: Footer grid not found")
        
        # Check if styles are inline or external
        style_tags = soup.find_all('style')
        if style_tags:
            print(f"⚠ Found {len(style_tags)} inline <style> tags (might override external CSS)")
    else:
        print(f"✗ ERROR: HTTP {r.status_code}")

if __name__ == '__main__':
    import time
    print("Waiting for server to be ready...")
    time.sleep(3)
    test_landing_page()
