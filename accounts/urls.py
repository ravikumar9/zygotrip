from django.urls import path
from .views import LoginView, logout_view, profile

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', profile, name='profile'),
    path('logout/', logout_view, name='logout'),
]
