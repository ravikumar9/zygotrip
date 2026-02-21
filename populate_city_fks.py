"""
Populate city_id and locality_id foreign keys
Maps old text city values to core_city table
"""
import sqlite3
import sys

try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    print("✓ Connected to database\n")

    print("Populating city_id foreign keys...\n")
except Exception as e:
    print(f"ERROR connecting: {e}")
    sys.exit(1)

# Get all cities
cursor.execute("SELECT id, name FROM core_city")
cities = {name: id for id, name in cursor.fetchall()}
print(f"Found {len(cities)} cities:", list(cities.keys()))

# Get all properties with their current city text
cursor.execute("SELECT id, city_text FROM hotels_property WHERE city_text IS NOT NULL")
properties = cursor.fetchall()
print(f"\nFound {len(properties)} properties to update\n")

updated = 0
failed = []

# Define mapping rules for common city name variations
city_mapping = {
    'delhi': 'New Delhi',
    'goa': 'North Goa',  # Default Goa → North Goa
}

for prop_id, city_text in properties:
    # Try exact match first
    if city_text in cities:
        city_id = cities[city_text]
        cursor.execute("UPDATE hotels_property SET city_id = ? WHERE id = ?", (city_id, prop_id))
        print(f"✓ Property {prop_id}: '{city_text}' → city_id={city_id}")
        updated += 1
    else:
        # Try case-insensitive match
        city_lower = city_text.lower()
        matched = False
        
        # Check mapping rules first
        if city_lower in city_mapping:
            target_city = city_mapping[city_lower]
            if target_city in cities:
                city_id = cities[target_city]
                cursor.execute("UPDATE hotels_property SET city_id = ? WHERE id = ?", (city_id, prop_id))
                print(f"✓ Property {prop_id}: '{city_text}' → city_id={city_id} (mapped to: {target_city})")
                updated += 1
                matched = True
        
        # Try exact case-insensitive match
        if not matched:
            for city_name, city_id in cities.items():
                if city_name.lower() == city_lower:
                    cursor.execute("UPDATE hotels_property SET city_id = ? WHERE id = ?", (city_id, prop_id))
                    print(f"✓ Property {prop_id}: '{city_text}' → city_id={city_id} (fuzzy match: {city_name})")
                    updated += 1
                    matched = True
                    break
        
        if not matched:
            # For unmatched cities, set to NULL (we can't create data, per user directive)
            failed.append((prop_id, city_text))
            print(f"⚠️  Property {prop_id}: '{city_text}' - NO MATCH (city_id will be NULL)")

conn.commit()

print(f"\n{'='*60}")
print(f"✅ Updated {updated}/{len(properties)} properties")
if failed:
    print(f"⚠️  Failed to match {len(failed)} properties:")
    for prop_id, city_text in failed:
        print(f"   - Property {prop_id}: '{city_text}'")
else:
    print(f"✅ All properties successfully mapped!")

# Verify
cursor.execute("SELECT COUNT(*) FROM hotels_property WHERE city_id IS NOT NULL")
count = cursor.fetchone()[0]
print(f"\nVerification: {count} properties now have city_id set")

conn.close()