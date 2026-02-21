import asyncio
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

ROUTES = ["/", "/hotels/", "/buses/", "/cabs/", "/packages/"]

REQUIRED_NAV = ["Hotels", "Buses", "Cabs", "Packages", "Flights", "Trains", "Login", "Register"]

VIEWPORTS = {
    "desktop": {"width": 1280, "height": 720},
    "tablet": {"width": 834, "height": 1112},
    "mobile": {"width": 375, "height": 667},
}

ROOT = Path(__file__).resolve().parent
REPORT_PATH = ROOT / "structure_report.json"


def port_open(host="127.0.0.1", port=8000):
    sock = socket.socket()
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except Exception:
        return False


def start_server():
    if port_open():
        print("Server already running.")
        return None

    print("Starting Django server...")
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    start = time.time()
    while True:
        if port_open():
            print("Server started successfully.")
            return proc
        if time.time() - start > TIMEOUT:
            print("\nSERVER FAILED TO START\n")
            proc.kill()
            sys.exit(1)
        time.sleep(0.5)


async def launch_browser(playwright):
    try:
        return await playwright.chromium.launch(headless=True)
    except Exception as exc:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False,
        )
        return await playwright.chromium.launch(headless=True)


async def check_structure(page, failures, page_key, viewport_name):
    """Check HTML structure: header, main, footer must exist and be properly positioned."""
    
    structure = await page.evaluate(
        r"""
        () => {
          const header = document.querySelector('header');
          const main = document.querySelector('main');
          const footer = document.querySelector('footer');
          
          return {
            hasHeader: !!header,
            hasMain: !!main,
            hasFooter: !!footer,
            headerRect: header ? header.getBoundingClientRect() : null,
            mainRect: main ? main.getBoundingClientRect() : null,
            footerRect: footer ? footer.getBoundingClientRect() : null,
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            bodyHasGradient: window.getComputedStyle(document.body).backgroundImage.includes('gradient')
          };
        }
        """
    )

    if not structure["hasHeader"]:
        failures.append(f"{page_key} STRUCTURE: missing header ({viewport_name})")
    if not structure["hasMain"]:
        failures.append(f"{page_key} STRUCTURE: missing main ({viewport_name})")
    if not structure["hasFooter"]:
        failures.append(f"{page_key} STRUCTURE: missing footer ({viewport_name})")

    # Check overflow (structure issue, not cosmetic)
    overflow_threshold = 40 if structure["clientWidth"] < 480 else 16
    if structure["scrollWidth"] > structure["clientWidth"] + overflow_threshold:
        failures.append(f"{page_key} STRUCTURE: horizontal overflow ({viewport_name})")

    # Check header is full width
    if structure["headerRect"] and structure["headerRect"]["width"] < structure["clientWidth"] - 2:
        failures.append(f"{page_key} STRUCTURE: header not full width ({viewport_name})")

    # Check gradient background
    if not structure["bodyHasGradient"]:
        failures.append(f"{page_key} STRUCTURE: missing background gradient ({viewport_name})")


async def check_nav(page, failures, page_key, viewport_name):
    """Check navigation elements are present."""
    
    nav_items = await page.evaluate(
        r"""
        () => {
          const navText = document.body.innerText;
          const found = [];
          const required = ["Hotels", "Buses", "Cabs", "Packages", "Flights", "Trains", "Login", "Register"];
          for (const item of required) {
            if (navText.includes(item)) found.push(item);
          }
          return found;
        }
        """
    )

    missing = set(REQUIRED_NAV) - set(nav_items)
    for item in missing:
        failures.append(f"{page_key} STRUCTURE: missing nav item '{item}' ({viewport_name})")


async def validate_page(browser, page_key, viewport_name, viewport):
    """Validate a single page."""
    failures = []

    async with await browser.new_page(viewport=viewport) as page:
        try:
            await page.goto(f"{BASE_URL}{page_key}", timeout=TIMEOUT * 1000)
            await page.wait_for_load_state("networkidle")

            await check_structure(page, failures, page_key, viewport_name)
            await check_nav(page, failures, page_key, viewport_name)

        except PlaywrightTimeoutError:
            failures.append(f"{page_key} STRUCTURE: page timeout ({viewport_name})")
        except Exception as e:
            failures.append(f"{page_key} STRUCTURE: {str(e)[:50]} ({viewport_name})")

    return failures


async def main():
    proc = start_server()
    all_failures = []

    try:
        async with async_playwright() as playwright:
            browser = await launch_browser(playwright)

            for page_key in ROUTES:
                for viewport_name, viewport in VIEWPORTS.items():
                    failures = await validate_page(browser, page_key, viewport_name, viewport)
                    all_failures.extend(failures)

            await browser.close()

    finally:
        if proc:
            proc.terminate()

    REPORT_PATH.write_text(
        json.dumps(
            {"total_failures": len(all_failures), "failures": all_failures},
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps({"total_failures": len(all_failures), "failures": all_failures}, indent=2))

    if all_failures:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())