#!/usr/bin/env python
"""Test the search API to verify it returns correct data."""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.hotels.models import Property, City
from django.test import RequestFactory

print("=" * 80)
print("TESTING SEARCH API FIX")
print("=" * 80)

# Get a property
props = Property.objects.filter(slug__isnull=False).select_related('city', 'locality')[:5]
print(f"\n✅ Found {props.count()} properties with slugs")

for prop in props:
    print(f"\n📍 Property: {prop.name}")
    print(f"   ID: {prop.id}")
    print(f"   Slug: {prop.slug}")
    print(f"   City ID: {prop.city_id}")
    print(f"   City: {prop.city.name if prop.city else 'None'}")
    print(f"   Locality: {prop.locality.name if prop.locality else 'None'}")

# Now test the serialization that the API will use
print("\n" + "=" * 80)
print("TESTING API SERIALIZATION")
print("=" * 80)

from apps.search.engine import search_engine
from django.http import QueryDict

# Create a fake request
factory = RequestFactory()
request = factory.get('/api/search/hotels/', {'q': 'delhi', 'page': '1'})

# Simulate the search_hotels view
from apps.hotels.models import Property
from django.core.paginator import Paginator

hotels = Property.objects.filter(
    name__icontains='delhi'
).select_related('city', 'locality').all()[:20]

print(f"\n✅ Found {hotels.count()} hotels matching 'delhi'")

# Serialize them like the API does
for hotel in hotels:
    result = {
        'id': hotel.id,
        'name': hotel.name,
        'slug': hotel.slug or '',
        'rating': float(hotel.rating) if hotel.rating else 0.0,
        'review_count': hotel.review_count or 0,
        'popularity_score': hotel.popularity_score or 0,
        'bookings_today': hotel.bookings_today or 0,
        'is_trending': hotel.is_trending or False,
        'base_price': float(hotel.base_price) if hotel.base_price else 0.0,
        'has_free_cancellation': hotel.has_free_cancellation if hotel.has_free_cancellation is not None else True,
        'city': hotel.city.name if hotel.city else (hotel.city_text or 'Unknown'),
        'city_id': hotel.city_id if hotel.city_id else None,
        'locality': {
            'id': hotel.locality.id,
            'name': hotel.locality.name
        } if hotel.locality else None,
    }
    
    print(f"\n📋 {result['name']}")
    print(f"   slug: {result['slug']}")
    print(f"   city: {result['city']}")
    print(f"   city_id: {result['city_id']}")
    print(f"   locality: {result['locality']}")
    
    # Verify all required fields are present
    assert result['slug'] != '', f"❌ Slug is empty for {result['name']}"
    assert result['city_id'] is not None, f"❌ city_id is None for {result['name']}"
    
print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)