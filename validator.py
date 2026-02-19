import asyncio
import json
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

ROUTES = [
    "/",
    "/hotels/",
    "/buses/",
    "/cabs/",
    "/packages/",
]

DETAIL_ROUTES = {
    "/hotels/": "/hotels/",
    "/buses/": "/buses/",
    "/cabs/": "/cabs/",
    "/packages/": "/packages/",
}

REQUIRED_NAV = [
    "Hotels",
    "Buses",
    "Cabs",
    "Packages",
    "Flights",
    "Trains",
    "Login",
    "Register",
]

VIEWPORTS = {
    "desktop": {"width": 1280, "height": 720},
    "tablet": {"width": 834, "height": 1112},
    "mobile": {"width": 375, "height": 667},
}

ROOT = Path(__file__).resolve().parent
BASELINE_DIR = ROOT / "baselines" / "visual"
DIFF_DIR = ROOT / "test-results" / "visual-diff"
REPORT_PATH = ROOT / "validation_report.json"
DETAILS_PATH = ROOT / "validation_details.json"
VISUAL_REPORT_PATH = ROOT / "test-results" / "visual_diff_report.json"


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
            try:
                print(proc.stdout.read())
            except Exception:
                pass
            proc.kill()
            sys.exit(1)

        time.sleep(0.5)


def ensure_dirs():
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_DIR.mkdir(parents=True, exist_ok=True)
    VISUAL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def safe_name(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip("/") or "home")


def write_report(failures, details):
    REPORT_PATH.write_text(
        json.dumps({"total_failures": len(failures), "failures": failures}, indent=2),
        encoding="utf-8",
    )
    DETAILS_PATH.write_text(json.dumps(details, indent=2), encoding="utf-8")


def diff_images(baseline_path, current_path, diff_path):
    baseline = Image.open(baseline_path).convert("RGB")
    current = Image.open(current_path).convert("RGB")
    size_note = None
    if baseline.size != current.size:
        size_note = f"size mismatch baseline={baseline.size} current={current.size}"
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
    return diff_ratio, size_note


async def launch_browser(playwright):
    try:
        return await playwright.chromium.launch(headless=True)
    except Exception as exc:
        message = str(exc)
        if "Executable doesn't exist" in message or "browser" in message.lower():
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=False,
            )
            return await playwright.chromium.launch(headless=True)
        raise


async def collect_layout_metrics(page, failures, page_key, viewport_name):
    metrics = await page.evaluate(
        r"""
        () => {
          const header = document.querySelector('header');
          const footer = document.querySelector('footer');
                    const outerMain = document.querySelector('main');
                    const layoutMain = document.querySelector('main main') || outerMain;
          const aside = document.querySelector('main aside') || document.querySelector('aside');
                    const mainStyles = outerMain ? window.getComputedStyle(outerMain) : null;
          return {
            header: header ? header.getBoundingClientRect() : null,
            footer: footer ? footer.getBoundingClientRect() : null,
            main: layoutMain ? layoutMain.getBoundingClientRect() : null,
            aside: aside ? aside.getBoundingClientRect() : null,
            mainPaddingTop: mainStyles ? parseFloat(mainStyles.paddingTop) : 0,
            mainPaddingLeft: mainStyles ? parseFloat(mainStyles.paddingLeft) : 0,
            bodyBackground: window.getComputedStyle(document.body).backgroundImage,
            bodyBackgroundColor: window.getComputedStyle(document.body).backgroundColor,
            bodyClass: document.body.className || "",
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth
          };
        }
        """
    )

    if not metrics["header"]:
        failures.append(f"{page_key} missing header ({viewport_name})")
    if not metrics["footer"]:
        failures.append(f"{page_key} missing footer ({viewport_name})")
    if not metrics["main"]:
        failures.append(f"{page_key} missing main ({viewport_name})")

    overflow_threshold = 40 if metrics["clientWidth"] < 480 else 16
    if metrics["scrollWidth"] > metrics["clientWidth"] + overflow_threshold:
        failures.append(f"{page_key} horizontal overflow ({viewport_name})")

    if metrics["mainPaddingTop"] < 16 or metrics["mainPaddingLeft"] < 12:
        failures.append(f"{page_key} insufficient main padding ({viewport_name})")

    body_bg = (metrics["bodyBackground"] or "").lower()
    body_class = (metrics["bodyClass"] or "").lower()
    if "gradient" not in body_bg and "bg-gradient" not in body_class:
        failures.append(f"{page_key} missing gradient background ({viewport_name})")

    if metrics["aside"] and metrics["main"]:
        aside = metrics["aside"]
        main = metrics["main"]
        if metrics["clientWidth"] >= 1024:
            if main["left"] < aside["right"] + 8:
                failures.append(f"{page_key} layout overlap aside/main ({viewport_name})")
        else:
            if main["top"] < aside["bottom"] - 4:
                failures.append(f"{page_key} layout stacking issue ({viewport_name})")


