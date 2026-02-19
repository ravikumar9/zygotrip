from django.urls import path
from .views import (
    add_meal, add_property, add_room, dashboard, set_price, submit_approval,
    add_property_image, add_room_image, add_offer, update_ratings
)

app_name = 'dashboard_owner'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('properties/add/', add_property, name='add_property'),
    path('properties/<int:property_id>/rooms/add/', add_room, name='add_room'),
    path('properties/<int:property_id>/meals/add/', add_meal, name='add_meal'),
    path('properties/<int:property_id>/images/add/', add_property_image, name='add_property_image'),
    path('properties/<int:property_id>/offers/add/', add_offer, name='add_offer'),
    path('properties/<int:property_id>/ratings/update/', update_ratings, name='update_ratings'),
    path('rooms/<int:room_id>/price/', set_price, name='set_price'),
    path('rooms/<int:room_id>/images/add/', add_room_image, name='add_room_image'),
]
