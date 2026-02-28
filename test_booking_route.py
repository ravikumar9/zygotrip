#!/usr/bin/env python
"""Test booking route"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client
from apps.hotels.models import Property
from apps.rooms.models import RoomType

client = Client()

# Get a property and room
prop = Property.objects.first()
if prop:
    room = RoomType.objects.filter(property=prop).first()
    if room:
        print(f"Testing property: {prop.slug}, room: {room.id}")
        
        # Test booking route
        url = f'/hotels/{prop.slug}/booking/?room_type={room.id}&checkin=2026-02-26&checkout=2026-02-28&adults=2&children=0&rooms=1'
        print(f"URL: {url}")
        response = client.get(url)
        print(f"Response status: {response.status_code}")
        print(f"Response content length: {len(response.content)}")
        
        if response.status_code != 200:
            print(f"Response content (first 500 chars):\n{response.content[:500]}")
    else:
        print(f"No rooms found for property {prop.slug}")
else:
    print("No properties found in database")
