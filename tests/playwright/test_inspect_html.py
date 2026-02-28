"""Diagnostic test to inspect HTML content"""
import pytest
from playwright.sync_api import Page
from datetime import datetime, timedelta


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0",
        "ignore_https_errors": True,
    }


def test_inspect_html(page: Page):
    """Inspect the actual HTML to diagnose missing elements"""
    checkin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    checkout = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
    
    url = f"https://127.0.0.1:8000/hotels/hotel-listing/?location=Udaipur&checkin={checkin}&checkout={checkout}&adults=2&rooms=1"
    page.goto(url)
    
    # Get HTML content
    html = page.content()
    
    # Check for key indicators
    print("\n=== DIAGNOSTIC RESULTS ===")
    print(f"URL: {url}")
    print(f"Page title: {page.title()}")
    
    # Check for data attributes
    has_hotel_card_attr = 'data-hotel-card' in html
    print(f"Has data-hotel-card: {has_hotel_card_attr}")
    
    # Count occurrences
    hotel_card_count = html.count('data-hotel-card')
    print(f"data-hotel-card count: {hotel_card_count}")
    
    # Check for hotels container
    has_hotels_grid = 'hotel-cards-grid' in html
    print(f"Has hotel-cards-grid: {has_hotels_grid}")
    
    # Look for empty state
    has_empty_state = 'empty-state' in html
    print(f"Has empty-state: {has_empty_state}")
    
    # Look for actual hotel data
    has_hotel_name_class = 'hotel-name' in html
    print(f"Has hotel-name class: {has_hotel_name_class}")
    
    # Look for price
    has_price = '₹' in html
    print(f"Has price symbol: {has_price}")
    
    # Save a snippet of the body  
    body_start = html.find('<body')
    body_end = html.find('</body>') + len('</body>')
    if body_start > 0 and body_end > body_start:
        body_content = html[body_start:min(body_start + 3000, body_end)]
        print(f"\nFirst 3000 chars of body:")
        print(body_content[:500])
    
    # Look for hotel-cards-grid section
    grid_start = html.find('hotel-cards-grid')
    if grid_start > 0:
        print(f"\nFound hotel-cards-grid at position {grid_start}")
        print(html[grid_start:grid_start + 500])
    else:
        print("\nNo 'hotel-cards-grid' found in HTML!")
