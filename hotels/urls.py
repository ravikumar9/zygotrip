from django.urls import path
from apps.hotels.views import hotel_list

app_name = 'hotels'

urlpatterns = [
    path('', hotel_list, name='list'),
]
