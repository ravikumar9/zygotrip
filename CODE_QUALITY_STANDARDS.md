# ARCHITECTURAL TRANSFORMATION - CODE QUALITY STANDARDS

## Overview
This document defines code quality standards for the transformed architecture.

## Type Hints (Python 3.10+)
All service methods MUST have type hints:

```python
from typing import List, Dict, Optional, QuerySet
from decimal import Decimal

def get_property_price(property_id: int, check_in: date) -> Optional[Decimal]:
    """Return minimum room price for date"""
    pass

def search_properties(
    city: str,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None
) -> QuerySet[Property]:
    """Search properties with filters"""
    pass
```

## Docstrings (Google Style)
All public methods require docstrings:

```python
def apply_ranking(self, queryset: QuerySet) -> QuerySet:
    """
    Apply composite relevance scoring to property search results.
    
    Combines multiple signals: rating (30%), price (20%), distance (25%),
    popularity (15%), and availability (10%).
    
    Args:
        queryset: Filtered property queryset to rank
        
    Returns:
        QuerySet annotated with relevance_score, ordered by relevance
        
    Example:
        >>> service = SearchRankingService(qs, {'lat': '28.6139', 'lng': '77.2090'})
        >>> ranked_qs = service.apply_ranking(qs)
    """
    pass
```

## Constants Over Magic Numbers
Create constants.py for all magic values:

```python
# apps/hotels/constants.py

# Caching TTLs (seconds)
CACHE_TTL_HOTEL_LIST = 60
CACHE_TTL_HOTEL_DETAIL = 300
CACHE_TTL_CATEGORIES = 3600
CACHE_TTL_SEARCH_RESULTS = 120

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Ranking weights
RANKING_WEIGHT_RATING = 0.30
RANKING_WEIGHT_PRICE = 0.20
RANKING_WEIGHT_DISTANCE = 0.25
RANKING_WEIGHT_POPULARITY = 0.15
RANKING_WEIGHT_AVAILABILITY = 0.10

# Thresholds
MIN_RATING_TOP_RATED = 4.5
MIN_RATING_EXCEPTIONAL = 4.8
MIN_BOOKINGS_POPULAR = 3
MIN_BOOKINGS_TRENDING = 5
MAX_ROOMS_SCARCITY_URGENT = 3
MAX_ROOMS_SCARCITY_WARNING = 5
```

## Service Layer Pattern
Services MUST:
- Accept validated input (not raw request.GET/POST)
- Return typed DTOs or domain objects
- Handle errors and log exceptions
- Be stateless (no instance state mutation)
- Be testable in isolation

```python
class PropertySearchService:
    def __init__(self, filters: SearchFilters, user: User = None):
        self.filters = filters  # Validated DTO
        self.user = user
    
    def execute(self) -> SearchResultDTO:
        """Execute search and return typed DTO"""
        try:
            # Business logic
            return SearchResultDTO(
                properties=properties,
                total_count=count,
                applied_filters=self.filters
            )
        except Exception as exc:
            logger.exception("Search service error", exc_info=exc)
            raise ServiceException("Search failed") from exc
```

## Validation Firewall
Models MUST implement clean() for data integrity:

```python
class RoomType(models.Model):
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_guests = models.PositiveIntegerField()
    
    def clean(self):
        if self.base_price <= 0:
            raise ValidationError({'base_price': 'Price must be positive'})
        if self.max_guests < 1 or self.max_guests > 10:
            raise ValidationError({'max_guests': 'Guests must be 1-10'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Always validate before save
        super().save(*args, **kwargs)
```

## Query Optimization Checklist
Every queryset MUST:
- Use select_related() for FK access
- Use prefetch_related() for M2M/reverse FK
- Use only() or defer() to limit columns
- Add values()/values_list() for JSON serialization
- Use exists() instead of count() > 0
- Use iterator() for large result sets

```python
# BAD: N+1 queries
properties = Property.objects.filter(city='Mumbai')
for prop in properties:
    print(prop.owner.name)  # N queries
    print(prop.images.count())  # N queries

# GOOD: Optimized
properties = Property.objects.filter(city='Mumbai')\
    .select_related('owner', 'city')\
    .prefetch_related('images', 'amenities')\
    .only('id', 'name', 'rating', 'owner__name')
```

## Error Handling
Use domain-specific exceptions:

```python
# apps/hotels/exceptions.py
class PropertyServiceException(Exception):
    """Base exception for property service errors"""
    pass

class PropertyNotFoundError(PropertyServiceException):
    """Property does not exist or not accessible"""
    pass

class PricingCalculationError(PropertyServiceException):
    """Cannot calculate pricing for date range"""
    pass

# Usage in service
def get_property_price(property_id: int, date: date) -> Decimal:
    property_obj = Property.objects.filter(id=property_id).first()
    if not property_obj:
        raise PropertyNotFoundError(f"Property {property_id} not found")
    
    try:
        return calculate_price(property_obj, date)
    except Exception as exc:
        logger.exception(f"Pricing error for property {property_id}")
        raise PricingCalculationError("Cannot calculate price") from exc
```

## Testing Standards
Each service MUST have:
- Unit tests with mocked dependencies
- Integration tests with test database
- Edge case tests (null, empty, invalid)

```python
# tests/test_search_ranking.py
class TestSearchRankingService:
    def test_ranking_applies_correct_weights(self):
        """Verify composite score calculation"""
        # Arrange
        qs = PropertyFactory.create_batch(10)
        service = SearchRankingService(qs, {})
        
        # Act
        result = service.apply_ranking()
        
        # Assert
        assert result.first().relevance_score > 0
        assert result.first().rating >= result.last().rating
    
    def test_ranking_handles_missing_location(self):
        """Distance score defaults to neutral when lat/lng missing"""
        service = SearchRankingService(qs, {})  # No lat/lng
        result = service.apply_ranking()
        assert result.exists()  # No crash
```

## Code Review Checklist
Before merging, verify:
- [ ] All services have type hints
- [ ] All public methods have docstrings
- [ ] No magic numbers (use constants)
- [ ] Queries use select_related/prefetch_related
- [ ] Models implement clean() validation
- [ ] Error handling with specific exceptions
- [ ] Logging for critical paths
- [ ] Tests cover happy path + edge cases
- [ ] No print() statements (use logger)
- [ ] No commented-out code
- [ ] No TODO comments without tickets
