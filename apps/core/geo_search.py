"""
Geo Search Engine
Implements bounding box filtering, nearby search, distance sorting

Critical pattern from logs:
- ne/sw coordinates define viewport
- Centre coordinates for city context
- Distance calculation for "2.3 km from city centre"
"""
from math import radians, cos, sin, asin, sqrt
from django.db.models import Q, F
from decimal import Decimal


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points (km)
    Haversine formula: accurate for short distances
    """
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c  # Earth radius
    return round(km, 1)


def hotels_in_bounding_box(ne_lat, ne_lng, sw_lat, sw_lng):
    """
    Return hotels within map viewport
    
    Args:
        ne_lat: North-east corner latitude
        ne_lng: North-east corner longitude
        sw_lat: South-west corner latitude
        sw_lng: South-west corner longitude
    
    Returns:
        QuerySet of Property objects
    """
    from apps.hotels.models import Property
    
    return Property.objects.filter(
        latitude__gte=sw_lat,
        latitude__lte=ne_lat,
        longitude__gte=sw_lng,
        longitude__lte=ne_lng
    )


def hotels_near_point(lat, lng, radius_km=10, limit=50):
    """
    Return hotels within radius of point
    
    Uses bounding box approximation first (fast),
    then calculates exact distance (accurate)
    """
    from apps.hotels.models import Property
    
    # Rough bounding box (1 degree ≈ 111 km)
    lat_delta = Decimal(radius_km) / Decimal(111)
    lng_delta = Decimal(radius_km) / Decimal(111 * cos(radians(float(lat))))
    
    # Fast filter: bounding box
    candidates = Property.objects.filter(
        latitude__gte=lat - lat_delta,
        latitude__lte=lat + lat_delta,
        longitude__gte=lng - lng_delta,
        longitude__lte=lng + lng_delta
    )
    
    # Accurate filter: calculate exact distance
    results = []
    for hotel in candidates:
        distance = haversine_distance(lat, lng, hotel.latitude, hotel.longitude)
        if distance <= radius_km:
            hotel.distance = distance  # Attach for sorting
            results.append(hotel)
    
    # Sort by distance
    results.sort(key=lambda h: h.distance)
    return results[:limit]


def sort_hotels_by_distance(hotels, reference_lat, reference_lng):
    """
    Sort hotels by distance from reference point
    Attaches .distance attribute to each hotel
    """
    for hotel in hotels:
        hotel.distance = haversine_distance(
            reference_lat, reference_lng,
            hotel.latitude, hotel.longitude
        )
    
    return sorted(hotels, key=lambda h: h.distance)


def get_city_context(city_code):
    """
    Load entire city context (CTXCR pattern)
    
    Returns:
        {
            'city': City object,
            'localities': QuerySet of Locality,
            'bounding_box': {'ne': {...}, 'sw': {...}, 'centre': {...}},
            'hotel_count': int
        }
    """
    from apps.core.location_models import City, Locality
    from apps.hotels.models import Property
    
    try:
        city = City.objects.get(code=city_code)
    except City.DoesNotExist:
        return None
    
    localities = Locality.objects.filter(city=city, is_active=True)
    hotel_count = Property.objects.filter(city=city).count()
    
    return {
        'city': city,
        'localities': localities,
        'bounding_box': {
            'ne': {'lat': city.ne_lat, 'lng': city.ne_lng},
            'sw': {'lat': city.sw_lat, 'lng': city.sw_lng},
            'centre': {'lat': city.latitude, 'lng': city.longitude}
        },
        'hotel_count': hotel_count
    }