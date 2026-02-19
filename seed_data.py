"""
Seed database with sample data for testing
Run: python seed_data.py
"""
import os
import django
from datetime import datetime, date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.hotels.models import Property
from buses.models import Bus, BusType
from cabs.models import Cab
from packages import models as package_models
from packages.models import Package
from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser if doesn't exist
admin_user = None
if not User.objects.filter(email='admin@zygotrip.com').exists():
    admin_user = User.objects.create_superuser(
        email='admin@zygotrip.com',
        password='admin123',
        full_name='Admin User'
    )
    print("✓ Created admin user (admin@zygotrip.com / admin123)")
else:
    admin_user = User.objects.get(email='admin@zygotrip.com')
    print("✓ Admin user already exists")

# Create a standard user for testing
if not User.objects.filter(email='user@test.com').exists():
    User.objects.create_user(
        email='user@test.com',
        password='test123',
        full_name='Test User'
    )
    print("✓ Created test user (user@test.com / test123)")

# Create sample properties (hotels)
properties_data = [
    {
        'owner': admin_user,
        'name': 'Grand Plaza Hotel',
        'property_type': 'Hotel',
        'city': 'Mumbai',
        'area': 'Andheri West',
        'country': 'India',
        'address': 'Plot 45, Andheri West, Mumbai 400053',
        'description': 'Luxury hotel with modern amenities',
        'base_price': 3500,
        'rating': 4.5,
    },
    {
        'owner': admin_user,
        'name': 'Comfort Inn Express',
        'property_type': 'Hotel',
        'city': 'Delhi',
        'area': 'Connaught Place',
        'country': 'India',
        'address': '12 Connaught Place, New Delhi 110001',
        'description': 'Comfortable stay in the heart of Delhi',
        'base_price': 2800,
        'rating': 4.0,
    },
    {
        'owner': admin_user,
        'name': 'Lake View Resort',
        'property_type': 'Resort',
        'city': 'Bangalore',
        'area': 'Whitefield',
        'country': 'India',
        'address': 'Whitefield Main Road, Bangalore 560066',
        'description': 'Scenic resort with lake views',
        'base_price': 4200,
        'rating': 4.5,
    },
    {
        'owner': admin_user,
        'name': 'Budget Stay Inn',
        'property_type': 'Hotel',
        'city': 'Pune',
        'area': 'Hinjewadi',
        'country': 'India',
        'address': 'Phase 1, Hinjewadi, Pune 411057',
        'description': 'Affordable accommodation for business travelers',
        'base_price': 1500,
        'rating': 3.5,
    },
]

for prop_data in properties_data:
    Property.objects.get_or_create(name=prop_data['name'], defaults=prop_data)
print(f"✓ Created {Property.objects.count()} properties")

# Create bus type if doesn't exist
bus_type_seater, _ = BusType.objects.get_or_create(
    name='seater',
    defaults={'base_fare': 500, 'capacity': 40}
)
bus_type_sleeper, _ = BusType.objects.get_or_create(
    name='sleeper',
    defaults={'base_fare': 800, 'capacity': 30}
)
print(f"✓ Created bus types")

# Create sample buses
buses_data = [
    {
        'operator': admin_user,
        'registration_number': 'MH01AB1234',
        'bus_type': bus_type_seater,
        'operator_name': 'RedBus Express',
        'from_city': 'Mumbai',
        'to_city': 'Pune',
        'departure_time': time(6, 0),
        'arrival_time': time(10, 0),
        'journey_date': date.today(),
        'price_per_seat': 450,
        'available_seats': 25,
    },
    {
        'operator': admin_user,
        'registration_number': 'KA02CD5678',
        'bus_type': bus_type_sleeper,
        'operator_name': 'VRL Travels',
        'from_city': 'Bangalore',
        'to_city': 'Hyderabad',
        'departure_time': time(22, 0),
        'arrival_time': time(6, 0),
        'journey_date': date.today(),
        'price_per_seat': 850,
        'available_seats': 18,
    },
    {
        'operator': admin_user,
        'registration_number': 'DL03EF9012',
        'bus_type': bus_type_seater,
        'operator_name': 'Orange Travels',
        'from_city': 'Delhi',
        'to_city': 'Jaipur',
        'departure_time': time(8, 30),
        'arrival_time': time(14, 30),
        'journey_date': date.today(),
        'price_per_seat': 600,
        'available_seats': 32,
    },
]

for bus_data in buses_data:
    Bus.objects.get_or_create(
        registration_number=bus_data['registration_number'],
        defaults=bus_data
    )
print(f"✓ Created {Bus.objects.count()} buses")

# Create sample cabs
cabs_data = [
    {
        'owner': admin_user,
        'name': 'Swift Dzire',
        'city': 'mumbai',
        'seats': 4,
        'fuel_type': 'petrol',
        'base_price_per_km': 12,
        'system_price_per_km': 15,
        'is_active': True,
    },
    {
        'owner': admin_user,
        'name': 'Innova Crysta',
        'city': 'delhi',
        'seats': 7,
        'fuel_type': 'diesel',
        'base_price_per_km': 18,
        'system_price_per_km': 21,
        'is_active': True,
    },
    {
        'owner': admin_user,
        'name': 'WagonR',
        'city': 'bangalore',
        'seats': 4,
        'fuel_type': 'petrol',
        'base_price_per_km': 10,
        'system_price_per_km': 13,
        'is_active': True,
    },
]

for cab_data in cabs_data:
    Cab.objects.get_or_create(
        name=cab_data['name'],
        city=cab_data['city'],
        defaults=cab_data
    )
print(f"✓ Created {Cab.objects.count()} cabs")

# Create package category
package_category, _ = package_models.PackageCategory.objects.get_or_create(
    name='Holiday',
    defaults={'description': 'Holiday packages', 'icon': '🏖️'}
)
print(f"✓ Created package categories")

# Create sample packages
packages_data = [
    {
        'provider': admin_user,
        'name': 'Goa Beach Paradise',
        'description': 'Explore beautiful beaches and enjoy water sports',
        'category': package_category,
        'duration_days': 5,
        'destination': 'Goa',
        'base_price': 15000,
        'rating': 4.6,
        'inclusions': 'Hotel, Transport, Meals',
        'is_active': True,
    },
    {
        'provider': admin_user,
        'name': 'Kerala Backwaters',
        'description': 'Experience serene backwaters and lush greenery',
        'category': package_category,
        'duration_days': 6,
        'destination': 'Kerala',
        'base_price': 22000,
        'rating': 4.8,
        'inclusions': 'Hotel, Transport, Meals, Houseboat',
        'is_active': True,
    },
    {
        'provider': admin_user,
        'name': 'Rajasthan Heritage Tour',
        'description': 'Visit magnificent forts and palaces',
        'category': package_category,
        'duration_days': 7,
        'destination': 'Rajasthan',
        'base_price': 28000,
        'rating': 4.7,
        'inclusions': 'Hotel, Transport, Meals, Guide',
        'is_active': True,
    },
]

for package_data in packages_data:
    Package.objects.get_or_create(
        name=package_data['name'],
        defaults=package_data
    )
print(f"✓ Created {Package.objects.count()} packages")

print("\n✅ Database seeding complete!")
print("\nSample credentials:")
print("  Admin: admin@zygotrip.com / admin123")
print("  User: user@test.com / test123")
