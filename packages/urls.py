from django.urls import path
from . import views

app_name = 'packages'

urlpatterns = [
    path('', views.list_packages, name='list'),
    path('<int:package_id>/', views.package_detail, name='detail'),
    path('<int:package_id>/book/', views.package_booking, name='booking'),
    path('booking/<uuid:booking_uuid>/', views.booking_review, name='review'),
    path('booking/<uuid:booking_uuid>/success/', views.booking_success, name='booking-success'),
    
    # Owner route
    path('owner/register/', views.owner_package_add, name='owner-add'),
]
