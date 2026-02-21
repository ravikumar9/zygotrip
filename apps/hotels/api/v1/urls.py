"""API v1 URL configuration"""

from django.urls import path
from . import views

app_name = 'hotels_api_v1'

urlpatterns = [
    path('properties/', views.property_list_api, name='property_list'),
    path('search/', views.property_search_api, name='search'),
    path('properties/<int:property_id>/', views.property_detail_api, name='property_detail'),
]