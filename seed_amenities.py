#!/usr/bin/env python
"""
Seed script for new models: Amenities, star_rating updates
Run with: python manage.py shell < seed_amenities.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.hotels.models import Amenity, Property, PropertyAmenityLink

# Create global amenities
amenity_list = [
    {'name': 'Free Wifi', 'icon': '📶', 'description': 'High-speed internet access'},
    {'name': 'Swimming Pool', 'icon': '🏊', 'description': 'Outdoor or indoor swimming pool'},
    {'name': 'Breakfast', 'icon': '🍽️', 'description': 'Free or paid breakfast'},
    {'name': 'Parking', 'icon': '🅿️', 'description': 'Free or paid parking'},
    {'name': 'Couple Friendly', 'icon': '👥', 'description': 'Welcoming to couples'},
    {'name': 'Business Center', 'icon': '💼', 'description': 'Business services available'},
    {'name': 'Gym', 'icon': '💪', 'description': 'Fitness center'},
    {'name': 'Restaurant', 'icon': '🍴', 'description': 'On-site restaurant'},
    {'name': 'Laundry', 'icon': '🧺', 'description': 'Laundry service'},
    {'name': '24-Hour Front Desk', 'icon': '🛎️', 'description': '24-hour reception'},
    {'name': 'Air Conditioning', 'icon': '❄️', 'description': 'AC in rooms'},
    {'name': 'Hot Water', 'icon': '💦', 'description': 'Hot water supply'},
]

print("[*] Creating global amenities...")
amenities_created = 0
for amenity_data in amenity_list:
    amenity, created = Amenity.objects.get_or_create(
        name=amenity_data['name'],
        defaults={
            'icon': amenity_data['icon'],
            'description': amenity_data['description']
        }
    )
    if created:
        amenities_created += 1
        print(f"  [+] Created amenity: {amenity.name}")
    else:
        print(f"  [*] Amenity already exists: {amenity.name}")

print(f"\n[OK] Created {amenities_created} new amenities")

# Update existing properties with star ratings and amenities
print("\n[*] Updating existing properties with star ratings...")
properties = Property.objects.all()
for idx, prop in enumerate(properties):
    # Set star rating if not already set
    if not hasattr(prop, 'star_rating') or prop.star_rating == 3:  # Default was 3
        prop.star_rating = min(5, 2 + (idx % 4))  # Vary between 2-5 stars
        prop.save(update_fields=['star_rating'])
        print(f"  [+] {prop.name}: {prop.star_rating} stars")

print(f"\n[OK] Updated {len(properties)} properties with star ratings")

# Assign random amenities to properties
print("\n[*] Assigning amenities to properties...")
all_amenities = list(Amenity.objects.all())
for idx, prop in enumerate(properties[:10]):  # Assign to first 10 properties
    # Assign 4-6 random amenities to each property
    amenities_to_assign = all_amenities[idx:idx+5]
    for amenity in amenities_to_assign:
        link, created = PropertyAmenityLink.objects.get_or_create(
            property=prop,
            amenity=amenity
        )
        if created:
            print(f"  [+] Assigned '{amenity.name}' to {prop.name}")

print("\n[OK] Amenity seeding complete!")