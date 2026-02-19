"""
URL Configuration for Search APIs
Maps intelligent search endpoints
"""
from django.urls import path
from core.search_api import (
    autocomplete_api,
    hotel_search_api,
    map_results_api,
    city_context_api
)

app_name = 'search_api'

urlpatterns = [
    # Autocomplete: /api/search/autocomplete/?q=coor
    path('autocomplete/', autocomplete_api, name='autocomplete'),
    
    # Hotel search: /api/search/hotels/?city_id=1&price_max=5000&sort_by=rating
    path('hotels/', hotel_search_api, name='hotel_search'),
    
    # Map results: /api/search/map/?ne_lat=12.5&ne_lng=77.6&sw_lat=12.3&sw_lng=77.4
    path('map/', map_results_api, name='map_results'),
    
    # City context: /api/search/city/COORG/
    path('city/<str:city_code>/', city_context_api, name='city_context'),
]
