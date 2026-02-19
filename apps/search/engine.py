"""Unified Search Engine - Single source of truth for all search operations.

Consolidates:
- Hotel search
- Location autocomplete
- Filter aggregation
- Advanced ranking

This replaces:
- core.search_service
- core.search_api
- apps.search.services
- apps.hotels.search
"""

from django.db.models import Q, Case, When, Value, IntegerField, F, Prefetch
from django.core.cache import cache
from typing import Optional, Dict, Any, Tuple, List
import logging

from apps.hotels.models import Property
from core.location_models import City, Locality

logger = logging.getLogger(__name__)


class UnifiedSearchEngine:
    """Enterprise OTA search engine with:
    - Multi-field scoring
    - Location-aware search
    - Advanced filtering
    - Query optimization
    - Result ranking
    """
    
    def __init__(self):
        """Initialize search engine."""
        self.cache_ttl = 300  # 5 minutes
    
    def search_hotels(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        locality: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_rating: Optional[float] = None,
        amenities: Optional[List[str]] = None,
        property_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Property], int]:
        """Perform advanced hotel search.
        
        Args:
            query: Text search query
            city: City name filter
            locality: Locality/area filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            min_rating: Minimum rating filter
            amenities: List of amenities to include
            property_types: List of property types
            limit: Results per page
            offset: Pagination offset
            
        Returns:
            (results_queryset, total_count)
        """
        try:
            # Build cache key
            cache_key = self._build_cache_key(
                'search', query, city, locality, min_price, max_price, min_rating
            )
            cached = cache.get(cache_key)
            if cached is not None:
                return cached[:len(cached) - len(cached)//2], cached[-1]  # Unpack
            
            # Build query
            q_obj = Q()
            
            # Text search with prioritization
            if query:
                query_lower = query.lower()
                text_q = (
                    Q(name__icontains=query) |
                    Q(city__name__icontains=query) |
                    Q(area__icontains=query) |
                    Q(landmark__icontains=query) |
                    Q(address__icontains=query)
                )
                q_obj &= text_q
            
            # Location filters
            if city:
                q_obj &= Q(city__name__icontains=city)
            if locality:
                q_obj &= Q(locality__name__icontains=locality)
            
            # Price filters (using room_types foreign key)
            if min_price:
                q_obj &= Q(room_types__base_price__gte=min_price)
            if max_price:
                q_obj &= Q(room_types__base_price__lte=max_price)
            
            # Rating filter
            if min_rating:
                q_obj &= Q(rating__gte=min_rating)
            
            # Property type filter
            if property_types:
                q_obj &= Q(property_type__in=property_types)
            
            # Base queryset with optimizations
            qs = Property.objects.filter(q_obj)
            
            # Apply select_related and prefetch_related (ONLY VALID RELATIONS)
            qs = qs.select_related(
                'city',
                'owner',
                'locality'
            ).prefetch_related(
                'images',
                'amenities',
                'room_types'
            )
            
            # Add ranking scores
            if query:
                qs = qs.annotate(
                    search_score=Case(
                        When(name__iexact=query, then=Value(10)),
                        When(name__icontains=query, then=Value(8)),
                        When(city__name__icontains=query, then=Value(6)),
                        When(area__icontains=query, then=Value(4)),
                        When(landmark__icontains=query, then=Value(3)),
                        When(address__icontains=query, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ).order_by('-search_score', '-rating')
            else:
                qs = qs.order_by('-rating', '-created_at')
            
            # Get total count before pagination
            total_count = qs.count()
            
            # Apply pagination
            results = qs[offset:offset + limit]
            
            # Cache results
            cache_data = (list(results), total_count)
            cache.set(cache_key, cache_data, self.cache_ttl)
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return [], 0
    
    def autocomplete(
        self,
        query: str,
        limit: int = 8,
    ) -> Dict[str, Any]:
        """Unified autocomplete endpoint.
        
        Combines:
        - City matches
        - Locality matches
        - Property matches
        
        Args:
            query: User input (minimum 2 chars)
            limit: Max results (default 8: 4 cities + 4 properties)
            
        Returns:
            {
                'results': [
                    {'label': '...', 'type': 'city|locality|property', 'url': '...'}
                ]
            }
        """
        try:
            if not query or len(query) < 2:
                return {'results': []}
            
            query_lower = query.lower()
            results = []
            
            # City matches (priority 1)
            try:
                cities = City.objects.filter(
                    name__icontains=query_lower
                ).values('id', 'name')[:limit // 2]
                for city in cities:
                    results.append({
                        'label': city['name'],
                        'type': 'city',
                        'url': f"/search/?q={city['name']}&city={city['id']}"
                    })
            except Exception as e:
                logger.error(f"City autocomplete error: {e}")
            
            # Locality matches (priority 2)
            try:
                localities = Locality.objects.filter(
                    name__icontains=query_lower
                ).values('id', 'name')[:limit // 2]
                for locality in localities:
                    results.append({
                        'label': locality['name'],
                        'type': 'locality',
                        'url': f"/search/?q={locality['name']}&locality={locality['id']}"
                    })
            except Exception as e:
                logger.error(f"Locality autocomplete error: {e}")
            
            # Property matches (priority 3)
            try:
                properties = Property.objects.filter(
                    Q(name__icontains=query) |
                    Q(landmark__icontains=query)
                ).values('id', 'name', 'slug', 'city__name')[:limit // 2]
                for prop in properties:
                    results.append({
                        'label': f"{prop['name']} - {prop['city__name'] or 'Property'}",
                        'type': 'property',
                        'url': f"/hotels/{prop['slug']}/"
                    })
            except Exception as e:
                logger.error(f"Property autocomplete error: {e}")
            
            # Limit to max results
            return {'results': results[:limit]}
            
        except Exception as e:
            logger.error(f"Autocomplete error: {str(e)}")
            return {'results': []}
    
    def get_filters(self) -> Dict[str, Any]:
        """Get available filters for advanced search.
        
        Returns:
            {
                'cities': [...],
                'property_types': [...],
                'amenities': [...],
                'price_range': {'min': ..., 'max': ...},
                'rating_range': {...}
            }
        """
        try:
            from django.db.models import Min, Max
            
            # Get price range from room_types (not base_price property)
            from rooms.models import RoomType
            price_stats = RoomType.objects.aggregate(
                min_price=Min('base_price'),
                max_price=Max('base_price')
            )
            
            # Get unique cities (related_name is 'hotels')
            cities = City.objects.filter(
                hotels__isnull=False
            ).distinct().values('id', 'name')[:20]
            
            # Get unique property types
            property_types = Property.objects.values_list(
                'property_type', flat=True
            ).distinct()
            
            return {
                'cities': list(cities),
                'property_types': list(property_types or []),
                'price_range': {
                    'min': price_stats.get('min_price') or 0,
                    'max': price_stats.get('max_price') or 10000,
                },
                'rating_range': {'min': 0, 'max': 5}
            }
        except Exception as e:
            logger.error(f"Get filters error: {e}")
            return {}
    
    def _build_cache_key(self, *args) -> str:
        """Build cache key from search parameters."""
        import hashlib
        key_str = "|".join(str(arg).lower() for arg in args)
        return f"search:{hashlib.md5(key_str.encode()).hexdigest()}"


# Create singleton instance
search_engine = UnifiedSearchEngine()
