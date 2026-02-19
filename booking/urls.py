from django.urls import path
from .views import create, payment, review, success, cancel

app_name = 'booking'

urlpatterns = [
    path('property/<int:property_id>/', create, name='create'),
    path('<uuid:uuid>/review/', review, name='review'),
    path('<uuid:uuid>/payment/', payment, name='payment'),
    path('<uuid:uuid>/success/', success, name='success'),
    path('<uuid:uuid>/cancel/', cancel, name='cancel'),
]
