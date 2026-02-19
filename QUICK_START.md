# QUICK START: Using the New Architecture

## For Frontend Developers

### REST API Endpoints

**List Properties**:
```javascript
fetch('/api/v1/properties/?city=Mumbai&min_price=1000&page=1')
  .then(res => res.json())
  .then(data => {
    console.log(data.results);  // Array of property cards
    console.log(data.pagination);  // Page info
  });
```

**Search with Ranking**:
```javascript
fetch('/api/v1/search/?q=luxury&lat=19.0760&lng=72.8777')
  .then(res => res.json())
  .then(data => {
    data.results.forEach(property => {
      console.log(`${property.name}: ${property.relevance_score}`);
    });
  });
```

**Property Detail**:
```javascript
fetch('/api/v1/properties/1/')
  .then(res => res.json())
  .then(property => {
    console.log(property.room_types);  // Array of room options
    console.log(property.badges);  // Trust signals
  });
```

## For Backend Developers

### Using SearchRankingService

```python
from apps.hotels.search import SearchRankingService
from apps.hotels.selectors import public_properties_queryset

# Get base queryset
qs = public_properties_queryset()

# Apply filters (city, price range, etc.)
filtered_qs = apply_hotel_filters(qs, request.GET)['queryset']

# Apply intelligent ranking
ranking_service = SearchRankingService(filtered_qs, dict(request.GET))
ranked_qs = ranking_service.apply_ranking()

# Results are now ordered by relevance_score
for property in ranked_qs[:10]:
    print(f"{property.name}: {property.relevance_score}")
```

### Using Trust Signal Service

```python
from apps.hotels.services.trust_signals import TrustSignalService

# Generate badges for a property
service = TrustSignalService(
    property_obj,
    context={'check_in': date(2025, 6, 15), 'user_distance_km': 1.5}
)
badges = service.generate_badges()

# Returns top 3 badges prioritized by conversion impact
# [
#   {'type': 'scarcity', 'label': 'Only 2 rooms left', 'icon': '⚠️'},
#   {'type': 'quality', 'label': 'Top Rated', 'icon': '⭐'},
#   {'type': 'flexibility', 'label': 'Free cancellation', 'icon': '✓'}
# ]
```

### Getting Property Pricing (Post-Refactor)

**DEPRECATED** ❌:
```python
price = property_obj.base_price  # Slow: queries room_types
```

**CORRECT** ✅:
```python
# In queryset (before iteration):
qs = Property.objects.annotate(
    min_room_price=Min('room_types__base_price')
)

# Then access annotation:
property_obj = qs.first()
price = property_obj.min_room_price  # Fast: already computed
```

## For Database Admins

### New Indexes (Performance Critical)

```sql
-- City filter (most common query)
CREATE INDEX hotels_prop_city_idx ON hotels_property (city_id);

-- Rating sort
CREATE INDEX hotels_prop_rating_idx ON hotels_property (rating DESC);

-- Active properties listing
CREATE INDEX hotels_prop_active_rating_idx 
ON hotels_property (is_active, rating DESC);

-- Geo queries (distance calculation)
CREATE INDEX hotels_prop_geo_idx 
ON hotels_property (latitude, longitude);
```

### Query Monitoring

```sql
-- Find slow queries (example for PostgreSQL)
SELECT 
    query, 
    mean_exec_time, 
    calls 
FROM pg_stat_statements 
WHERE query LIKE '%hotels_property%'
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

## For DevOps Engineers

### Environment Variables (Add to .env)

```bash
# Caching
CACHE_TTL_HOTEL_LIST=60
CACHE_TTL_SEARCH_RESULTS=120

# API Configuration
API_RATE_LIMIT_AUTHENTICATED=120
API_RATE_LIMIT_ANONYMOUS=30

# Performance
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

### Health Check Endpoint (Recommended Addition)

```python
# core/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Check system health"""
    try:
        # Database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Cache check
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        assert cache.get('health_check') == 'ok'
        
        return JsonResponse({'status': 'healthy', 'database': 'ok', 'cache': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

### Monitoring Queries to Watch

```python
# Check for N+1 queries
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as queries:
    # Your view code here
    pass

if len(queries) > 10:
    print(f"WARNING: {len(queries)} queries executed!")
    for q in queries:
        print(q['sql'])
```

## For QA Testers

### Critical Test Paths

1. **Property Pricing**:
   - Create property without room types → Should fail/warn
   - Create property with room type → Price displays correctly
   - Property with multiple room types → Shows minimum price

2. **API Endpoints**:
   ```bash
   # Should return 200 with JSON
   curl http://localhost:8042/api/v1/properties/
   
   # Should apply ranking
   curl "http://localhost:8042/api/v1/search/?q=hotel&lat=19.0760&lng=72.8777"
   
   # Should return property detail
   curl http://localhost:8042/api/v1/properties/1/
   ```

3. **Trust Signals**:
   - Property with high rating → "Top Rated" badge
   - Property with low inventory → "Only X rooms left" badge
   - Property with bookings_today > 3 → "Booked X times" badge

4. **Performance**:
   - Search with 1000 properties → Response < 300ms
   - API endpoints → No 500 errors
   - Database CPU → No spike after deployment

### Edge Cases to Test

```python
# Empty search results
/api/v1/properties/?city=NonexistentCity
# Expected: {"results": [], "pagination": {...}}

# Invalid page number
/api/v1/properties/?page=999999
# Expected: Returns last page, no error

# Extreme price range
/api/v1/properties/?min_price=0&max_price=999999999
# Expected: Returns all properties

# Property with no images
GET /api/v1/properties/123/
# Expected: images array empty, no crash
```

## Common Issues & Solutions

### Issue: Property prices showing as 0

**Cause**: Property has no room types  
**Fix**:
```python
from rooms.models import RoomType

RoomType.objects.create(
    property=property_obj,
    name="Standard Room",
    description="Default room",
    base_price=1000,
    max_guests=2
)
```

### Issue: API returns 500 error

**Cause**: Missing prefetch optimization  
**Fix**: Check queryset uses `select_related` and `prefetch_related`

### Issue: Search ranking not working

**Cause**: No sorting parameter provided  
**Verify**: Check `sort_by` in query params. If present, ranking is skipped.

### Issue: Migrations fail

**Cause**: Existing data references removed fields  
**Fix**: Run data migration first to migrate prices to RoomType

## Constants Reference

```python
from apps.hotels.constants import *

# Use constants instead of magic numbers:
if property.rating >= MIN_RATING_TOP_RATED:  # Not: >= 4.5
    paginator = Paginator(items, DEFAULT_PAGE_SIZE)  # Not: Paginator(items, 20)
    cache.set(key, data, CACHE_TTL_HOTEL_LIST)  # Not: cache.set(key, data, 60)
```

## Helpful Commands

```bash
# Check system health
python manage.py check

# Run migrations
python manage.py migrate

# Check for unapplied migrations
python manage.py showmigrations hotels

# Create sample data (if seed command exists)
python manage.py seed_data --properties=50

# Shell access
python manage.py shell_plus  # If django-extensions installed
python manage.py shell  # Standard shell
```

## Support

For questions or issues:
1. Check [ARCHITECTURAL_TRANSFORMATION_REPORT.md](ARCHITECTURAL_TRANSFORMATION_REPORT.md)
2. Review [CODE_QUALITY_STANDARDS.md](CODE_QUALITY_STANDARDS.md)
3. Search codebase for similar implementations
4. Check Django logs: `logs/debug.log`
