#!/usr/bin/env python
"""Debug booking route to find the actual exception"""

import os
import django
import requests
from urllib3.exceptions import InsecureRequestWarning

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Test data
property_slug = "bangalore-grand-stay-1-blr"
room_type_id = 1
checkin = "2026-02-26"
checkout = "2026-02-28"
adults = 2
children = 0
rooms = 1

# Build URL
url = f"https://localhost:8000/hotels/{property_slug}/booking/?room_type={room_type_id}&checkin={checkin}&checkout={checkout}&adults={adults}&children={children}&rooms={rooms}"

print(f"Testing URL: {url}\n")

try:
    response = requests.get(url, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)} bytes\n")
    
    if response.status_code >= 400:
        print("ERROR RESPONSE:")
        print(response.text[:2000])
    else:
        print("SUCCESS:")
        print(response.text[:500])
        
except Exception as e:
    print(f"Request Error: {e}")
