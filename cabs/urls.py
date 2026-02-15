from django.urls import path
from . import views

app_name = 'cabs'

urlpatterns = [
    path('', views.coming_soon, name='list'),
]
