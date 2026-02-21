import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zygotrip_project.settings')
django.setup()

from apps.search.engine import UnifiedSearchEngine

engine = UnifiedSearchEngine()
auto = engine.autocomplete('del', limit=5)
print('Autocomplete results for "del":')
for item in auto.get('results', [])[:3]:
    print(f'  - {item.get("label", "")} ({item.get("type", "")})')
print(f'Total: {len(auto.get("results", []))} results')

# Test search
results, count = engine.search_hotels('delhi')
print(f'\nSearch results for "delhi": {count} hotels')