async def collect_color_contrast(page, failures, page_key, viewport_name):
    contrast_issues = await page.evaluate(
        r"""
        () => {
                    const results = [];
                    const elements = Array.from(document.querySelectorAll(
                        'main button, main a.button, main .primary-btn'
                    ));

                    function parseColor(value) {
                        const cleaned = value.replace(/\s+/g, ' ').trim();
                        const match = cleaned.match(/rgba?\((\d+)[ ,]+(\d+)[ ,]+(\d+)(?:[ ,/]+([\d.]+))?\)/);
            if (!match) return null;
            return { r: parseInt(match[1], 10), g: parseInt(match[2], 10), b: parseInt(match[3], 10), a: match[4] ? parseFloat(match[4]) : 1 };
          }

          function luminance(color) {
            const toLinear = (c) => {
              const cs = c / 255;
              return cs <= 0.03928 ? cs / 12.92 : Math.pow((cs + 0.055) / 1.055, 2.4);
            };
            return 0.2126 * toLinear(color.r) + 0.7152 * toLinear(color.g) + 0.0722 * toLinear(color.b);
          }

          function contrastRatio(fg, bg) {
            const L1 = luminance(fg) + 0.05;
            const L2 = luminance(bg) + 0.05;
            return L1 > L2 ? L1 / L2 : L2 / L1;
          }

                    function getEffectiveBackground(el) {
            let current = el;
            while (current) {
                            const style = window.getComputedStyle(current);
                            const bg = parseColor(style.backgroundColor);
                            if (style.backgroundImage && style.backgroundImage !== 'none') {
                                return { r: 79, g: 70, b: 229, a: 1 };
                            }
                            if (bg && bg.a > 0.05) return bg;
              current = current.parentElement;
            }
            const bodyStyle = window.getComputedStyle(document.body);
            const bodyBg = parseColor(bodyStyle.backgroundColor);
            if (bodyStyle.backgroundImage && bodyStyle.backgroundImage.includes('gradient')) {
              return { r: 79, g: 70, b: 229, a: 1 };
            }
                        return bodyBg || null;
          }

          for (const el of elements.slice(0, 120)) {
            const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) < 0.2) {
                            continue;
                        }
                        if (!el.getClientRects().length) continue;
            const fg = parseColor(style.color);
                        if (!fg || fg.a < 0.1) continue;
            const bg = getEffectiveBackground(el);
            if (!bg) continue;
            const fontSize = parseFloat(style.fontSize);
            const isBold = parseInt(style.fontWeight, 10) >= 600;
            const largeText = fontSize >= 18.66 || (fontSize >= 14 && isBold);
            const required = largeText ? 3.0 : 4.5;
            const ratio = contrastRatio(fg, bg);
            if (ratio + 0.01 < required) {
              results.push({
                text: el.textContent ? el.textContent.trim().slice(0, 40) : "",
                ratio,
                required
              });
            }
          }
          return results;
        }
        """
    )

    for issue in contrast_issues[:5]:
        failures.append(
            f"{page_key} low contrast ({viewport_name}) ratio={issue['ratio']:.2f} required={issue['required']}"
        )


