"""
Search Service - Intelligent Autocomplete
Implements unified search across cities/areas/hotels

Critical: Single query returns mixed entity types
Pattern from logs: SearchIndex table (NOT individual model queries)
"""
from django.db.models import Q
from core.location_models import LocationSearchIndex, City, Locality
from apps.hotels.models import Property


def autocomplete_search(query, limit=10):
    """
    Intelligent autocomplete: mixed entity types
    
    Args:
        query: User input text (e.g., "coor", "cheap mumbai")
    
    Returns:
        {
            'cities': [...],
            'localities': [...],
            'hotels': [...]
        }
    """
    if not query or len(query) < 2:
        return {'cities': [], 'localities': [], 'hotels': []}
    
    # Query LocationSearchIndex (NOT individual tables)
    results = LocationSearchIndex.objects.filter(
        Q(search_text__icontains=query) | Q(alternate_names__icontains=query),
        is_active=True,
        is_clickable=True
    ).select_related('context_city').order_by('-search_score', '-search_count')[:limit]
    
    # Group by entity type
    grouped = {
        'cities': [],
        'localities': [],
        'hotels': []
    }
    
    for entry in results:
        if entry.entity_type == 'city':
            grouped['cities'].append({
                'id': entry.entity_id,
                'name': entry.display_name,
                'code': entry.context_city.code if entry.context_city else None,
                'type': 'city'
            })
        elif entry.entity_type == 'locality':
            grouped['localities'].append({
                'id': entry.entity_id,
                'name': entry.display_name,
                'city': entry.context_city.name if entry.context_city else '',
                'type': 'locality'
            })
        elif entry.entity_type == 'hotel':
            grouped['hotels'].append({
                'id': entry.entity_id,
                'name': entry.display_name,
                'city': entry.context_city.name if entry.context_city else '',
                'type': 'hotel'
            })
    
    return grouped


def semantic_search_parse(query):
    """
    Parse semantic intent from search query
    
    Examples:
    - "cheap coorg hotels" → {location: 'coorg', price_order: 'asc'}
    - "luxury resorts near beach" → {property_type: 'resort', rating_min: 4, locality_type: 'beach'}
    - "hotels near airport" → {locality_type: 'airport'}
    """
    query_lower = query.lower()
    filters = {}
    
    # Price intent
    if any(word in query_lower for word in ['cheap', 'budget', 'affordable']):
        filters['price_order'] = 'asc'
        filters['price_max'] = 3000
    elif any(word in query_lower for word in ['luxury', 'premium', '5 star']):
        filters['rating_min'] = 4.0
        filters['price_min'] = 5000
    
    # Property type
    if 'resort' in query_lower:
        filters['property_type'] = 'Resort'
    elif 'villa' in query_lower:
        filters['property_type'] = 'Villa'
    elif 'hostel' in query_lower:
        filters['property_type'] = 'Hostel'
    
    # Locality type
    if 'beach' in query_lower:
        filters['locality_type'] = 'beach'
    elif 'airport' in query_lower:
        filters['locality_type'] = 'airport'
    elif 'hill station' in query_lower or 'hills' in query_lower:
        filters['locality_type'] = 'hill_station'
    
    # Location extraction (remove intent words)
    location_query = query_lower
    for word in ['cheap', 'luxury', 'budget', 'hotel', 'hotels', 'resort', 'near', 'in']:
        location_query = location_query.replace(word, '')
    location_query = location_query.strip()
    
    if location_query:
        filters['location_text'] = location_query
    
    return filters


