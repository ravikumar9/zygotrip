"""
Search API Endpoints
Implements intelligent autocomplete + geo search

Critical APIs:
1. /api/search/autocomplete/ - Mixed entity results
2. /api/search/hotels/ - Filtered + ranked hotel results  
3. /api/search/map/ - Bounding box geo queries
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from core.search_service import autocomplete_search, semantic_search_parse, search_hotels
from core.geo_search import hotels_in_bounding_box, get_city_context, sort_hotels_by_distance


@require_GET
def autocomplete_api(request):
    """
    Intelligent autocomplete: mixed entity types
    
    GET /api/search/autocomplete/?q=coor
    
    Response:
    {
        "cities": [{"id": 1, "name": "Coorg", "code": "COORG", "type": "city"}],
        "localities": [{"id": 2, "name": "Madikeri", "city": "Coorg", "type": "locality"}],
        "hotels": [{"id": 123, "name": "Taj Resort Coorg", "city": "Coorg", "type": "hotel"}]
    }
    """
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))
    
    if not query or len(query) < 2:
        return JsonResponse({'cities': [], 'localities': [], 'hotels': []})
    
    results = autocomplete_search(query, limit=limit)
    return JsonResponse(results)


@require_GET
def hotel_search_api(request):
    """
    Filtered + ranked hotel search
    
    GET /api/search/hotels/?city_id=1&price_max=5000&rating_min=4&sort_by=popularity
    
    Response:
    {
        "count": 45,
        "results": [
            {
                "id": 123,
                "name": "Taj Resort Coorg",
                "rating": 4.5,
                "review_count": 230,
                "distance_km": 2.3,  # If reference point provided
                "popularity_score": 89,
                "bookings_today": 12,
                "is_trending": true,
                "base_price": 3500,
                "has_free_cancellation": true,
                "city": "Coorg",
                "locality": "Madikeri"
            }
        ]
    }
    """
    # Extract filters from query params
    filters = {}
    
    if request.GET.get('city_id'):
        filters['city_id'] = int(request.GET.get('city_id'))
    if request.GET.get('locality_id'):
        filters['locality_id'] = int(request.GET.get('locality_id'))
    if request.GET.get('price_min'):
        filters['price_min'] = float(request.GET.get('price_min'))
    if request.GET.get('price_max'):
        filters['price_max'] = float(request.GET.get('price_max'))
    if request.GET.get('rating_min'):
        filters['rating_min'] = float(request.GET.get('rating_min'))
    if request.GET.get('property_type'):
        filters['property_type'] = request.GET.get('property_type')
    if request.GET.get('free_cancellation') == 'true':
        filters['free_cancellation'] = True
    if request.GET.get('sort_by'):
        filters['sort_by'] = request.GET.get('sort_by')
    if request.GET.get('price_order'):
        filters['price_order'] = request.GET.get('price_order')
    
    # Execute search
    hotels = search_hotels(filters)
    
    # If reference point provided, calculate distances
    ref_lat = request.GET.get('ref_lat')
    ref_lng = request.GET.get('ref_lng')
    if ref_lat and ref_lng:
        hotels = list(hotels)
        hotels = sort_hotels_by_distance(hotels, float(ref_lat), float(ref_lng))
    
    # Pagination
    page = int(request.GET.get('page', 1))
    paginator = Paginator(hotels, 20)
    page_obj = paginator.get_page(page)
    
    # Serialize results
    results = []
    for hotel in page_obj:
        result = {
            'id': hotel.id,
            'name': hotel.name,
            'slug': hotel.slug or '',
            'rating': float(hotel.rating) if hotel.rating else 0.0,
            'review_count': hotel.review_count or 0,
            'popularity_score': hotel.popularity_score or 0,
            'bookings_today': hotel.bookings_today or 0,
            'is_trending': hotel.is_trending or False,
            'base_price': float(hotel.base_price) if hotel.base_price else 0.0,
            'has_free_cancellation': hotel.has_free_cancellation if hotel.has_free_cancellation is not None else True,
            'city': hotel.city.name if hotel.city else (hotel.city_text or 'Unknown'),
            'city_id': hotel.city_id if hotel.city_id else None,
            'locality': {
                'id': hotel.locality.id,
                'name': hotel.locality.name
            } if hotel.locality else None,
        }
        
        # Add coordinates if available
        if hotel.latitude and hotel.longitude:
            result['latitude'] = float(hotel.latitude)
            result['longitude'] = float(hotel.longitude)
        
        # Add distance if calculated
        if hasattr(hotel, 'distance'):
            result['distance_km'] = hotel.distance
        
        results.append(result)
    
    return JsonResponse({
        'count': paginator.count,
        'page': page,
        'total_pages': paginator.num_pages,
        'results': results
    })


@require_GET
def map_results_api(request):
    """
    Hotels within map viewport (bounding box)
    
    GET /api/search/map/?ne_lat=12.5&ne_lng=77.6&sw_lat=12.3&sw_lng=77.4
    
    Response:
    {
        "count": 23,
        "hotels": [
            {
                "id": 123,
                "name": "Taj Resort",
                "latitude": 12.45,
                "longitude": 77.5,
                "rating": 4.5,
                "base_price": 3500
            }
        ]
    }
    """
    ne_lat = request.GET.get('ne_lat')
    ne_lng = request.GET.get('ne_lng')
    sw_lat = request.GET.get('sw_lat')
    sw_lng = request.GET.get('sw_lng')
    
    if not all([ne_lat, ne_lng, sw_lat, sw_lng]):
        return JsonResponse({'error': 'Missing bounding box coordinates'}, status=400)
    
    hotels = hotels_in_bounding_box(
        float(ne_lat), float(ne_lng),
        float(sw_lat), float(sw_lng)
    )
    
    # Serialize for map markers
    results = []
    for hotel in hotels[:200]:  # Limit to 200 markers
        results.append({
            'id': hotel.id,
            'name': hotel.name,
            'slug': hotel.slug,
            'latitude': float(hotel.latitude),
            'longitude': float(hotel.longitude),
            'rating': float(hotel.rating),
            'base_price': float(hotel.base_price),
            'is_trending': hotel.is_trending
        })
    
    return JsonResponse({
        'count': len(results),
        'hotels': results
    })


@require_GET
def city_context_api(request, city_code):
    """
    Load entire city context (CTXCR pattern)
    
    GET /api/search/city/COORG/
    
    Response:
    {
        "city": {"id": 1, "name": "Coorg", "code": "COORG"},
        "localities": [...],
        "bounding_box": {
            "ne": {"lat": 12.5, "lng": 75.8},
            "sw": {"lat": 12.2, "lng": 75.5},
            "centre": {"lat": 12.35, "lng": 75.65}
        },
        "hotel_count": 45
    }
    """
    context = get_city_context(city_code)
    
    if not context:
        return JsonResponse({'error': 'City not found'}, status=404)
    
    city = context['city']
    localities = context['localities']
    
    return JsonResponse({
        'city': {
            'id': city.id,
            'name': city.name,
            'code': city.code,
            'display_name': city.display_name
        },
        'localities': [
            {
                'id': loc.id,
                'name': loc.name,
                'type': loc.locality_type,
                'hotel_count': loc.hotel_count,
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude)
            }
            for loc in localities
        ],
        'bounding_box': context['bounding_box'],
        'hotel_count': context['hotel_count']
    })
