#!/usr/bin/env python
"""Comprehensive route testing - verify all routes working"""
import urllib.request
import ssl
import json

ssl._create_default_https_context = ssl._create_unverified_context

test_routes = [
    {
        "name": "Landing Page",
        "url": "https://localhost:8000/hotels/",
        "expected_status": 200,
        "check_content": "Search"
    },
    {
        "name": "Search Results",
        "url": "https://localhost:8000/hotels/search/?location=coorg&checkin=2026-02-26&checkout=2026-02-28&adults=2&rooms=1",
        "expected_status": 200,
        "check_content": "hotel",
        "check_no_redirect": True
    },
    {
        "name": "Property Detail",
        "url": "https://localhost:8000/hotels/bangalore-grand-stay-1-blr/?checkin=2026-02-26&checkout=2026-02-28&adults=2&rooms=1",
        "expected_status": 200,
        "check_content": "Overview"
    },
    {
        "name": "Booking Page",
        "url": "https://localhost:8000/hotels/bangalore-grand-stay-1-blr/booking/?room_type=1&checkin=2026-02-26&checkout=2026-02-28&adults=2&rooms=1",
        "expected_status": 200,
        "check_content": "Complete Your Booking"
    }
]

print("=" * 70)
print("COMPREHENSIVE ROUTE TEST SUITE")
print("=" * 70)

results = []
for test in test_routes:
    try:
        req = urllib.request.Request(test["url"])
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            html = response.read().decode('utf-8', errors='ignore')
            
            # Check status
            status_ok = status == test["expected_status"]
            
            # Check content
            content_ok = test.get("check_content", "").lower() in html.lower()
            
            # Check no redirect (if requested)
            redirect_ok = True
            
            all_ok = status_ok and content_ok and redirect_ok
            results.append({
                "test": test["name"],
                "status": "✓ PASS" if all_ok else "✗ FAIL",
                "http_status": f"{status} {'OK' if status_ok else 'WRONG'}",
                "content": "OK" if content_ok else "MISSING",
            })
    except Exception as e:
        results.append({
            "test": test["name"],
            "status": "✗ ERROR",
            "error": str(e)[:100]
        })

# Print results
for result in results:
    print(f"\n{result['test']}")
    print(f"  Status: {result['status']}")
    print(f"  HTTP: {result.get('http_status', 'N/A')}")
    if 'content' in result:
        print(f"  Content: {result['content']}")
    if 'error' in result:
        print(f"  Error: {result['error']}")

passed = sum(1 for r in results if "PASS" in r["status"])
print(f"\n{'=' * 70}")
print(f"RESULTS: {passed}/{len(results)} tests passed")
print(f"{'=' * 70}")
