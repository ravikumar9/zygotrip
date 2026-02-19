import requests
import sys

try:
    print("Testing hotel search API...", flush=True)
    
    # Test hotel search API
    response = requests.get('http://127.0.0.1:8000/api/search/hotels/?city_id=1')
    print(f"Status Code: {response.status_code}", flush=True)
    
    if response.status_code != 200:
        print(f"\nERROR Response Content:\n{response.text[:1000]}", flush=True)
        sys.exit(1)
    
    data = response.json()
    
    print(f"Response keys: {list(data.keys())}", flush=True)
    print(f"Count: {data.get('count', 'N/A')}", flush=True)

    if 'results' in data:
        results = data['results']
        print(f"Number of results: {len(results)}", flush=True)
        if results:
            print(f"\nFirst result:", flush=True)
            first = results[0]
            for key, value in first.items():
                print(f"  {key}: {value}", flush=True)
    elif 'hotels' in data:
        hotels = data['hotels']
        print(f"Number of hotels: {len(hotels)}", flush=True)
        if hotels:
            print(f"\nFirst hotel:", flush=True)
            first = hotels[0]
            for key, value in first.items():
                print(f"  {key}: {value}", flush=True)
            
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()

