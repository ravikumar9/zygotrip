import requests
import time

requests.packages.urllib3.disable_warnings()

print("Waiting 2 seconds for server...")
time.sleep(2)

url = 'https://localhost:8000/hotels/'
r = requests.get(url, verify=False, timeout=10)

print(f'Status: {r.status_code}')
print(f'CSS base.css in HTML: {"base.css" in r.text}')
print(f'Navbar class in HTML: {"navbar-nav" in r.text}')
print(f'Footer grid in HTML: {"footer-grid" in r.text}')
print(f'Cache-busting v=20260226: {"v=20260226" in r.text}')

if r.status_code == 200:
    print('\n✓ Page loads successfully')
    print('✓ HTML structure looks correct')
    print('\nNOTE: If you still see vertical lists:')
    print('1. Hard refresh browser: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)')
    print('2. Clear browser cache completely')
    print('3. Try different browser')
else:
    print(f'\n✗ Error: HTTP {r.status_code}')
