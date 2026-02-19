# PHASE 8-9 INTEGRATION GUIDE
## Production OTA Architecture - Final Integration Steps

> **Current Status**: Foundation complete (100%), Integration pending (0%), OTA Features missing (0%)
> **Overall Progress**: 70% Complete

---

## PART A: CURRENT STATE ANALYSIS

### ✅ What's Been Built (Production Ready)

#### Layer 1: ViewModels (3 classes, 400 lines)
```
apps/hotels/viewmodels/
  ├── __init__.py
  ├── hotel_card_vm.py       → HotelCardVM (45 properties)
  ├── hotel_detail_vm.py     → HotelDetailVM + RoomTypeVM, ReviewVM
  └── filters_vm.py          → FiltersVM + FilterOptionVM
```

**HotelCardVM Properties** (View these in `hotel_card_vm.py`):
- Identity: `id`, `name`, `slug`, `city`, `area`, `latitude`, `longitude`
- Pricing: `price_current`, `price_original`, `discount_percent`, `savings_amount`
- Ratings: `rating_value`, `rating_count`, `rating_tier`
- Analytics: `rooms_left`, `booked_today`, `viewers_now` ← PHASE 9 signals
- Trust: `is_verified`, `is_best_rating`, `is_lowest_price`, `is_best_deal`, `is_best_value` ← PHASE 9
- UI: `image_url`, `image_alt`, `amenities` (list), `free_cancellation`, `pay_at_hotel`
- Methods: `has_discount()`, `is_urgent()`, `is_hot()`, `rating_stars()`, `availability_status()`

#### Layer 2: Search Engine (200 lines)
```
apps/hotels/search.py
  ├── ProductionSearchEngine       → Multi-field text scoring (10-point scale)
  └── FilterAggregator            → Dynamic filter generation from data
```

#### Layer 3: View Logic (200 lines)
```
apps/search/views_production.py
  ├── build_hotel_card_vm()       → ORM → ViewModel transformation
  ├── search_list()               → Main search endpoint
  ├── search_autocomplete()       → Typeahead suggestions
  └── search_api()                → Public JSON API
```

#### Layer 4: Utilities
```
apps/hotels/image_optimization.py → ImageOptimizer + ImageTemplate
apps/hotels/maps.py              → Google Maps async callback
```

#### Layer 5: Design System
```
static/css/tokens.css            → 150+ tokens (OVERHAUL: comprehensive system)
static/css/hotel-card.css        → 3-column grid layout (280 lines)
```

---

## PART B: CRITICAL INTEGRATION TASKS (PHASE 8)

### ✅ Task 8.1: Update Search URLs

**File**: `apps/search/urls.py`

**Current State**:
```python
from .views import search
from .api_views import autocomplete_locations, search_hotels
...
urlpatterns = [
    path("", search, name="list"),      # ← Still pointing to OLD search view
    path("api/", search_hotels, name="api_search"),
]
```

**Action Required**: Update to use NEW production search view:

```python
from django.urls import path
from .views_production import search_list, search_autocomplete, search_api
from .api_views import autocomplete_locations, search_hotels

app_name = "search"

urlpatterns = [
    # Main search page
    path("", search_list, name="list"),  # ← NOW points to views_production.search_list
    
    # Autocomplete API
    path("autocomplete/", search_autocomplete, name="autocomplete"),
    
    # Public API
    path("api/", search_api, name="api_search"),
    
    # Legacy (keep for backward compatibility)
    path("legacy_api/", search_hotels, name="legacy_api"),
]
```

**Why**: 
- OLD `search` view uses raw ORM objects + toy-level search
- NEW `search_list` uses ProductionSearchEngine + ViewModels + dynamic filters
- This is the PRIMARY INTEGRATION POINT

**Validation**: After change, test: `GET /search/?q=mumbai`

---

### ✅ Task 8.2: Update Search Template (`search/list.html`)

**File**: `templates/search/list.html`

