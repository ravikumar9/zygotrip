from django.urls import path
from . import views

app_name = 'packages'

urlpatterns = [
    path('', views.list_packages, name='list'),
    path('<int:package_id>/', views.package_detail, name='detail'),
    path('booking/<uuid:booking_uuid>/', views.booking_review, name='review'),
]
