from django.urls import path
from .views import home, component_library_preview, dashboard, seed_test_data, health_check
from .marketplace_api import (
    SearchAutocompleteAPI,
    TrendingDestinationsAPI,
    CategoriesAPI,
    OffersAPI
)

app_name = 'core'

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('component-library/', component_library_preview, name='component_library_preview'),
    path('test/seed/', seed_test_data, name='seed_test_data'),
    path('health/', health_check, name='health_check'),  # PHASE 9: Health check
    
    # Marketplace API Endpoints
    path('api/search-autocomplete', SearchAutocompleteAPI.as_view(), name='api_search_autocomplete'),
    path('api/trending-destinations', TrendingDestinationsAPI.as_view(), name='api_trending_destinations'),
    path('api/categories', CategoriesAPI.as_view(), name='api_categories'),
    path('api/offers', OffersAPI.as_view(), name='api_offers'),
]