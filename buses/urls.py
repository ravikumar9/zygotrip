from django.urls import path
from . import views

app_name = 'buses'

urlpatterns = [
    path('', views.list_buses, name='list'),
    path('<int:bus_id>/', views.bus_detail, name='detail'),
    path('booking/<uuid:booking_uuid>/', views.booking_review, name='review'),
]
