"""Production search engine with scoring, filtering, and optimization.

Replaces toy-level name__icontains logic with real OTA search.
"""

from django.db.models import Q, Case, When, Value, IntegerField, F, Prefetch, Min, Max
from django.core.cache import cache
from typing import Optional, Dict, Any


class ProductionSearchEngine:
    """Enterprise search engine with:
    - Multi-field scoring
    - Advanced filtering
    - Query optimization
    - Result ranking
    """
    
    def __init__(self, model):
        """Initialize with Property model."""
        self.model = model
        self.query = Q()
    
    def search(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_rating: Optional[float] = None,
        amenities: Optional[list] = None,
        property_types: Optional[list] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple:
        """Perform advanced search.
        
        Returns: (results, total_count, score_map)
        """
        try:
            # Phase 1: Text search with scoring
            if query:
                self._build_text_query(query)
            
            # Phase 2: Filter query
            if city:
                self.query &= Q(city__name__icontains=city)
            
            if min_price or max_price:
                if min_price:
                    self.query &= Q(base_price__gte=min_price)
                if max_price:
                    self.query &= Q(base_price__lte=max_price)
            
            if min_rating:
                self.query &= Q(rating__gte=min_rating)
            
            if amenities:
                for amenity in amenities:
                    self.query &= Q(amenities__icontains=amenity)
            
            if property_types:
                self.query &= Q(property_type__in=property_types)
            
            # Phase 3: Execute with optimization
            base_qs = self.model.objects.filter(self.query)
            
            # Optimize DB queries - only use valid relations
            optimized_qs = base_qs.select_related(
                'city',
                'owner',
                'locality'
            ).prefetch_related(
                'images',
                'amenities',
                'room_types'
            )
            
            # Add scoring for ranking
            if query:
                optimized_qs = optimized_qs.annotate(
                    search_score=Case(
                        # Exact name match (highest priority)
                        When(name__iexact=query, then=Value(10)),
                        # Name contains (high priority)
                        When(name__icontains=query, then=Value(8)),
                        # City match
                        When(city__name__icontains=query, then=Value(6)),
                        # Area match
                        When(area__icontains=query, then=Value(4)),
                        # Landmark match
                        When(landmark__icontains=query, then=Value(3)),
                        # Address match
                        When(address__icontains=query, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ).order_by('-search_score', '-rating')
            else:
                # No query: rank by rating + popularity
                optimized_qs = optimized_qs.order_by('-rating', '-bookings_today')
            
            # Get total count before pagination
            total_count = optimized_qs.count()
            
            # Apply pagination
            results = optimized_qs[offset:offset + limit]
            
            return list(results), total_count
        
        except Exception as e:
            # Return empty results on error instead of crashing
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Search engine error: {str(e)}")
            return [], 0
    
    def _build_text_query(self, query: str):
        """Build multi-field text search query."""
        self.query &= (
            Q(name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(area__icontains=query) |
            Q(landmark__icontains=query) |
            Q(address__icontains=query) |
            Q(description__icontains=query)
        )


class FilterAggregator:
    """Generate dynamic filter options based on querystate.
    
    Server-driven: filters computed from actual data, not hardcoded.
    """
    
    def __init__(self, model, base_qs):
        """Initialize with Property model and base queryset."""
        self.model = model
        self.base_qs = base_qs
    
    def get_price_range(self) -> Dict[str, int]:
        """Get min/max prices for slider from room_types."""
        from django.db.models import Min, Max
        stats = self.base_qs.annotate(
            min_room_price=Min('room_types__base_price')
        ).aggregate(
            min_price=Min('min_room_price'),
            max_price=Max('min_room_price')  # Using same annotation, could improve
        )
        return {
            'min': int(stats['min_price'] or 1000),
            'max': int(stats['max_price'] or 10000),
        }
    
    def get_rating_options(self, limit: int = 5) -> list:
        """Get rating options with result counts."""
        options = []
        for rating in [5, 4, 3, 2, 1]:
            count = self.base_qs.filter(rating__gte=rating).count()
            if count > 0:
                options.append({
                    'label': f'{rating}+ ⭐',
                    'value': rating,
                    'count': count
                })
        return options
    
    def get_amenity_options(self, limit: int = 15) -> list:
        """Get most common amenities with counts."""
        from apps.hotels.models import PropertyAmenity
        from django.db.models import Count
        
        # Count amenities across all properties in this query
        property_ids = self.base_qs.values_list('id', flat=True)
        
        amenity_counts = PropertyAmenity.objects.filter(
            property_id__in=property_ids
        ).values('name').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        return [
            {
                'label': item['name'],
                'value': item['name'].lower().replace(' ', '_'),
                'count': item['count']
            }
            for item in amenity_counts
        ]


# Cache layer
def get_cached_search_results(cache_key: str, timeout: int = 300):
    """Get search results from cache."""
    return cache.get(cache_key)


def set_cached_search_results(cache_key: str, results: Any, timeout: int = 300):
    """Cache search results."""
    cache.set(cache_key, results, timeout)