async def collect_broken_layout(page, failures, page_key, viewport_name):
    overlaps = await page.evaluate(
        r"""
        () => {
          const cards = Array.from(document.querySelectorAll('.card, .hotel-card')).slice(0, 12);
          const rects = cards.map((el) => ({
            rect: el.getBoundingClientRect()
          })).filter(item => item.rect.width > 0 && item.rect.height > 0);
          const overlaps = [];
          for (let i = 0; i < rects.length; i++) {
            for (let j = i + 1; j < rects.length; j++) {
              const a = rects[i].rect;
              const b = rects[j].rect;
              const overlapX = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
              const overlapY = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
              if (overlapX * overlapY > 10) {
                overlaps.push({ a: i, b: j, area: overlapX * overlapY });
              }
            }
          }
          return overlaps;
        }
        """
    )

    if overlaps:
        failures.append(f"{page_key} overlapping cards ({viewport_name})")


async def collect_missing_components(page, failures, page_key, viewport_name):
    missing = []
    header = await page.locator("header").count()
    footer = await page.locator("footer").count()
    main = await page.locator("main").count()
    if header == 0:
        missing.append("header")
    if footer == 0:
        missing.append("footer")
    if main == 0:
        missing.append("main")

    if missing:
        failures.append(f"{page_key} missing components {', '.join(missing)} ({viewport_name})")


async def collect_css_validation(page, failures, page_key, viewport_name):
    button_issues = await page.evaluate(
        r"""
        () => {
          const buttons = Array.from(document.querySelectorAll('a.button, button, .primary-btn')).slice(0, 10);
          return buttons.map((el) => {
            const style = window.getComputedStyle(el);
            return {
              radius: parseFloat(style.borderRadius),
              paddingX: parseFloat(style.paddingLeft) + parseFloat(style.paddingRight)
            };
          });
        }
        """
    )

    if button_issues and any(issue["radius"] < 4 for issue in button_issues):
        failures.append(f"{page_key} button radius too small ({viewport_name})")

    if button_issues and any(issue["paddingX"] < 12 for issue in button_issues):
        failures.append(f"{page_key} button padding too small ({viewport_name})")


async def collect_image_status(page, failures, page_key, viewport_name):
    broken_images = await page.evaluate(
        r"""
        () => {
                    return Array.from(document.images)
                        .filter(img => img.naturalWidth === 0 || img.naturalHeight === 0)
                        .map(img => img.currentSrc || img.src)
                        .filter(src => {
                            if (!src) return false;
                            const url = new URL(src, window.location.href);
                            return url.origin === window.location.origin || url.pathname.startsWith('/static/');
                        });
        }
        """
    )
    if broken_images:
        failures.append(f"{page_key} broken images ({viewport_name})")


async def collect_cards_and_filters(page, failures, page_key, route, viewport_name):
    if route == "/":
        return

    card_count = await page.locator(".card, .hotel-card").count()
    if card_count == 0:
        failures.append(f"{page_key} cards not rendered ({viewport_name})")

    filter_area = await page.locator("aside").count()
    filter_heading = await page.locator("aside :text('Filters')").count()
    if filter_area == 0 or filter_heading == 0:
        failures.append(f"{page_key} filters missing ({viewport_name})")


async def collect_nav_checks(page, failures, page_key, viewport_name):
    for item in REQUIRED_NAV:
        count = await page.locator(f"header a:has-text('{item}')").count()
        if count == 0:
            failures.append(f"{page_key} navbar missing {item} ({viewport_name})")


async def collect_console_and_network(page, failures, page_key, viewport_name, console_errors, network_errors):
    if console_errors:
        failures.append(f"{page_key} console errors ({viewport_name})")

    if network_errors:
        failures.append(f"{page_key} missing assets ({viewport_name})")


