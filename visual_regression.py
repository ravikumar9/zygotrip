import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30
UI_PHASE = os.getenv("UI_PHASE", "redesign").lower()

ROUTES = ["/", "/hotels/", "/buses/", "/cabs/", "/packages/"]

VIEWPORTS = {
    "desktop": {"width": 1280, "height": 720},
    "tablet": {"width": 834, "height": 1112},
    "mobile": {"width": 375, "height": 667},
}

ROOT = Path(__file__).resolve().parent
BASELINE_DIR = ROOT / "baselines" / "visual"
DIFF_DIR = ROOT / "test-results" / "visual-diff"
REPORT_PATH = ROOT / "visual_report.json"


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


def ensure_dirs():
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_DIR.mkdir(parents=True, exist_ok=True)


async def launch_browser(playwright):
    try:
        return await playwright.chromium.launch(headless=True)
    except Exception as exc:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False,
        )
        return await playwright.chromium.launch(headless=True)


def diff_images(baseline_path, current_path, diff_path):
    """Compare two images and calculate diff ratio."""
    baseline = Image.open(baseline_path).convert("RGB")
    current = Image.open(current_path).convert("RGB")

    if baseline.size != current.size:
        max_w = max(baseline.size[0], current.size[0])
        max_h = max(baseline.size[1], current.size[1])
        padded_baseline = Image.new("RGB", (max_w, max_h), (255, 255, 255))
        padded_current = Image.new("RGB", (max_w, max_h), (255, 255, 255))
        padded_baseline.paste(baseline, (0, 0))
        padded_current.paste(current, (0, 0))
        baseline = padded_baseline
        current = padded_current

    diff = ImageChops.difference(baseline, current)
    stat = ImageStat.Stat(diff)
    diff_ratio = sum(stat.mean) / (len(stat.mean) * 255)
    diff.save(diff_path)
    return diff_ratio


def safe_name(value):
    import re
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip("/") or "home")


async def validate_page(browser, page_key, viewport_name, viewport):
    """Capture screenshot and compare to baseline if UI_PHASE=freeze."""
    failures = []

    if UI_PHASE != "freeze":
        return failures

    async with await browser.new_page(viewport=viewport) as page:
        try:
            await page.goto(f"{BASE_URL}{page_key}", timeout=TIMEOUT * 1000)
            await page.wait_for_load_state("networkidle")

            filename = f"{safe_name(page_key)}_{viewport_name}.png"
            baseline_path = BASELINE_DIR / filename
            current_path = DIFF_DIR / f"current_{filename}"
            diff_path = DIFF_DIR / f"diff_{filename}"

            await page.screenshot(path=current_path)

            if not baseline_path.exists():
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                current_path.rename(baseline_path)
                return []

            diff_ratio = diff_images(baseline_path, current_path, diff_path)

            if diff_ratio > 0.05:
                failures.append(f"{page_key} VISUAL: diff {diff_ratio:.3f} ({viewport_name})")

            current_path.unlink(missing_ok=True)

        except PlaywrightTimeoutError:
            failures.append(f"{page_key} VISUAL: page timeout ({viewport_name})")
        except Exception as e:
            failures.append(f"{page_key} VISUAL: {str(e)[:50]} ({viewport_name})")

    return failures


async def main():
    ensure_dirs()
    proc = start_server()
    all_failures = []

    print(f"UI_PHASE={UI_PHASE}")
    if UI_PHASE != "freeze":
        print("Visual validation disabled (UI_PHASE=redesign)")
        REPORT_PATH.write_text(
            json.dumps({"total_failures": 0, "failures": [], "status": "skipped"}),
            encoding="utf-8",
        )
        print(json.dumps({"total_failures": 0, "failures": [], "status": "skipped"}, indent=2))
        return

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


if __name__ == "__main__":
    asyncio.run(main())