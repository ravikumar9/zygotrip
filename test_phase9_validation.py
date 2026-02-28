#!/usr/bin/env python
"""Phase 9: Comprehensive OTA Platform Validation Script"""

import asyncio
from playwright.async_api import async_playwright

async def test_comprehensive_validation():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        results = {
            'routing': [],
            'navigation': [],
            'layouts': [],
            'content': [],
            'functionality': []
        }
        
        try:
            base_url = "https://127.0.0.1:8000"
            
            # ===== PHASE 9.1: ROUTING VALIDATION =====
            print("\n" + "="*60)
            print("PHASE 9.1: ROUTING VALIDATION")
            print("="*60)
            
            test_routes = [
                ("Hotels", "/hotels/", 200),
                ("Buses", "/buses/", 200),
                ("Cabs", "/cabs/", 200),
                ("Packages", "/packages/", 200),
                ("Flights", "/flights/", 200),
                ("Trains", "/trains/", 200),
                ("Home", "/", 200),
                ("Login", "/login/", 200),
                ("Register", "/register/", 200),
                ("Dashboard", "/dashboard/", 200),
            ]
            
            for name, route, expected_status in test_routes:
                try:
                    response = await page.goto(f"{base_url}{route}")
                    status = response.status if response else None
                    success = status == expected_status
                    results['routing'].append({
                        'route': name,
                        'path': route,
                        'status': status,
                        'expected': expected_status,
                        'passed': success
                    })
                    print(f"✓" if success else "✗", f"{name} ({route}): {status}")
                except Exception as e:
                    results['routing'].append({
                        'route': name,
                        'path': route,
                        'error': str(e),
                        'passed': False
                    })
                    print(f"✗ {name} ({route}): {e}")
            
            # ===== PHASE 9.2: NAVIGATION VALIDATION =====
            print("\n" + "="*60)
            print("PHASE 9.2: NAVIGATION VALIDATION")
            print("="*60)
            
            await page.goto(f"{base_url}/")
            
            nav_links = [
                ("Home", "core:home"),
                ("Hotels", "hotels:list"),
                ("Buses", "buses:list"),
                ("Cabs", "cabs:list"),
                ("Packages", "packages:list"),
            ]
            
            for name, expected_pattern in nav_links:
                try:
                    link = await page.locator(f"a:has-text('{name}')").first
                    href = await link.get_attribute("href") if link else None
                    has_hardcoded = href and href.startswith("/") if href else False
                    uses_url_tag = href and "{% url" not in str(href)  # Can't see {% %} in rendered HTML
                    success = href is not None and not has_hardcoded
                    results['navigation'].append({
                        'link': name,
                        'href': href,
                        'uses_url_reversal': success,
                        'passed': success
                    })
                    print(f"✓" if success else "✗", f"{name}: {href}")
                except Exception as e:
                    results['navigation'].append({
                        'link': name,
                        'error': str(e),
                        'passed': False
                    })
                    print(f"✗ {name}: {e}")
            
            # ===== PHASE 9.3: HOTEL LISTING LAYOUT =====
            print("\n" + "="*60)
            print("PHASE 9.3: HOTEL LISTING LAYOUT")
            print("="*60)
            
            await page.goto(f"{base_url}/hotels/")
            
            layout_checks = [
                ("Max-width container", ".max-w-7xl"),
                ("Grid layout", ".lg\\:grid"),
                ("Sticky sidebar", ".sticky"),
                ("Sort bar", "#sort-bar"),
                ("Filter section", "#filters-sidebar"),
                ("Results area", "article.hotel-card"),
            ]
            
            for check_name, selector in layout_checks:
                try:
                    element = await page.query_selector(selector)
                    success = element is not None
                    results['layouts'].append({
                        'check': check_name,
                        'selector': selector,
                        'found': success
                    })
                    print(f"✓" if success else "✗", f"{check_name}: {success}")
                except Exception as e:
                    results['layouts'].append({
                        'check': check_name,
                        'error': str(e),
                        'passed': False
                    })
                    print(f"✗ {check_name}: {e}")
            
            # ===== PHASE 9.4: CONTENT & NO HARDCODED DEFAULTS =====
            print("\n" + "="*60)
            print("PHASE 9.4: CONTENT & NO HARDCODED DEFAULTS")
            print("="*60)
            
            # Check no hardcoded "Madikeri"
            madikeri_count = await page.locator("text=Madikeri").count()
            no_default_city = madikeri_count == 0
            results['content'].append({
                'check': 'No hardcoded Madikeri default',
                'found_count': madikeri_count,
                'passed': no_default_city
            })
            print(f"✓" if no_default_city else "✗", f"Hardcoded Madikeri: {madikeri_count} (should be 0)")
            
            # Check hero search exists
            hero = await page.query_selector(".hero--search")
            has_hero = hero is not None
            results['content'].append({
                'check': 'Hero search section',
                'found': has_hero
            })
            print(f"✓" if has_hero else "✗", f"Hero search section: {has_hero}")
            
            # Check for "Where to" label
            where_to = await page.locator("label:has-text('Where to')").count()
            has_where_to = where_to > 0
            results['content'].append({
                'check': 'Where to label',
                'found': has_where_to
            })
            print(f"✓" if has_where_to else "✗", f"'Where to' label: {has_where_to}")
            
            # ===== PHASE 9.5: BUS PAGE VALIDATION =====
            print("\n" + "="*60)
            print("PHASE 9.5: BUS PAGE VALIDATION")
            print("="*60)
            
            await page.goto(f"{base_url}/buses/")
            
            buses_checks = [
                ("Hero section", ".hero--search"),
                ("From City field", "input[name='from_city']"),
                ("To City field", "input[name='to_city']"),
                ("Date field", "input[name='date']"),
                ("Search button", "button:has-text('Search')"),
                ("Empty state message", "text=Start searching"),
            ]
            
            for check_name, selector in buses_checks:
                try:
                    element = await page.query_selector(selector) if not selector.startswith("text=") else await page.locator(selector).first
                    success = element is not None if not selector.startswith("text=") else await page.locator(selector.replace("text=", "")).count() > 0
                    results['content'].append({
                        'page': 'Buses',
                        'check': check_name,
                        'found': success
                    })
                    print(f"✓" if success else "✗", f"{check_name}: {success}")
                except Exception as e:
                    results['content'].append({
                        'page': 'Buses',
                        'check': check_name,
                        'error': str(e),
                        'passed': False
                    })
                    print(f"✗ {check_name}: {e}")
            
            # ===== PHASE 9.6: CAB PAGE VALIDATION =====
            print("\n" + "="*60)
            print("PHASE 9.6: CAB PAGE VALIDATION")
            print("="*60)
            
            await page.goto(f"{base_url}/cabs/")
            
            cabs_checks = [
                ("Hero section", ".hero--search"),
                ("Pickup field", "input[name='pickup']"),
                ("Dropoff field", "input[name='dropoff']"),
                ("Date field", "input[name='date']"),
                ("Search button", "button:has-text('Search')"),
                ("Cab type cards", "text=Hatchback|text=Sedan|text=SUV"),
            ]
            
            for check_name, selector in cabs_checks:
                try:
                    if "|" in selector:
                        elements = selector.split("|")
                        success = any(await page.locator(s.replace("text=", "")).count() > 0 for s in elements)
                    elif selector.startswith("text="):
                        success = await page.locator(selector.replace("text=", "")).count() > 0
                    else:
                        success = await page.query_selector(selector) is not None
                    
                    results['content'].append({
                        'page': 'Cabs',
                        'check': check_name,
                        'found': success
                    })
                    print(f"✓" if success else "✗", f"{check_name}: {success}")
                except Exception as e:
                    results['content'].append({
                        'page': 'Cabs',
                        'check': check_name,
                        'error': str(e),
                        'passed': False
                    })
                    print(f"✗ {check_name}: {e}")
            
            # ===== PHASE 9.7: PACKAGES PAGE VALIDATION =====
            print("\n" + "="*60)
            print("PHASE 9.7: PACKAGES PAGE VALIDATION")
            print("="*60)
            
            await page.goto(f"{base_url}/packages/")
            
            packages_checks = [
                ("Hero section", ".hero--search"),
                ("Package cards", ".rounded-2xl"),
                ("Popular Destinations text", "text=Popular Destinations"),
                ("Package pricing", "text=per person"),
            ]
            
            for check_name, selector in packages_checks:
                try:
                    if selector.startswith("text="):
                        success = await page.locator(selector.replace("text=", "")).count() > 0
                    else:
                        element = await page.query_selector(selector)
                        success = element is not None
                    
                    results['content'].append({
                        'page': 'Packages',
                        'check': check_name,
                        'found': success
                    })
                    print(f"✓" if success else "✗", f"{check_name}: {success}")
                except Exception as e:
                    results['content'].append({
                        'page': 'Packages',
                        'check': check_name,
                        'error': str(e),
                        'passed': False
                    })
                    print(f"✗ {check_name}: {e}")
            
            # ===== SUMMARY =====
            print("\n" + "="*60)
            print("VALIDATION SUMMARY")
            print("="*60)
            
            total_checks = sum(len(v) for v in results.values())
            passed_checks = sum(
                sum(1 for item in v if item.get('passed', item.get('found', item.get('status') == item.get('expected', 200))))
                for v in results.values()
            )
            
            for category, items in results.items():
                category_passed = sum(1 for item in items if item.get('passed', item.get('found', False)))
                print(f"\n{category.upper()}: {category_passed}/{len(items)} passed")
            
            print(f"\n{'='*60}")
            print(f"OVERALL: {passed_checks}/{total_checks} checks passed")
            print(f"SUCCESS RATE: {(passed_checks/total_checks*100):.1f}%")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_validation())
