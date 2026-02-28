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
from django.views.generic import TemplateView
from apps.accounts.views import (
    LoginView, register_view, logout_view,
    register_traveler, register_property_owner, register_cab_owner,
    register_bus_operator, register_package_provider
)
from apps.search.views_production import cities_autocomplete, location_autocomplete, search_index_api
from apps.hotels.api import suggest_hotels
from apps.dashboard_owner.views import add_property
from apps.cabs.dashboards import cab_create
from apps.buses.dashboards import bus_create

urlpatterns = [
    # Core routes
    path('', include('apps.core.urls')),
    
    # Auth routes - with explicit names matching template references
    path('login/', LoginView.as_view(), name='account_login'),
    path('logout/', logout_view, name='account_logout'),
    
    # Generic registration (redirects to traveler)
    path('register/', register_view, name='account_register'),
    
    # ========================================
    # PHASE B: ROLE-SPECIFIC ENTRY POINTS
    # ========================================
    path('register/traveler/', register_traveler, name='register_traveler'),
    path('register/property-owner/', register_property_owner, name='register_property_owner'),
    path('register/cab-owner/', register_cab_owner, name='register_cab_owner'),
    path('register/bus-operator/', register_bus_operator, name='register_bus_operator'),
    path('register/package-provider/', register_package_provider, name='register_package_provider'),
    
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
    path('api/hotels/suggest/', suggest_hotels, name='api_hotels_suggest'),
    path('api/search/', search_index_api, name='search_index_api'),
    path('api/cities/', cities_autocomplete, name='cities_autocomplete'),
    path('api/locations/', location_autocomplete, name='location_autocomplete'),
    
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

    # Legal pages
    path('privacy/', TemplateView.as_view(template_name='legal/privacy.html'), name='privacy_policy'),
    path('terms/', TemplateView.as_view(template_name='legal/terms.html'), name='terms_of_service'),
]

handler403 = 'apps.core.views.permission_denied'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", static_serve, kwargs={"insecure": True}),
    ]