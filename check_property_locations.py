"""
Check which properties have geolocation data
"""
import sqlite3
import sys

try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Get properties with their location data
    cursor.execute("""
        SELECT id, name, city_text, latitude, longitude, city_id
        FROM hotels_property
        ORDER BY id
    """)

    properties = cursor.fetchall()
    print(f"Fetched {len(properties)} properties\n", flush=True)

    with_coords = 0
    without_coords = 0
    with_city_fk = 0

    print("Properties with coordinates:")
    for prop_id, name, city, lat, lng, city_id in properties:
        if lat is not None and lng is not None:
            print(f"  ✓ [{prop_id}] {name} ({city}): lat={lat}, lng={lng}, city_id={city_id}")
            with_coords += 1
            if city_id:
                with_city_fk += 1
        else:
            without_coords += 1

    print(f"\n{'='*60}")
    print(f"With coordinates: {with_coords}")
    print(f"Without coordinates: {without_coords}")
    print(f"With city_id FK: {with_city_fk}")

    conn.close()

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

