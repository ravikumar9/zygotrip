#!/usr/bin/env python
import requests
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'zygotrip_project.settings'
import django
django.setup()

from apps.hotels.models import Property
from apps.rooms.models import RoomType

requests.packages.urllib3.disable_warnings()

prop = Property.objects.first()
room = RoomType.objects.filter(property=prop).first()

print(f'Property: {prop.slug}')
print(f'Room: {room.id}')

# Test with running server
resp = requests.get(f'https://127.0.0.1:8000/hotels/{prop.slug}/booking/?room_type={room.id}&checkin=2026-02-26&checkout=2026-02-28&adults=2&children=0&rooms=1', verify=False)
print(f'Status: {resp.status_code}')
print(f'URL: {resp.url}')

# Show first 200 chars of content
content_preview = resp.text[:200]
print(f'Content preview: {content_preview}')