**Current State** (assumes old structure):
```html
{% extends "base.html" %}
{% block content %}
  <div class="search-results">
    {% for property in properties %}  {# ← Iterating ORM objects #}
      <div class="hotel-item">
        <h3>{{ property.name }}</h3>
        <p>{{ property.base_price }}</p>  {# ← Accessing ORM attributes #}
      </div>
    {% endfor %}
  </div>
{% endblock %}
```

**Action Required**: Refactor to use HotelCardVM:

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
  <div class="search-page">
    {# FILTERS SECTION #}
    <aside class="search-filters">
      <h3 class="heading-lg">Filters</h3>
      
      {# Price Range Filter #}
      <div class="filter-section">
        <h4 class="heading-sm">Price Per Night</h4>
        <form method="get" class="filter-form">
          <label>
            Min: <input type="number" name="min_price" 
                   value="{{ filters.price.min_current }}" 
                   class="input-small" />
          </label>
          <label>
            Max: <input type="number" name="max_price" 
                   value="{{ filters.price.max_current }}" 
                   class="input-small" />
          </label>
          <button type="submit" class="btn btn-primary btn-sm">Apply</button>
        </form>
      </div>
      
      {# Rating Filter #}
      {% if filters.ratings %}
        <div class="filter-section">
          <h4 class="heading-sm">Rating</h4>
          <ul class="filter-options">
            {% for option in filters.ratings %}
              <li>
                <label>
                  <input type="checkbox" name="rating" value="{{ option.value }}"
                    {% if option.is_selected %}checked{% endif %} />
                  <span>{{ option.label }}</span>
                  <span class="filter-count">{{ option.count }}</span>
                </label>
              </li>
            {% endfor %}
          </ul>
        </div>
      {% endif %}
      
      {# Amenities Filter #}
      {% if filters.amenities %}
        <div class="filter-section">
          <h4 class="heading-sm">Amenities</h4>
          <ul class="filter-options">
            {% for option in filters.amenities %}
              <li>
                <label>
                  <input type="checkbox" name="amenity" value="{{ option.value }}"
                    {% if option.is_selected %}checked{% endif %} />
                  <span>{{ option.label }}</span>
                </label>
              </li>
            {% endfor %}
          </ul>
        </div>
      {% endif %}
    </aside>

    {# RESULTS SECTION #}
    <main class="search-results">
      <header class="results-header">
        <h1 class="heading-3xl">
          {% if query %}
            Search Results for "{{ query }}"
          {% else %}
            Browse Hotels
          {% endif %}
        </h1>
        <p class="text-secondary">{{ total_count }} properties found</p>
      </header>

      {# HOTEL CARDS GRID #}
      {% if results %}
        <div class="hotel-cards-grid">
          {% for hotel in results %}  {# ← NOW iterating HotelCardVM objects (not ORM) #}
            <div class="hotel-card">
              
              {# IMAGE COLUMN #}
              <div class="hotel-card-image-wrapper">
                <img 
                  src="{{ hotel.image_url }}" 
                  alt="{{ hotel.image_alt }}"
                  loading="lazy"
                  decoding="async"
                  width="260"
                  height="195"
                  class="hotel-card-image"
                  onerror="this.src='{% static 'img/placeholder-hotel.jpg' %}'" />
                
                {# BADGES OVERLAY #}
                {% if hotel.is_verified %}
                  <span class="hotel-card-badge badge-verified">
                    <i class="icon-verified"></i> Verified
                  </span>
                {% endif %}
                {% if hotel.is_best_deal %}
                  <span class="hotel-card-badge badge-best-deal">Best Deal</span>
                {% endif %}
              </div>

              {# INFO COLUMN #}
              <div class="hotel-card-info">
                <div class="hotel-card-header">
                  <h3 class="heading-md">
                    <a href="{% url 'hotels:detail' hotel.slug %}">{{ hotel.name }}</a>
                  </h3>
                </div>

                <div class="hotel-card-rating">
                  {% if hotel.rating_value %}
                    <div class="rating-badge">
                      <span class="rating-value">{{ hotel.rating_value }}</span>
                      <span class="rating-stars">{{ hotel.rating_stars }}</span>
                    </div>
                    <span class="rating-count text-secondary">({{ hotel.rating_count }} reviews)</span>
                  {% endif %}
                </div>

                <div class="hotel-card-location text-secondary">
                  <span>{{ hotel.area }}, {{ hotel.city }}</span>
                </div>

                {# AMENITIES TAGS #}
                {% if hotel.amenities %}
                  <ul class="hotel-card-amenities">
                    {% for amenity in hotel.amenities|slice:":3" %}
                      <li class="amenity-tag">{{ amenity }}</li>
                    {% endfor %}
                    {% if hotel.amenities|length > 3 %}
                      <li class="amenity-tag more">+{{ hotel.amenities|length|add:"-3" }} more</li>
                    {% endif %}
                  </ul>
                {% endif %}

                {# POLICIES #}
                <div class="hotel-card-policies text-xs text-secondary">
                  {% if hotel.free_cancellation %}
                    <span class="policy-badge">Free Cancellation</span>
                  {% endif %}
                  {% if hotel.pay_at_hotel %}
                    <span class="policy-badge">Pay at Hotel</span>
                  {% endif %}
                </div>
              </div>

              {# PRICE COLUMN #}
              <div class="hotel-card-price">
                {% if hotel.price_original and hotel.has_discount %}
                  <p class="price-original">₹{{ hotel.price_original|floatformat:0 }}</p>
                {% endif %}

                <p class="price-current">₹{{ hotel.price_current|floatformat:0 }}</p>
                <p class="price-label">per night</p>

                {% if hotel.has_discount %}
                  <span class="discount-badge">-{{ hotel.discount_percent }}%</span>
                {% endif %}

                {# CONVERSION SIGNALS (PHASE 9) #}
                {% if hotel.booked_today > 0 %}
                  <div class="conversion-signal urgency">
                    <i class="icon-fire"></i>
                    <span>{{ hotel.booked_today }} booked today</span>
                  </div>
                {% endif %}

                {% if hotel.viewers_now > 0 %}
                  <div class="conversion-signal attention">
                    <i class="icon-eye"></i>
                    <span>{{ hotel.viewers_now }} viewing now</span>
                  </div>
                {% endif %}

                {# CTA BUTTON #}
                <a href="{% url 'hotels:detail' hotel.slug %}" class="btn btn-primary btn-block">
                  View Details
                </a>
              </div>
            </div>
          {% endfor %}
        </div>

        {# PAGINATION #}
        {% if page_obj.has_other_pages %}
          <nav class="pagination">
            {% if page_obj.has_previous %}
              <a href="?page=1" class="btn btn-outline">First</a>
              <a href="?page={{ page_obj.previous_page_number }}" class="btn btn-outline">Previous</a>
            {% endif %}

            <span class="page-info">
              Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}
            </span>

            {% if page_obj.has_next %}
              <a href="?page={{ page_obj.next_page_number }}" class="btn btn-outline">Next</a>
              <a href="?page={{ page_obj.paginator.num_pages }}" class="btn btn-outline">Last</a>
            {% endif %}
          </nav>
        {% endif %}

      {% else %}
        <div class="empty-state">
          <h2 class="heading-lg">No properties found</h2>
          <p class="text-secondary">Try adjusting your filters or search terms</p>
        </div>
      {% endif %}
    </main>
  </div>

  <style>
    .search-page {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: var(--space-8);
      padding: var(--space-6);
      max-width: var(--container-max);
      margin: 0 auto;
    }

    .hotel-cards-grid {
      display: flex;
      flex-direction: column;
      gap: var(--space-6);
    }

    @media (max-width: 1024px) {
      .search-page {
        grid-template-columns: 1fr;
      }
      .search-filters {
        display: none;
      }
    }
  </style>
{% endblock %}
```

**Key Changes**:
1. ✅ Iterate `results` (HotelCardVM objects) not `properties` (ORM)
2. ✅ Access `hotel.price_current` not `property.base_price`
3. ✅ Access `hotel.image_url` not `property.images.first().url`
4. ✅ Use `filters` from FiltersVM (server-driven, not hardcoded)
5. ✅ Include PHASE 9 signals: `booked_today`, `viewers_now`, badges
6. ✅ Use token classes: `heading-lg`, `text-secondary`, `btn-primary`

**Validation**: After update, test search page - should show hotel cards with prices, ratings, amenities

---

### ✅ Task 8.3: Update Hotel Detail View

**File**: `apps/hotels/views.py` (detail view)

**Current State** (example):
```python
def hotel_detail(request, slug):
    hotel = get_object_or_404(Property, slug=slug)
    return render(request, 'hotels/detail.html', {'hotel': hotel})  # ← Passing ORM object
```

**Action Required**: Transform to use HotelDetailVM:

```python
from django.shortcuts import render, get_object_or_404
from .models import Property
from .viewmodels import HotelDetailVM

def hotel_detail(request, slug):
    """Display hotel detail page with ViewModel"""
    property_obj = get_object_or_404(
        Property.objects.select_related(
            'city', 'owner', 'pricing'
        ).prefetch_related(
            'images', 'amenities_set', 'reviews'
        ),
        slug=slug
    )
    
    # Transform ORM → ViewModel
    hotel_vm = HotelDetailVM.from_orm(property_obj)
    
    # Add context
    context = {
        'hotel': hotel_vm,
        'gallery_images': hotel_vm.gallery_images,
        'average_rating': hotel_vm.average_rating,
    }
    
    return render(request, 'hotels/detail.html', context)
```

**Why**:
- Ensures detail page uses same architecture as search
- Guarantees query optimization (select_related + prefetch_related)
- All templates receive VMs, never ORM objects

---

### ✅ Task 8.4: Update Hotel Detail Template

**File**: `templates/hotels/detail.html`

**Key Changes**:
```html
{# OLD #}
<h1>{{ hotel.name }}</h1>
<p>{{ hotel.base_price }}</p>
<img src="{{ hotel.images.first.url }}" />

{# NEW #}
<h1>{{ hotel.name }}</h1>
<p>₹{{ hotel.price_current }}</p>
<img src="{{ hotel.primary_image.url }}" loading="lazy" />
```

**Why**:
- Consistent property naming across all pages
- Guaranteed data availability (VM validation ensures all properties exist)
- All templates use same pattern

---

### ✅ Task 8.5: Performance Optimization - Query Verification

**File**: `apps/hotels/views.py` (or new `apps/hotels/performance.py`)

**Action Required**: Add caching and query monitoring:

```python
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition
from django.core.cache import cache
from .search import ProductionSearchEngine

# Cache search results for 6 hours
@cache_page(60 * 60 * 6)  # 6 hours
def search_list(request):
    """Main search endpoint with caching"""
    query = request.GET.get('q', '').strip()
    
    # Check cache
    cache_key = f'search:{query}'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Search
    search_engine = ProductionSearchEngine(Property)
    results = search_engine.search(
        query=query,
        min_price=request.GET.get('min_price'),
        max_price=request.GET.get('max_price'),
    )
    
    # Convert to VMs
    hotel_vms = [build_hotel_card_vm(prop) for prop in results]
    
    # Cache result
    cache.set(cache_key, hotel_vms, 60 * 60 * 6)
    
    return render(request, 'search/list.html', {
        'results': hotel_vms,
    })
```

**Why**:
- Reduces database queries
- Improves response time
- Decreases server load

---

### ✅ Task 8.6: Fragment Caching for Hotel Cards

**File**: `templates/partials/hotel_card.html` (if using partial includes)

```html
{% load cache %}

{% cache 3600 hotel_card hotel.id %}
  <div class="hotel-card">
    {# Card content here #}
  </div>
{% endcache %}
```

**Why**:
- Caches each card individually (1 hour TTL)
- Huge performance boost for large result sets
- Cache invalidates per-hotel (not all-or-nothing)

---

## PART C: PHASE 9 IMPLEMENTATION (OTA FEATURES)

### 🔄 Task 9.1: Enhance HotelCardVM with Trust Elements

**File**: `apps/hotels/viewmodels/hotel_card_vm.py`

**Status**: Properties already defined, just need computation

**Verification** (in `hotel_card_vm.py`):
```python
@dataclass
class HotelCardVM:
    # ... existing properties ...
    
    # PHASE 9: Trust & Conversion Signals
    is_verified: bool              # ← Already in class?
    booked_today: int              # ← Already in class?
    viewers_now: int               # ← Already in class?
    is_best_rating: bool           # ← Already in class?
    is_lowest_price: bool          # ← Already in class?
    is_best_deal: bool             # ← Already in class?
    is_best_value: bool            # ← Already in class?
```

**If any are missing**, add them:

```python
# In post_init method or as properties:
def is_urgent(self) -> bool:
    """Property is hot - multiple bookings or viewers"""
    return self.booked_today > 0 or self.viewers_now > 5

def is_hot(self) -> bool:
    """Multiple signals of popularity"""
    return (
        self.booked_today >= 3
        or (self.viewers_now >= 10)
        or self.rooms_left <= 3
    )
```

**Computation** (in `build_hotel_card_vm` function):

```python
def build_hotel_card_vm(property_obj, today_bookings=None, current_viewers=None) -> HotelCardVM:
    """Transform ORM → HotelCardVM with PHASE 9 signals"""
    
    # Get today's booking count (from cache or DB)
    booked_today = get_today_booking_count(property_obj.id)
    
    # Get current viewer count (from cache or real-time system)
    viewers_now = get_current_viewer_count(property_obj.id)
    
    # Compute badges
    is_best_rating = is_property_best_rated(property_obj)
    is_lowest_price = is_property_lowest_price(property_obj)
    is_best_deal = has_significant_discount(property_obj)
    is_best_value = is_high_rating_low_price(property_obj)
    
    return HotelCardVM(
        id=property_obj.id,
        name=property_obj.name,
        # ... other properties ...
        booked_today=booked_today,
        viewers_now=viewers_now,
        is_verified=property_obj.is_verified,
        is_best_rating=is_best_rating,
        is_lowest_price=is_lowest_price,
        is_best_deal=is_best_deal,
        is_best_value=is_best_value,
    )
```

**Why**:
- Adds trust signals ("verified", "best rated")
- Adds urgency signals ("booked today", "viewing now")
- Adds decision aids ("best deal", "best value")
- Critical for OTA conversion optimization

---

### 🔄 Task 9.2: Create Badge Styles

**File**: `static/css/badges.css` (new file)

```css
/* Trust Badges */
.badge-verified {
  background: var(--color-success);
  color: white;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  display: flex;
  align-items: center;
  gap: 4px;
}

.badge-best-rated {
  background: #e8c547;
  color: #8b5e0a;
  font-weight: var(--weight-bold);
}

.badge-lowest-price {
  background: var(--color-danger);
  color: white;
  font-weight: var(--weight-bold);
}

.badge-best-deal {
  background: #f59e0b;
  color: white;
  font-weight: var(--weight-bold);
}

.hotel-card-badge {
  position: absolute;
  top: var(--space-3);
  left: var(--space-3);
  z-index: 10;
}

/* Conversion Signals */
.conversion-signal {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  margin-top: var(--space-2);
}

.conversion-signal.urgency {
  background: #fef2f2;
  color: #dc2626;
  border-left: 2px solid #dc2626;
}

.conversion-signal.attention {
  background: #f0f9ff;
  color: #0284c7;
  border-left: 2px solid #0284c7;
}
```

**Include in base.html**:
```html
<link rel="stylesheet" href="{% static 'css/badges.css' %}" />
```

---

### 🔄 Task 9.3: Update Search View to Populate PHASE 9 Data

**File**: `apps/search/views_production.py`

**Enhance `search_list` function**:

```python
def search_list(request):
    """Search with PHASE 9 features"""
    query = request.GET.get('q', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Execute search
    search_engine = ProductionSearchEngine(Property)
    results_qs = search_engine.search(
        query=query,
        min_price=min_price,
        max_price=max_price,
    )
    
    # Get booking/viewer data for PHASE 9
    booking_counts = get_today_booking_counts([p.id for p in results_qs])
    viewer_counts = get_current_viewer_counts([p.id for p in results_qs])
    
    # Transform to VMs with PHASE 9 signals
    hotel_cards = [
        build_hotel_card_vm(
            prop,
            booked_today=booking_counts.get(prop.id, 0),
            viewers_now=viewer_counts.get(prop.id, 0),
        )
        for prop in results_qs
    ]
    
    # Build filters
    filters_vm = build_filters_vm(request, results_qs)
    
    # Render
    return render(request, 'search/list.html', {
        'results': hotel_cards,
        'filters': filters_vm,
        'query': query,
        'total_count': len(results_qs),
    })
```

**Helper Functions** (add to `apps/hotels/signals.py` or new file):

```python
from django.core.cache import cache
from django.utils.timezone import now, timedelta
from booking.models import Booking

def get_today_booking_counts(property_ids):
    """Get today's booking count for multiple properties"""
    today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    bookings = Booking.objects.filter(
        property_id__in=property_ids,
        created_at__gte=today_start
    ).values('property_id').annotate(count=Count('id'))
    
    return {b['property_id']: b['count'] for b in bookings}

def get_current_viewer_counts(property_ids):
    """Get count of users viewing properties (from cache/analytics)"""
    # Simple approach: use cached data from analytics
    counts = {}
    for prop_id in property_ids:
        key = f'property:{prop_id}:viewers_now'
        counts[prop_id] = cache.get(key, 0)
    return counts
```

---

## PART D: VALIDATION CHECKLIST

### Before Going Live

- [ ] **Task 8.1**: Search URLs updated to use `views_production.py`
- [ ] **Task 8.2**: `search/list.html` refactored to use HotelCardVM
- [ ] **Task 8.3**: Hotel detail view uses HotelDetailVM
- [ ] **Task 8.4**: Hotel detail template updated for ViewModel access
- [ ] **Task 8.5**: Query caching implemented
- [ ] **Task 8.6**: Fragment caching configured
- [ ] **Task 9.1**: HotelCardVM includes PHASE 9 properties (verify in code)
- [ ] **Task 9.2**: Badge styles created and included in base.html
- [ ] **Task 9.3**: Search view populates booked_today, viewers_now
- [ ] **CSS**: No inline colors remaining (all using tokens)
- [ ] **Test**: Search returns 20 hotel cards with badges/signals
- [ ] **Performance**: Page load < 2 seconds, CLS = 0
- [ ] **Mobile**: Layout works on 768px breakpoint

### Post-Launch Monitoring

- [ ] Monitor query count (should be < 5 queries per page via select_related)
- [ ] Monitor response time (target < 500ms for search)
- [ ] Monitor cache hit rate (target > 80%)
- [ ] Monitor conversion rate (OTA signals should improve CTR)

---

## PART E: QUICK REFERENCE - FILE LOCATIONS

### New Production Code (Ready to Use)

```
apps/
  ├── hotels/
  │   ├── search.py                          [ProductionSearchEngine, FilterAggregator]
  │   ├── image_optimization.py              [ImageOptimizer, ImageTemplate]
  │   ├── maps.py                            [get_google_maps_context, coordinates]
  │   └── viewmodels/
  │       ├── __init__.py
  │       ├── hotel_card_vm.py               [HotelCardVM - 45 properties]
  │       ├── hotel_detail_vm.py             [HotelDetailVM, RoomTypeVM, ReviewVM]
  │       └── filters_vm.py                  [FiltersVM, FilterOptionVM, factory]
  └── search/
      └── views_production.py                [search_list, build_hotel_card_vm, APIs]

static/css/
  ├── tokens.css                             [150+ design tokens - OVERHAUL]
  ├── hotel-card.css                         [3-column grid layout - NEW]
  ├── badges.css                             [Trust badges - TO CREATE]
  └── (legacy files still in use)

templates/
  ├── base.html                              [UPDATED - includes new CSS]
  ├── search/
  │   └── list.html                          [TO UPDATE - use VMs]
  └── hotels/
      └── detail.html                        [TO UPDATE - use HotelDetailVM]
```

---

## PART F: ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT REQUEST: GET /search/?q=mumbai                           │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 1: views_production.search_list()                          │
│ ├─ Extract: query, filters from request                          │
│ └─ Call: ProductionSearchEngine.search(query)                    │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 2: ProductionSearchEngine (apps/hotels/search.py)          │
│ ├─ Build multi-field text query (10-point scoring)              │
│ ├─ Apply filters (price, rating, amenities)                     │
│ ├─ Optimize: select_related + prefetch_related                  │
│ └─ Order by: search_score desc, rating desc                     │
│                                                                   │
│ FilterAggregator:                                                │
│ ├─ get_price_range() → Available price range                    │
│ ├─ get_rating_options() → Available rating levels with counts   │
│ └─ get_amenity_options() → Available amenities with counts      │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 3: ORM Results (Property QuerySet)                         │
│ └─ Property objects with optimized queries                       │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 4: ViewModel Transformation                                │
│ └─ build_hotel_card_vm(property_obj) → HotelCardVM              │
│    ├─ Extract: name, price, ratings, images, amenities          │
│    ├─ Compute: discount_percent, savings_amount, rating_tier    │
│    ├─ Get PHASE 9: booked_today, viewers_now                    │
│    └─ Return: Strongly-typed HotelCardVM                         │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 5: Filter Generation (FilterAggregator)                    │
│ └─ FiltersVM with dynamic options from search results            │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 6: Context Preparation                                     │
│ {                                                                │
│   'results': [HotelCardVM, HotelCardVM, ...],                   │
│   'filters': FiltersVM,                                          │
│   'query': 'mumbai',                                             │
│ }                                                                │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 7: Template Rendering (search/list.html)                  │
│ ├─ Iterate: {% for hotel in results %}  [HotelCardVM objects]  │
│ ├─ Access: {{ hotel.price_current }}, {{ hotel.image_url }}    │
│ ├─ Render: 3-column grid (image | info | price)                │
│ ├─ Show: Badges (verified, best deal, best rated)              │
│ ├─ Show: Signals (booked today, viewing now) [PHASE 9]         │
│ ├─ Show: Filters sidebar (dynamic options)                      │
│ └─ Style: Token-based CSS classes                               │
└──────────────────────────────┬──────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ CLIENT RESPONSE: Rendered HTML with hotel cards                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## SUMMARY

**Current Status**: 70% Complete
- ✅ Infrastructure built (VMs, search, filters, tokens, CSS)
- 🔄 Integration 50% (URLs updated, templates pending)
- ⏳ OTA Features 0% (PHASE 9 - badges/signals)

**Next Steps**:
1. **TODAY**: Run through Tasks 8.1-8.6 (Integration)
2. **THIS WEEK**: Implement Tasks 9.1-9.3 (PHASE 9)
3. **QA**: Validate all 9 phases working end-to-end
4. **DEPLOY**: Launch production OTA architecture

**Time Estimate**:
- Integration (8.1-8.6): 1-2 hours
- OTA Features (9.1-9.3): 1-2 hours
- Testing & QA: 1-2 hours
- **Total**: 3-6 hours to complete all phases

---

**Questions? Refer to**:
- `apps/hotels/viewmodels/hotel_card_vm.py` - VM structure
- `apps/hotels/search.py` - Search logic
- `apps/search/views_production.py` - View implementation
- `static/css/tokens.css` - Token system
- `static/css/hotel-card.css` - Card layout
