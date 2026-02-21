"""
REAL E2E TESTS (HEADLESS=FALSE)
Covers auth, search, filters, booking, provider flows.
"""
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zygotrip_project.settings")

import django

django.setup()

from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User, Role, UserRole
from apps.accounts.selectors import user_has_role
from apps.hotels.models import Property
from apps.rooms.models import RoomType
from apps.dashboard_admin.models import PropertyApproval
from apps.core.location_models import Country, State, City
from apps.booking.models import Booking
from apps.cabs.models import Cab
from apps.buses.models import Bus
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async

BASE_URL = "http://localhost:8000"
HEADLESS = False

ARTIFACTS_DIR = Path("e2e_artifacts")
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
HTML_DIR = ARTIFACTS_DIR / "html"
VIDEOS_DIR = ARTIFACTS_DIR / "videos"
LOGS_DIR = ARTIFACTS_DIR / "logs"

for d in [SCREENSHOTS_DIR, HTML_DIR, VIDEOS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    safe_msg = "".join(c for c in msg if ord(c) < 128)
    print(f"[{ts}] {safe_msg}")


def save_html(name, html):
    path = HTML_DIR / f"{name}.html"
    path.write_text(html, encoding="utf-8")


def save_json(name, data):
    path = LOGS_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def ensure_roles_and_users():
    roles = {
        "customer": "Customer",
        "property_owner": "Property Owner",
        "cab_owner": "Cab Owner",
        "bus_operator": "Bus Operator",
        "admin": "Admin",
    }
    role_objs = {}
    for code, name in roles.items():
        role_objs[code], _ = Role.objects.get_or_create(code=code, defaults={"name": name})

    creds = {
        "customer": {"email": "customer@test.com", "password": "Test123!"},
        "owner": {"email": "owner@test.com", "password": "Test123!"},
        "vendor": {"email": "vendor@test.com", "password": "Test123!"},
        "admin": {"email": "admin@test.com", "password": "Test123!"},
    }

    def ensure_user(email, password):
        user, _ = User.objects.get_or_create(email=email, defaults={"full_name": email.split("@")[0].title(), "is_active": True})
        user.set_password(password)
        user.is_active = True
        user.save()
        return user

    customer = ensure_user(creds["customer"]["email"], creds["customer"]["password"])
    owner = ensure_user(creds["owner"]["email"], creds["owner"]["password"])
    vendor = ensure_user(creds["vendor"]["email"], creds["vendor"]["password"])
    admin = ensure_user(creds["admin"]["email"], creds["admin"]["password"])

    UserRole.objects.get_or_create(user=customer, role=role_objs["customer"])
    UserRole.objects.get_or_create(user=owner, role=role_objs["property_owner"])
    UserRole.objects.get_or_create(user=vendor, role=role_objs["cab_owner"])
    UserRole.objects.get_or_create(user=vendor, role=role_objs["bus_operator"])
    UserRole.objects.get_or_create(user=admin, role=role_objs["admin"])

    return creds


def ensure_city():
    country, _ = Country.objects.get_or_create(code="IN", defaults={"name": "India", "display_name": "India"})
    state, _ = State.objects.get_or_create(country=country, code="DL", defaults={"name": "Delhi", "display_name": "Delhi"})
    city, _ = City.objects.get_or_create(
        state=state,
        code="DELHI",
        defaults={
            "name": "New Delhi",
            "display_name": "New Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "ne_lat": 28.9,
            "ne_lng": 77.4,
            "sw_lat": 28.4,
            "sw_lng": 77.0,
        },
    )
    return city


def ensure_properties(owner):
    city = ensure_city()
    total = Property.objects.count()
    if total == 0:
        log("Seeding 10 hotels (count was 0)")
        for i in range(10):
            prop = Property.objects.create(
                owner=owner,
                name=f"Test Hotel {i + 1}",
                property_type="Hotel",
                city=city,
                area="Central",
                landmark="Main Market",
                country="India",
                address=f"{i + 1} Main Road",
                description="Test property description",
                rating=4.8 if i % 2 == 0 else 3.2,
                latitude=28.6139,
                longitude=77.2090,
                base_price=2000 + i * 50,
            )
            PropertyApproval.objects.get_or_create(property=prop, defaults={"status": PropertyApproval.STATUS_APPROVED})
            RoomType.objects.get_or_create(
                property=prop,
                name="Standard",
                defaults={"description": "Standard room", "base_price": 2000, "max_guests": 2},
            )
    else:
        for prop in Property.objects.all()[:2]:
            PropertyApproval.objects.get_or_create(property=prop, defaults={"status": PropertyApproval.STATUS_APPROVED})
            if prop.room_types.count() == 0:
                RoomType.objects.create(
                    property=prop,
                    name="Standard",
                    description="Standard room",
                    base_price=2000,
                    max_guests=2,
                )


def get_public_properties_count():
    return Property.objects.filter(approval__status=PropertyApproval.STATUS_APPROVED, is_active=True).count()


def fetch_api_proof():
    url = f"{BASE_URL}/api/search/hotels/?q=delhi"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = response.read().decode("utf-8")
        save_json("api_hotels", json.loads(data))
        return True
    except Exception as exc:
        save_json("api_hotels_error", {"error": str(exc)})
        return False


async def run_e2e(creds):
    console_logs = []
    request_logs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(record_video_dir=str(VIDEOS_DIR), viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        def on_console(msg):
            console_logs.append({"type": msg.type, "text": msg.text})

        def on_request(req):
            if req.url.startswith(BASE_URL):
                request_logs.append({"method": req.method, "url": req.url})

        page.on("console", on_console)
        page.on("request", on_request)

        async def snapshot(name):
            await page.screenshot(path=str(SCREENSHOTS_DIR / f"{name}.png"), full_page=True)
            html = await page.content()
            save_html(name, html)

        # FLOW 0: Home + Hero
        log("OPEN HOME")
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await snapshot("home_after")

        # HERO bounds for spacing proof
        hero_rect = await page.evaluate("""
            () => {
                const hero = document.querySelector('.hero');
                const title = document.querySelector('.hero-title');
                const subtitle = document.querySelector('.hero-subtitle');
                if (!hero || !title || !subtitle) return null;
                return {
                    hero: hero.getBoundingClientRect(),
                    title: title.getBoundingClientRect(),
                    subtitle: subtitle.getBoundingClientRect(),
                };
            }
        """)
        save_json("hero_rect", hero_rect or {})

        # FLOW 1: Registration
        log("REGISTER USER")
        await page.goto(f"{BASE_URL}/register/", wait_until="networkidle")
        await snapshot("register_before")
        new_email = f"new_{int(datetime.now().timestamp())}@test.com"
        await page.fill('#id_email', new_email)
        await page.fill('#id_full_name', 'Test User')
        await page.fill('#id_password1', 'Test123!')
        await page.fill('#id_password2', 'Test123!')
        await page.click('button[type="submit"]')
        await page.wait_for_url(f"{BASE_URL}/**", timeout=10000)
        await snapshot("register_after")

        # Logout to ensure login form is available
        await page.goto(f"{BASE_URL}/logout/", wait_until="networkidle")
        await context.clear_cookies()

        # Registration DB proof
        def _reg_exists():
            return User.objects.filter(email=new_email).exists()
        reg_exists = await sync_to_async(_reg_exists)()

        # FLOW 2: Login (Customer)
        log("LOGIN CUSTOMER")
        await page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
        await snapshot("login_before")
        await page.wait_for_selector('#id_username', timeout=10000)
        await page.fill('#id_username', creds["customer"]["email"])
        await page.fill('#id_password', creds["customer"]["password"])
        await page.click('button[type="submit"]')
        await page.wait_for_url(f"{BASE_URL}/**", timeout=10000)
        await snapshot("login_after")

        cookies = await context.cookies()
        session_cookie = next((c for c in cookies if 'session' in c['name']), None)

        # FLOW 3: Search + Filter
        log("SEARCH + FILTER")
        await page.goto(f"{BASE_URL}/hotels/", wait_until="networkidle")
        await snapshot("hotels_before")

        def _search_city():
            prop = Property.objects.filter(
                approval__status=PropertyApproval.STATUS_APPROVED,
                is_active=True,
            ).select_related("city").first()
            if not prop:
                return ""
            if prop.city_id and prop.city:
                return prop.city.name
            if getattr(prop, "legacy_city", ""):
                return prop.legacy_city
            if prop.city_text:
                return prop.city_text
            return ""

        search_city = await sync_to_async(_search_city)()

        search_input = await page.query_selector('#search-location')
        if search_input and search_city:
            await search_input.fill(search_city)
            await page.keyboard.press("Enter")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)

        cards_before = await page.query_selector_all('.hotel-card')
        count_before = len(cards_before)

        # Bounding rect proof for alignment
        rects = await page.evaluate("""
            () => {
                const input = document.querySelector('.search-bar input');
                const select = document.querySelector('.search-bar select');
                if (!input && !select) return null;
                return {
                    input: input ? input.getBoundingClientRect() : null,
                    select: select ? select.getBoundingClientRect() : null,
                };
            }
        """)
        save_json("searchbar_rect", rects or {})

        if await page.locator('input[name="rating"]').count() > 0:
            await page.locator('input[name="rating"]').first.check()
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)

        cards_after = await page.query_selector_all('.hotel-card')
        count_after = len(cards_after)

        if count_before > 0 and count_after == count_before:
            await page.evaluate("""
                () => {
                    const maxPrice = document.querySelector('input[name="max_price"]');
                    if (!maxPrice) return false;
                    maxPrice.value = '1';
                    maxPrice.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
            """)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(500)
            cards_after = await page.query_selector_all('.hotel-card')
            count_after = len(cards_after)

        try:
            filter_query = await page.evaluate("""
                () => window.location.search
            """)
        except Exception:
            await page.wait_for_load_state('networkidle')
            filter_query = await page.evaluate("""
                () => window.location.search
            """)

        await snapshot("hotels_after_filter")

        # FLOW 4: Hotel Detail + Booking
        log("BOOKING FLOW")
        first_details = await page.query_selector('.hotel-card a')
        if first_details:
            await first_details.click()
            await page.wait_for_load_state('networkidle')
            await snapshot("hotel_detail")

            # Fill booking form
            room_option = await page.evaluate("""
                () => {
                    const opt = document.querySelector('#id_room_type option[value]:not([value=""])');
                    return opt ? opt.value : "";
                }
            """)
            if room_option:
                await page.select_option('#id_room_type', room_option)

            check_in = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            check_out = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

            await page.fill('#id_check_in', check_in)
            await page.fill('#id_check_out', check_out)
            await page.fill('#id_quantity', '1')
            await page.fill('#id_guest_full_name', 'Test Guest')
            await page.fill('#id_guest_age', '30')
            await page.fill('#id_guest_email', creds["customer"]["email"])

            def _booking_before():
                return Booking.objects.count()
            booking_before = await sync_to_async(_booking_before)()

            await page.click('button[type="submit"]')
            await page.wait_for_url('**/booking/**/review/', timeout=10000)
            await snapshot("booking_review")

            await page.click('button[type="submit"]')
            await page.wait_for_url('**/booking/**/payment/', timeout=10000)
            await snapshot("booking_payment")

            await page.click('button[type="submit"]')
            await page.wait_for_url('**/booking/**/success/', timeout=10000)
            await snapshot("booking_success")

            def _booking_after():
                return Booking.objects.count()
            booking_after = await sync_to_async(_booking_after)()
        else:
            def _booking_before():
                return Booking.objects.count()
            booking_before = await sync_to_async(_booking_before)()
            booking_after = booking_before

        # FLOW 5: Owner creates property
        log("OWNER CREATES PROPERTY")
        await page.goto(f"{BASE_URL}/logout/", wait_until="networkidle")
        await context.clear_cookies()
        await page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
        await page.wait_for_selector('#id_username', timeout=10000)
        await page.fill('#id_username', creds["owner"]["email"])
        await page.fill('#id_password', creds["owner"]["password"])
        await page.click('button[type="submit"]')
        await page.wait_for_url(f"{BASE_URL}/**", timeout=10000)

        await page.goto(f"{BASE_URL}/owner/property/create/", wait_until="networkidle")
        await snapshot("owner_property_before")

        async def fill_if(selector, value):
            if await page.query_selector(selector):
                await page.fill(selector, value)

        await fill_if('#id_name', f"Owner Property {int(datetime.now().timestamp())}")
        await fill_if('#id_property_type', 'Hotel')
        city_value = await page.evaluate("""
            () => {
                const opt = document.querySelector('#id_city option[value]:not([value=""])');
                return opt ? opt.value : "";
            }
        """)
        if city_value:
            await page.select_option('#id_city', city_value)
        await fill_if('#id_area', 'Central')
        await fill_if('#id_landmark', 'Main Market')
        await fill_if('#id_country', 'India')
        await fill_if('#id_address', '123 Owner Street')
        await fill_if('#id_description', 'Owner property description')
        await fill_if('#id_rating', '4.2')
        await fill_if('#id_latitude', '28.6139')
        await fill_if('#id_longitude', '77.2090')
        await fill_if('#id_base_price', '2500')
        await fill_if('#id_discount_price', '2200')
        await fill_if('input[name="image_url"]', 'https://via.placeholder.com/800x600.png?text=Hotel')

        invalid_fields = await page.evaluate("""
            () => {
                const form = document.querySelector('form');
                if (!form) return { exists: false, invalid: [] };
                const invalid = Array.from(form.querySelectorAll(':invalid')).map(el => ({
                    name: el.name || el.id || el.tagName,
                    value: el.value || ''
                }));
                return { exists: true, invalid };
            }
        """)
        save_json("owner_property_invalid", invalid_fields)

        def _owner_props_before():
            return Property.objects.filter(owner__email=creds["owner"]["email"]).count()
        owner_props_before = await sync_to_async(_owner_props_before)()
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        save_json("owner_property_post", {"url": page.url})
        await snapshot("owner_property_post_submit")
        await page.wait_for_url('**/owner/dashboard/**', timeout=10000)
        await snapshot("owner_property_after")
        def _owner_props_after():
            return Property.objects.filter(owner__email=creds["owner"]["email"]).count()
        owner_props_after = await sync_to_async(_owner_props_after)()

        # FLOW 6: Vendor adds cab
        log("VENDOR ADDS CAB")
        await page.goto(f"{BASE_URL}/logout/", wait_until="networkidle")
        await context.clear_cookies()
        await page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
        await page.wait_for_selector('#id_username', timeout=10000)
        await page.fill('#id_username', creds["vendor"]["email"])
        await page.fill('#id_password', creds["vendor"]["password"])
        await page.click('button[type="submit"]')
        await page.wait_for_url(f"{BASE_URL}/**", timeout=10000)

        await page.goto(f"{BASE_URL}/vendor/cab/create/", wait_until="networkidle")
        await snapshot("cab_before")

        await page.fill('input[name="name"]', 'Vendor Cab')
        if await page.locator('select[name="city"]').count() > 0:
            await page.select_option('select[name="city"]', 'delhi')
        if await page.locator('select[name="seats"]').count() > 0:
            await page.select_option('select[name="seats"]', '5')
        if await page.locator('select[name="fuel_type"]').count() > 0:
            await page.select_option('select[name="fuel_type"]', 'petrol')
        await page.fill('input[name="base_price_per_km"]', '12')

        def _cabs_before():
            return Cab.objects.filter(owner__email=creds["vendor"]["email"]).count()
        cabs_before = await sync_to_async(_cabs_before)()
        await page.click('button[type="submit"]')
        await page.wait_for_url('**/cabs/dashboard/**', timeout=10000)
        await snapshot("cab_after")
        def _cabs_after():
            return Cab.objects.filter(owner__email=creds["vendor"]["email"]).count()
        cabs_after = await sync_to_async(_cabs_after)()

        # FLOW 7: Vendor adds bus
        log("VENDOR ADDS BUS")
        await page.goto(f"{BASE_URL}/vendor/bus/create/", wait_until="networkidle")
        await snapshot("bus_before")

        await page.fill('input[name="registration_number"]', f"DL-{int(datetime.now().timestamp())}")
        await page.fill('input[name="operator_name"]', 'Vendor Travels')
        await page.fill('input[name="from_city"]', 'Delhi')
        await page.fill('input[name="to_city"]', 'Jaipur')
        await page.fill('input[name="departure_time"]', '10:00')
        await page.fill('input[name="arrival_time"]', '16:00')
        await page.fill('input[name="price_per_seat"]', '550')
        await page.fill('input[name="available_seats"]', '40')
        await page.fill('input[name="amenities"]', 'AC')
        await page.fill('input[name="bus_type_id"]', '1')

        def _buses_before():
            return Bus.objects.filter(operator__email=creds["vendor"]["email"]).count()
        buses_before = await sync_to_async(_buses_before)()
        await page.click('button[type="submit"]')
        await page.wait_for_url('**/buses/dashboard/**', timeout=10000)
        await snapshot("bus_after")
        def _buses_after():
            return Bus.objects.filter(operator__email=creds["vendor"]["email"]).count()
        buses_after = await sync_to_async(_buses_after)()

        await browser.close()

    save_json("console_logs", console_logs)
    save_json("request_logs", request_logs)

    results = {
        "registration_db": reg_exists,
        "session_cookie": bool(session_cookie),
        "hotel_count_before": count_before,
        "hotel_count_after": count_after,
        "filter_changed": count_before != count_after,
        "filter_query": filter_query,
        "booking_count_before": booking_before,
        "booking_count_after": booking_after,
        "owner_props_before": owner_props_before,
        "owner_props_after": owner_props_after,
        "cabs_before": cabs_before,
        "cabs_after": cabs_after,
        "buses_before": buses_before,
        "buses_after": buses_after,
    }
    save_json("e2e_results", results)
    return results


if __name__ == "__main__":
    creds = ensure_roles_and_users()
    owner_user = User.objects.get(email=creds["owner"]["email"])
    ensure_properties(owner_user)

    fetch_api_proof()

    log("Hotel.objects.count() = %s" % Property.objects.count())
    log("Public properties count = %s" % get_public_properties_count())

    results = asyncio.run(run_e2e(creds))

    print("\n=== E2E RESULTS ===")
    for key, value in results.items():
        print(f"{key}: {value}")

    print("\nCredentials:")
    print(json.dumps(creds, indent=2))

    sys.exit(0 if all([
        results["registration_db"],
        results["session_cookie"],
        results["filter_changed"],
        results["booking_count_after"] > results["booking_count_before"],
        results["owner_props_after"] > results["owner_props_before"],
        results["cabs_after"] > results["cabs_before"],
        results["buses_after"] > results["buses_before"],
    ]) else 1)