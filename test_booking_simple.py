#!/usr/bin/env python
"""Simple booking test without encoding issues"""
import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

try:
    url = "https://localhost:8000/hotels/bangalore-grand-stay-1-blr/booking/?room_type=1&checkin=2026-02-26&checkout=2026-02-28&adults=2&children=0&rooms=1"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as response:
        status = response.status
        html = response.read().decode('utf-8', errors='ignore')
        print(f"Status: {status}")
        if status == 200:
            if "Complete Your Booking" in html:
                print("SUCCESS: Booking page rendering correctly!")
            else:
                print("ERROR: Page loaded but content wrong")
        else:
            print(f"ERROR: Status {status}")
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__}: {str(e)[:200]}")
