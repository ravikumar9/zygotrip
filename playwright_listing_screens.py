from playwright.sync_api import sync_playwright


URL = "https://127.0.0.1:8000/hotels/"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        page.goto(URL, timeout=20000)
        page.wait_for_timeout(2000)

        page.screenshot(path="listing_page.png", full_page=True)

        sidebar = page.locator("#filters-sidebar")
        if sidebar.count() > 0 and sidebar.is_visible():
            sidebar.screenshot(path="filter_sidebar.png")

        sort_bar = page.locator("#sort-bar")
        if sort_bar.count() > 0 and sort_bar.is_visible():
            sort_bar.screenshot(path="sort_bar.png")

        card = page.locator(".hotel-card").first
        if card.count() > 0 and card.is_visible():
            card.screenshot(path="card_layout.png")

        browser.close()


if __name__ == "__main__":
    run()
