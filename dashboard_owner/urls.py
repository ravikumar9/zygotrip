from django.urls import path
from .views import add_meal, add_property, add_room, dashboard, set_price, submit_approval

app_name = 'dashboard_owner'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('properties/add/', add_property, name='add_property'),
    path('properties/<int:property_id>/rooms/add/', add_room, name='add_room'),
    path('properties/<int:property_id>/meals/add/', add_meal, name='add_meal'),
    path('rooms/<int:room_id>/price/', set_price, name='set_price'),
    path('properties/<int:property_id>/submit/', submit_approval, name='submit_approval'),
]
