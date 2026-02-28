from playwright.sync_api import sync_playwright
import traceback

URLS = [
    "https://127.0.0.1:8000/",
    "https://127.0.0.1:8000/health/",
    "https://127.0.0.1:8000/admin/",
]


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--ignore-certificate-errors",
                "--disable-web-security",
                "--allow-running-insecure-content",
            ],
        )

        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.on("console", lambda msg: print(f"[Console] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"[PageError] {exc}"))
        page.on(
            "requestfailed",
            lambda req: print(f"[RequestFailed] {req.url} - {req.failure}"),
        )

        for url in URLS:
            try:
                print(f"\nOpening: {url}")
                response = page.goto(url, timeout=10000)
                print("Status:", response.status if response else "No response")
                page.screenshot(
                    path=url.replace("https://", "").replace("/", "_") + ".png"
                )
            except Exception:
                print("Exception while loading:")
                traceback.print_exc()

        print("\nPlaywright session running. Close browser manually to exit.")
        page.wait_for_timeout(30000)
        browser.close()


if __name__ == "__main__":
    run()
