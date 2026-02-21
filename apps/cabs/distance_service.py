# cabs/distance_service.py - Distance calculation service

from geopy.distance import geodesic
from geopy.geocoders import Nominatim


# City coordinates (latitude, longitude) - approximate for Indian cities
CITY_COORDINATES = {
    'delhi': (28.7041, 77.1025),
    'mumbai': (19.0760, 72.8777),
    'bangalore': (12.9716, 77.5946),
    'jaipur': (26.9124, 75.7873),
    'pune': (18.5204, 73.8567),
    'hyderabad': (17.3850, 78.4867),
    'kolkata': (22.5726, 88.3639),
    'ahmedabad': (23.0225, 72.5714),
    'goa': (15.2993, 73.8243),
    'chandigarh': (30.7333, 76.7794),
    'lucknow': (26.8467, 80.9462),
    'surat': (21.1458, 72.1941),
}


class DistanceCalculationError(Exception):
    """Raised when distance calculation fails"""
    pass


def normalize_city_name(city_name):
    """Normalize city name to lowercase"""
    return city_name.strip().lower() if city_name else ''


def get_city_coordinates(city_name):
    """
    Get coordinates for a city.
    
    Args:
        city_name: City name (string)
    
    Returns:
        tuple: (latitude, longitude) or raises DistanceCalculationError
    """
    normalized_city = normalize_city_name(city_name)
    
    if normalized_city not in CITY_COORDINATES:
        raise DistanceCalculationError(
            f"City '{city_name}' coordinates not available. "
            f"Supported cities: {', '.join(CITY_COORDINATES.keys())}"
        )
    
    return CITY_COORDINATES[normalized_city]


def calculate_distance(from_city, to_city):
    """
    Calculate distance between two cities using coordinates.
    
    Args:
        from_city: Source city name
        to_city: Destination city name
    
    Returns:
        float: Distance in kilometers (rounded to 1 decimal)
    
    Raises:
        DistanceCalculationError: If cities not found or distance calc fails
    """
    try:
        from_coords = get_city_coordinates(from_city)
        to_coords = get_city_coordinates(to_city)
        
        # Using geodesic distance (in km)
        distance_km = geodesic(from_coords, to_coords).kilometers
        
        # Round to 1 decimal place
        return round(distance_km, 1)
    
    except DistanceCalculationError:
        raise
    except Exception as e:
        raise DistanceCalculationError(f"Distance calculation failed: {str(e)}")


def validate_route(from_city, to_city):
    """
    Validate that a route is calculable.
    
    Returns:
        tuple: (valid: bool, distance: float or None, error_message: str or None)
    """
    try:
        distance = calculate_distance(from_city, to_city)
        return True, distance, None
    except DistanceCalculationError as e:
        return False, None, str(e)


def calculate_fare(from_city, to_city, base_price_per_km):
    """
    Calculate cab fare based on distance and base price.
    
    Args:
        from_city: Source city
        to_city: Destination city
        base_price_per_km: Base price per km (Decimal)
    
    Returns:
        dict: {
            'distance_km': float,
            'base_fare': Decimal,
            'platform_margin': Decimal,  # ₹3 margin
            'total_fare': Decimal
        }
    
    Raises:
        DistanceCalculationError: If route calculation fails
    """
    from decimal import Decimal
    
    distance = calculate_distance(from_city, to_city)
    base_fare = Decimal(str(distance)) * base_price_per_km
    platform_margin = Decimal('3.00')  # ₹3 platform margin
    total_fare = base_fare + platform_margin
    
    return {
        'distance_km': distance,
        'base_fare': base_fare,
        'platform_margin': platform_margin,
        'total_fare': total_fare,
    }