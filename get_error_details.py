import requests
import sys

try:
    print("Fetching error...", flush=True)
    response = requests.get('http://127.0.0.1:8000/api/search/hotels/?city_id=1')
    print(f"Status: {response.status_code}", flush=True)

    # Save full error page
    with open('debug_hotel_api_error.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    print("Error page saved to debug_hotel_api_error.html", flush=True)

    # Try to extract just the exception line
    if 'Exception Type' in response.text:
        import re
        exc_type = re.search(r'Exception Type:.*?<td>(.*?)</td>', response.text)
        exc_value = re.search(r'Exception Value:.*?<pre class="exception_value">(.*?)</pre>', response.text, re.DOTALL)
        exc_location = re.search(r'Exception Location:.*?<td>(.*?)</td>', response.text)
        
        if exc_type:
            print(f"\nException Type: {exc_type.group(1)}", flush=True)
        if exc_value:
            print(f"Exception Value: {exc_value.group(1).strip()}", flush=True)
        if exc_location:
            print(f"Exception Location: {exc_location.group(1)}", flush=True)
    else:
        print("Could not find exception details", flush=True)
        
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()

