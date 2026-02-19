"""
Direct test of search API without HTTP
"""
import os
import sys
import django

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
    django.setup()
    print("✓ Django setup complete", flush=True)

    from apps.search.engine import search_engine
    print("✓ Imported search_engine", flush=True)

    print("Testing unified search engine...", flush=True)

    # Test search
    results, total = search_engine.search_hotels(city='Bangalore')

    print(f"Found {total} hotels", flush=True)

    # Try to serialize first hotel
    if results:
        hotel = results[0]
        print(f"\nFirst hotel: {hotel.name}", flush=True)
        print(f"  ID: {hotel.id}", flush=True)
        print(f"  City: {hotel.city}", flush=True)
        print(f"  city_id: {hotel.city_id}", flush=True)
        print(f"  city_text: {hotel.city_text}", flush=True)
        print(f"  Latitude: {hotel.latitude} (type: {type(hotel.latitude)})", flush=True)
        print(f"  Longitude: {hotel.longitude} (type: {type(hotel.longitude)})", flush=True)
        print(f"  Rating: {hotel.rating} (type: {type(hotel.rating)})", flush=True)
        print(f"  Base price: {hotel.base_price} (type: {type(hotel.base_price)})", flush=True)
        print(f"  Review count: {hotel.review_count}", flush=True)
        print(f"  Popularity score: {hotel.popularity_score}", flush=True)
        print(f"  Bookings today: {hotel.bookings_today}", flush=True)
        print(f"  Is trending: {hotel.is_trending}", flush=True)
        print(f"  Has free cancellation: {hotel.has_free_cancellation}", flush=True)
        
        # Try to convert each field
        print("\nTrying to serialize...", flush=True)
        try:
            rating = float(hotel.rating) if hotel.rating else 0.0
            print(f"✓ Rating: {rating}", flush=True)
        except Exception as e:
            print(f"✗ Rating failed: {e}", flush=True)
        
        try:
            price = float(hotel.base_price) if hotel.base_price else 0.0
            print(f"✓ Price: {price}", flush=True)
        except Exception as e:
            print(f"✗ Price failed: {e}", flush=True)
        
        # Test coordinates
        try:
            if hotel.latitude and hotel.longitude:
                lat = float(hotel.latitude)
                lng = float(hotel.longitude)
                print(f"✓ Coordinates: ({lat}, {lng})", flush=True)
            else:
                print(f"⚠ Coordinates missing", flush=True)
        except Exception as e:
            print(f"✗ Coordinates failed: {e}", flush=True)

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()