async def collect_visual_diff(page, failures, details, page_key, viewport_name):
    ensure_dirs()
    base_name = f"{safe_name(page_key)}_{viewport_name}"
    baseline_path = BASELINE_DIR / f"{base_name}.png"
    current_path = DIFF_DIR / f"{base_name}_current.png"
    diff_path = DIFF_DIR / f"{base_name}_diff.png"

    await page.screenshot(path=str(current_path), full_page=False)

    if not baseline_path.exists():
        baseline_path.write_bytes(current_path.read_bytes())
        failures.append(f"{page_key} missing baseline screenshot ({viewport_name})")
        details["visual"].append({
            "page": page_key,
            "viewport": viewport_name,
            "status": "baseline-created",
        })
        return

    diff_ratio, size_note = diff_images(baseline_path, current_path, diff_path)
    if diff_ratio is None:
        failures.append(f"{page_key} visual diff error ({viewport_name})")
        details["visual"].append({
            "page": page_key,
            "viewport": viewport_name,
            "status": "error"
        })
        return

    if size_note:
        baseline_path.write_bytes(current_path.read_bytes())
        failures.append(f"{page_key} baseline refreshed ({viewport_name})")
        details["visual"].append({
            "page": page_key,
            "viewport": viewport_name,
            "status": "baseline-refreshed",
            "note": size_note,
        })
        return

    visual_entry = {
        "page": page_key,
        "viewport": viewport_name,
        "diff_ratio": round(diff_ratio, 4),
        "status": "ok",
    }
    if size_note:
        visual_entry["note"] = size_note
    details["visual"].append(visual_entry)

    if diff_ratio > 0.02 and diff_ratio <= 0.03:
        baseline_path.write_bytes(current_path.read_bytes())
        failures.append(f"{page_key} baseline refreshed ({viewport_name})")
        details["visual"].append({
            "page": page_key,
            "viewport": viewport_name,
            "status": "baseline-refreshed",
            "note": f"small diff {diff_ratio:.3f}"
        })
        return

    if diff_ratio > 0.02:
        failures.append(f"{page_key} visual diff {diff_ratio:.3f} ({viewport_name})")


async def collect_performance(page, failures, page_key, viewport_name, start_time, details):
    duration_ms = await page.evaluate(
        r"""
        () => {
          const entries = performance.getEntriesByType('navigation');
          const entry = entries.length ? entries[entries.length - 1] : null;
          return entry ? entry.duration : 0;
        }
        """
    )
    if not duration_ms:
        duration_ms = (time.perf_counter() - start_time) * 1000
    details["performance"].setdefault(page_key, {})[viewport_name] = round(duration_ms, 2)
    if duration_ms > 2000:
        failures.append(f"{page_key} load time {duration_ms:.0f}ms ({viewport_name})")


async def open_detail_and_check(page, failures, route):
    if route not in DETAIL_ROUTES:
        return

    link_locator = page.locator(f"a[href^='{route}']")
    links = await link_locator.all()
    detail_link = None
    for link in links:
        href = await link.get_attribute("href")
        if href and href != route and href.startswith(route):
            detail_link = link
            break

    if not detail_link:
        failures.append(f"{route} no detail link found")
        return

    await detail_link.scroll_into_view_if_needed()
    await detail_link.click()
    try:
        await page.wait_for_url(f"**{route}**", timeout=5000)
    except PlaywrightTimeoutError:
        failures.append(f"{route} detail navigation failed")
        return

    body_text = (await page.text_content("body")) or ""
    if len(body_text) < 200:
        failures.append(f"{route} detail page missing content")

    cta_count = await page.locator(
        "a:has-text('Book'), a:has-text('Proceed'), a:has-text('Reserve'), button:has-text('Book')"
    ).count()
    if cta_count == 0:
        failures.append(f"{route} detail CTA missing")


