"""
URL configuration for zygotrip_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.views import serve as static_serve
from django.urls import include, path, re_path
from apps.accounts.views import LoginView, register_view, logout_view
from apps.dashboard_owner.views import add_property
from apps.cabs.dashboards import cab_create
from apps.buses.dashboards import bus_create

urlpatterns = [
    # Core routes
    path('', include('apps.core.urls')),
    
    # Auth routes - with explicit names matching template references
    path('login/', LoginView.as_view(), name='account_login'),
    path('register/', register_view, name='account_register'),  # User registration
    path('logout/', logout_view, name='account_logout'),
    
    # Accounts with namespace
    path('accounts/', include('apps.accounts.urls')),
    
    # Hotels with namespace AND backwards-compatible names
    path('hotels/', include('apps.hotels.urls')),
    
    # Search
    path('search/', include('apps.search.urls')),
    
    # Other apps
    path('buses/', include('apps.buses.urls')),
    path('packages/', include('apps.packages.urls')),
    path('flights/', include('apps.flights.urls')),
    path('trains/', include('apps.trains.urls')),
    path('cabs/', include('apps.cabs.urls')),
    
    # APIs (all consolidated into apps.search and apps.hotels)
    path('api/v1/', include('apps.hotels.api.v1.urls')),
    
    # Registration and Booking
    path('register/property/', include('apps.registration.urls')),
    path('booking/', include('apps.booking.urls')),
    path('invoice/', include('apps.payments.urls')),
    
    # Owner/Vendor dashboards
    path('owner/property/create/', add_property, name='owner_property_create'),
    path('vendor/cab/create/', cab_create, name='vendor_cab_create'),
    path('vendor/bus/create/', bus_create, name='vendor_bus_create'),
    path('owner/dashboard/', include('apps.dashboard_owner.urls')),
    path('admin/dashboard/', include('apps.dashboard_admin.urls')),
    path('finance/dashboard/', include('apps.dashboard_finance.urls')),
    path('admin/', admin.site.urls),
]

handler403 = 'apps.core.views.permission_denied'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", static_serve, kwargs={"insecure": True}),
    ]