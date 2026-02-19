import os
import sys
import django

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
    django.setup()
    print("✓ Django setup", flush=True)

    from apps.search.engine import search_engine
    print("\u2713 Imported search_engine\", flush=True)

    print("\nTesting unified search engine...\", flush=True)

    results, total = search_engine.search_hotels(query=\"Bangalore\")
    print(f\"Results count: {total}\", flush=True)
    
    if results['results']:
        print(f"\nFirst result:", flush=True)
        first = results['results'][0]
        for key, value in first.items():
            print(f"  {key}: {value}", flush=True)
    else:
        print("\n⚠ No results returned", flush=True)
        
        # Check searchable_properties directly
        from apps.search.selectors import searchable_properties
        props = searchable_properties()
        print(f"\nSearchable properties count: {props.count()}", flush=True)
        
        if props.exists():
            first_prop = props.first()
            print(f"First property: {first_prop.name}", flush=True)
            print(f"  City: {first_prop.city}", flush=True)
            print(f"  city_id: {first_prop.city_id}", flush=True)
            print(f"  city_text: {first_prop.city_text}", flush=True)
        
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()
