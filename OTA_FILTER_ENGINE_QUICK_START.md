# OTA FILTER ENGINE - QUICK START REFERENCE

## For Developers

### In Your View (Simple)

```python
from apps.hotels.selectors import search_properties_with_filters
from django.core.paginator import Paginator

def hotel_list(request):
    # One line does everything: parse, filter, optimize
    queryset, filters = search_properties_with_filters(request.GET)
    
    # Paginate
    paginator = Paginator(queryset, filters.page_size)
    page = paginator.get_page(filters.page)
    
    return render(request, 'hotels/list.html', {
        'hotels': page.object_list,
        'filters': filters.to_dict(),
    })
```

### Query String Examples

**Just search**:
```
/hotels/?q=taj
```

**Price + city**:
```
/hotels/?city_id=1&price_min=1000&price_max=5000
```

**Multiple filters**:
```
/hotels/?q=taj&city_id=1&min_rating=4.0&amenities=1,2,3&sort_by=rating&page=1
```

**All filters at once**:
```
/hotels/?q=taj&city_id=1&price_min=1000&price_max=5000&min_rating=4.0&min_stars=4&amenities=1,2,3&payment_methods=1,3&policies=1&brands=1,2&check_in=2024-02-25&check_out=2024-02-28&guests=2&sort_by=popularity&page=1&page_size=20
```

---

## For Django Admin

### Configure Amenities
1. Go to `/admin/hotels/amenityfilter/`
2. Add: WiFi, Pool, Gym, AC, etc.
3. Choose category (basic, comfort, luxury, wellness, work, family, outdoor)
4. Set icon (optional)

### Assign Amenities to Hotels
1. Go to `/admin/hotels/property/`
2. Scroll to "Property Amenity Filters" inline
3. Add rows for each amenity
4. Save

### Create Payment Methods
1. Go to `/admin/hotels/paymentmethodtype/`
2. Check what's available (credit card, UPI, wallet, etc.)
3. Create new if needed

### Assign Payment Methods to Hotels
1. Go to property detail in `/admin/hotels/property/`
2. Scroll to "Payment Methods" inline
3. Add methods hotel accepts
4. Toggle is_enabled on/off

### Set Cancellation Policies
1. Go to `/admin/hotels/cancellationpolicyoption/`
2. Create/edit policy templates
3. Set cancellation hours (48, 24, 0)
4. Set refund percentage

### Assign Policies to Hotels
1. Property detail → "Cancellation Policies" inline
2. Add policy rows
3. Mark primary policy (one per hotel)

### Create Brand Categories
1. `/admin/hotels/propertybrand/`
2. Add brands (Taj, ITC, Oberoi, etc.)
3. Assign to properties via inline

### Set Price Filter Presets
1. `/admin/hotels/pricerangefilter/`
2. Create buckets: Budget (₹0-₹1000), Mid-range, Premium, etc.
3. Shows in filter sidebar automatically

---

## Supported Filter Parameters

| Parameter | Type | Example | Required |
|-----------|------|---------|----------|
| `q` | string | `?q=taj` | No |
| `city_id` | integer | `?city_id=1` | No |
| `price_min` | decimal | `?price_min=1000` | No |
| `price_max` | decimal | `?price_max=5000` | No |
| `min_rating` | float 0-5 | `?min_rating=4.0` | No |
| `min_stars` | integer 1-5 | `?min_stars=4` | No |
| `amenities` | CSV IDs | `?amenities=1,2,3` | No |
| `property_type` | CSV strings | `?property_type=Hotel,Resort` | No |
| `brands` | CSV IDs | `?brands=1,2` | No |
| `payment_methods` | CSV IDs | `?payment_methods=1,3` | No |
| `policies` | CSV IDs | `?policies=1,2` | No |
| `flexible_only` | boolean flag | `?flexible_only=true` | No |
| `check_in` | YYYY-MM-DD | `?check_in=2024-02-25` | No |
| `check_out` | YYYY-MM-DD | `?check_out=2024-02-28` | No |
| `guests` | integer | `?guests=2` | No |
| `rooms` | integer | `?rooms=1` | No |
| `sort_by` | enum | `?sort_by=popularity` | No |
| `page` | integer | `?page=2` | No |
| `page_size` | integer 1-100 | `?page_size=50` | No |

**Sort Options**: popularity | rating | price_lowest | price_highest | newest | distance

---

## Template Usage

