from django.urls import path
from . import views

app_name = 'flights'

urlpatterns = [
    path('', views.coming_soon, name='list'),
]