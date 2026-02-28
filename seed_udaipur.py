"""Seed test data for hotel listings"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip.settings')
sys.path.insert(0, '/c/Users/ravi9/Downloads/Zy/zygotrip')
django.setup()

from apps.hotels.models import Property, PropertyImage, Room, Amenity, RoomAmenity
from django.utils import timezone

# Create Udaipur property
property_data = {
    'name': 'Grand Stay Udaipur',
    'slug': 'udaipur-grand-stay-5-udr',
    'city': 'Udaipur',
    'area': 'City Palace',
    'address': '123 Palace Road',
    'country': 'India',
    'latitude': 24.5854,
    'longitude': 73.6864,
    'description': 'Luxury hotel with lake views',
    'star_category': 5,
    'property_type': 'Hotel',
    'check_in_time': '2:00 PM',
    'check_out_time': '11:00 AM',
    'rating': 4.5,
    'review_count': 250,
    'base_price': 5000,
    'min_price': 4500,
    'max_guests': 4,
    'rooms_count': 50,
    'amenities_count': 15,
    'has_free_cancellation': True,
    'status': 'approved',
    'is_active': True,
}

# Create the property
try:
    prop = Property.objects.create(**property_data)
    print(f"Created property: {prop.name} ({prop.slug})")
    
    # Create a room
    room = Room.objects.create(
        property=prop,
        name='Deluxe Room',
        bed_type='King Bed',
        room_size_sqm=40,
        max_guests=2,
        base_price=5000,
        is_available=True,
    )
    print(f"Created room: {room.name}")
    
    print("\n✓ Udaipur property created successfully!")
except Exception as e:
    print(f"✗ Error: {e}")