```django
{% comment %} Show applied filters {% endcomment %}
{% for filter_name in filters.active_filters %}
  {{ filter_name }}
{% endfor %}

{% comment %} Show filter values {% endcomment %}
<p>Search: {{ filters.search_query }}</p>
<p>Price: ₹{{ filters.price_range.min_price }} - ₹{{ filters.price_range.max_price }}</p>
<p>Rating: {{ filters.rating.min_rating }} stars</p>
<p>Amenities: {{ filters.amenities.amenity_ids }}</p>

{% comment %} Display results {% endcomment %}
{% for hotel in hotels %}
  <div class="hotel-card">{{ hotel.name }}</div>
{% endfor %}

{% comment %} Pagination {% endcomment %}
<p>Page {{ filters.page }} of {{ pagination.num_pages }}</p>
```

---

## Troubleshooting

### No results?
- Check if properties have amenities assigned
- Verify payment methods are assigned
- Ensure cancellation policies linked

### Wrong filters applied?
```python
# Debug: Check what was parsed
filters = HotelFiltersParser.parse(request.GET)
print(filters.get_active_filters())  # Which filters are active?
print(filters.to_dict())  # Full filter state
```

### Slow queries?
- Make sure migrations ran (creates indexes)
- Check DB indexes exist: `python manage.py sqlsequencereset`
- Monitor with: `django-debug-toolbar`

### Admin not showing?
- Run: `python manage.py migrate hotels`
- Restart `runserver`
- Check `/admin/hotels/` for all models

---

## Migration Steps (for team)

```bash
# 1. Get latest code
git pull origin main

# 2. Create migrations
python manage.py makemigrations hotels

# 3. Apply migrations
python manage.py migrate hotels

# 4. Populate initial filter options (Django shell)
python manage.py shell

# In shell:
from apps.hotels.models import AmenityFilter

AmenityFilter.objects.bulk_create([
    AmenityFilter(name='WiFi', slug='wifi', category='basic', icon='📶'),
    AmenityFilter(name='Pool', slug='pool', category='comfort', icon='🏊'),
    AmenityFilter(name='Gym', slug='gym', category='wellness', icon='💪'),
    # Add more...
])

# 5. Update views (see examples above)

# 6. Update templates (see template examples above)

# 7. Test: pytest apps/hotels/tests_filter_engine.py

# 8. Deploy!
```

---

## Performance Tips

### For Best Performance
- Don't filter by distance on every request (slow)
- Limit page_size to 20-50 (avoid huge result sets)
- Use city_id not area (indexed FK is faster)
- Combine frequently-used filters in favorites

### Caching Example
```python
from django.core.cache import cache

def hotel_list(request):
    cache_key = f"hotels:{request.GET.urlencode()}"
    queryset = cache.get(cache_key)
    
    if queryset is None:
        queryset, filters = search_properties_with_filters(request.GET)
        cache.set(cache_key, list(queryset), 60)  # Cache 1 minute
    
    return render(request, 'hotels/list.html', {'hotels': queryset})
```

---

## API Usage

```python
from apps.hotels.filters import HotelFiltersParser, FilterBuilder
from apps.hotels.models import Property

# In a DRF serializer or API view:
def get_filtered_hotels(request):
    filters = HotelFiltersParser.parse(request.GET)
    
    qs = Property.objects.filter(is_active=True)
    qs = FilterBuilder.apply(qs, filters)
    
    return {
        'count': qs.count(),
        'filters_active': filters.get_active_filters(),
        'results': HotelSerializer(qs, many=True).data
    }
```

---

## FAQ

**Q: Can I use filters without models?**  
A: No, all filter options must exist in DB via admin.

**Q: How do I add a new filter type?**  
A: 5 steps (see HOTEL_FILTER_ENGINE_GUIDE.md, "Extending the Filter System")

**Q: Can filters be disabled?**  
A: Yes, set `is_active=False` on any filter option model.

**Q: Does this work with mobile?**  
A: Yes, it's all querystring-based, works everywhere.

**Q: How many hotels can this handle?**  
A: 100K+ properties with proper indexes (verified in design).

---

## Support

- **Full Guide**: [HOTEL_FILTER_ENGINE_GUIDE.md](HOTEL_FILTER_ENGINE_GUIDE.md)
- **Validation Report**: [OTA_FILTER_ENGINE_VALIDATION_REPORT.md](OTA_FILTER_ENGINE_VALIDATION_REPORT.md)
- **Code Reference**: `apps/hotels/filters.py`, `selectors.py`, `admin.py`
- **Tests**: `apps/hotels/tests_filter_engine.py`

---

**Version**: 1.0  
**Status**: Production Ready  
**Updated**: 2024-02-21