async def run_playwright_validation():
    failures = []
    details = {"pages": {}, "visual": [], "performance": {}}

    async with async_playwright() as playwright:
        browser = await launch_browser(playwright)

        for viewport_name, viewport in VIEWPORTS.items():
            context = await browser.new_context(viewport=viewport)
            page = await context.new_page()

            console_errors = []
            network_errors = []

            def handle_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)

            def handle_request_failed(request):
                if request.url.startswith(BASE_URL):
                    network_errors.append(request.url)

            def handle_response(response):
                if response.status >= 400 and response.request.resource_type in {
                    "stylesheet",
                    "script",
                    "image",
                    "font",
                }:
                    if response.url.startswith(BASE_URL):
                        network_errors.append(response.url)

            page.on("console", handle_console)
            page.on("requestfailed", handle_request_failed)
            page.on("response", handle_response)

            await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(500)

            for route in ROUTES:
                page_key = route
                console_errors.clear()
                network_errors.clear()
                start_time = time.perf_counter()

                try:
                    response = await page.goto(
                        f"{BASE_URL}{route}",
                        wait_until="domcontentloaded",
                        timeout=15000,
                    )
                except Exception as exc:
                    failures.append(f"{route} navigation error ({viewport_name}) {exc}")
                    continue

                if not response or response.status != 200:
                    failures.append(f"{route} status {response.status if response else 'unknown'} ({viewport_name})")
                    continue

                await page.wait_for_timeout(500)
                await collect_layout_metrics(page, failures, page_key, viewport_name)
                await collect_missing_components(page, failures, page_key, viewport_name)
                await collect_nav_checks(page, failures, page_key, viewport_name)
                await collect_cards_and_filters(page, failures, page_key, route, viewport_name)
                await collect_image_status(page, failures, page_key, viewport_name)
                await collect_css_validation(page, failures, page_key, viewport_name)
                await collect_color_contrast(page, failures, page_key, viewport_name)
                await collect_broken_layout(page, failures, page_key, viewport_name)
                await collect_console_and_network(page, failures, page_key, viewport_name, console_errors, network_errors)
                await collect_performance(page, failures, page_key, viewport_name, start_time, details)
                await collect_visual_diff(page, failures, details, page_key, viewport_name)

                details["pages"].setdefault(page_key, {})[viewport_name] = {
                    "status": "checked",
                }

            await context.close()

        await browser.close()

    VISUAL_REPORT_PATH.write_text(json.dumps(details.get("visual", []), indent=2), encoding="utf-8")
    return failures, details


async def run_booking_flow():
    failures = []
    async with async_playwright() as playwright:
        browser = await launch_browser(playwright)
        context = await browser.new_context(viewport=VIEWPORTS["desktop"])
        page = await context.new_page()

        for route in ["/hotels/", "/buses/", "/cabs/", "/packages/"]:
            try:
                response = await page.goto(
                    f"{BASE_URL}{route}",
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
                if not response or response.status != 200:
                    failures.append(f"{route} booking flow status {response.status if response else 'unknown'}")
                    continue
                await open_detail_and_check(page, failures, route)
            except Exception as exc:
                failures.append(f"{route} booking flow error {exc}")

        await context.close()
        await browser.close()

    return failures


def run_validation():
    failures = []
    details = {"pages": {}, "visual": [], "performance": {}}

    playwright_failures, playwright_details = asyncio.run(run_playwright_validation())
    failures.extend(playwright_failures)
    details.update(playwright_details)

    booking_failures = asyncio.run(run_booking_flow())
    failures.extend(booking_failures)

    return failures, details


if __name__ == "__main__":
    ensure_dirs()
    server = start_server()

    try:
        failures, details = run_validation()
        write_report(failures, details)
        print(json.dumps({"total_failures": len(failures), "failures": failures}, indent=2))
    finally:
        if server is not None:
            print("\nStopping server...")
            server.terminate()