def search_hotels(filters):
    """
    Execute hotel search with structured filters
    
    Args:
        filters: Dict from semantic_search_parse or direct API params
    
    Returns:
        QuerySet with intelligence signals attached
    """
    from apps.hotels.models import Property
    
    queryset = Property.objects.select_related('city', 'locality')
    
    # City filter
    if 'city_id' in filters:
        queryset = queryset.filter(city_id=filters['city_id'])
    elif 'location_text' in filters:
        # Fallback: fuzzy city match
        queryset = queryset.filter(
            Q(city__name__icontains=filters['location_text']) |
            Q(city__alternate_names__icontains=filters['location_text'])
        )
    
    # Locality filter
    if 'locality_id' in filters:
        queryset = queryset.filter(locality_id=filters['locality_id'])
    elif 'locality_type' in filters:
        queryset = queryset.filter(locality__locality_type=filters['locality_type'])
    
    # Price filters
    if 'price_min' in filters:
        queryset = queryset.filter(base_price__gte=filters['price_min'])
    if 'price_max' in filters:
        queryset = queryset.filter(base_price__lte=filters['price_max'])
    
    # Rating filter
    if 'rating_min' in filters:
        queryset = queryset.filter(rating__gte=filters['rating_min'])
    
    # Property type
    if 'property_type' in filters:
        queryset = queryset.filter(property_type=filters['property_type'])
    
    # Policy filters
    if filters.get('free_cancellation'):
        queryset = queryset.filter(has_free_cancellation=True)
    
    # Sorting
    if filters.get('price_order') == 'asc':
        queryset = queryset.order_by('base_price')
    elif filters.get('price_order') == 'desc':
        queryset = queryset.order_by('-base_price')
    elif filters.get('sort_by') == 'rating':
        queryset = queryset.order_by('-rating', '-review_count')
    elif filters.get('sort_by') == 'popularity':
        queryset = queryset.order_by('-popularity_score', '-bookings_this_week')
    else:
        # Default: relevance sorting
        queryset = queryset.order_by('-popularity_score', '-rating')
    
    return queryset


# Legacy class for backwards compatibility
class GlobalSearchService:
    """DEPRECATED: Use autocomplete_search() function instead"""
    
    @staticmethod
    def search(query, limit=10):
        return autocomplete_search(query, limit)

        
        # Search in SearchIndex
        results = SearchIndex.objects.filter(
            Q(normalized_name__istartswith=normalized_query) |
            Q(normalized_name__icontains=normalized_query),
            is_active=True
        ).order_by('-search_count', 'name')[:limit]
        
        # Increment search counts for returned results
        result_ids = [r.id for r in results]
        if result_ids:
            SearchIndex.objects.filter(id__in=result_ids).update(
                search_count=Q('search_count') + 1
            )
        
        return [
            {
                'id': r.id,
                'type': r.search_type,
                'name': r.name,
                'city': r.city,
                'state': r.state,
                'display_text': f"{r.name}, {r.city}" if r.search_type != 'CITY' else r.name,
                'search_count': r.search_count
            }
            for r in results
        ]
    
    @staticmethod
    def search_hotels(query, city=None):
        """
        Search specifically for hotels.
        
        Args:
            query (str): Search term (hotel name, area, landmark)
            city (str, optional): Filter by city
            
        Returns:
            QuerySet: Filtered hotel queryset
        """
        from apps.hotels.models import Hotel
        
        filters = Q(is_active=True, is_published=True)
        
        if query:
            filters &= (
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(address__icontains=query) |
                Q(area__icontains=query) |
                Q(city__icontains=query)
            )
        
        if city:
            filters &= Q(city__iexact=city)
        
        return Hotel.objects.filter(filters).select_related(
            'owner'
        ).prefetch_related(
            'amenities',
            'images',
            'rooms'
        )
    
    @staticmethod
    def get_popular_searches(limit=5):
        """
        Get most popular search terms.
        
        Returns:
            list: Top searched terms
        """
        return SearchIndex.objects.filter(
            is_active=True
        ).order_by('-search_count')[:limit].values('name', 'search_type', 'search_count')
    
    @staticmethod
    def index_hotel(hotel):
        """
        Add/update hotel in search index.
        
        Args:
            hotel: Hotel model instance
        """
        # Index property name
        SearchIndex.objects.update_or_create(
            search_type='PROPERTY',
            name=hotel.name,
            defaults={
                'city': hotel.city,
                'state': hotel.state or '',
                'content_type': 'hotel',
                'object_id': hotel.id,
                'is_active': hotel.is_active and hotel.is_published
            }
        )
        
        # Index city if not already present
        if hotel.city:
            SearchIndex.objects.get_or_create(
                search_type='CITY',
                name=hotel.city,
                defaults={
                    'city': hotel.city,
                    'state': hotel.state or '',
                    'is_active': True
                }
            )
        
        # Index area if provided
        if hotel.area:
            SearchIndex.objects.get_or_create(
                search_type='AREA',
                name=hotel.area,
                defaults={
                    'city': hotel.city,
                    'state': hotel.state or '',
                    'is_active': True
                }
            )
