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
from django.urls import include, path

urlpatterns = [
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('hotels/', include('hotels.urls')),
    path('buses/', include('buses.urls')),
    path('packages/', include('packages.urls')),
    path('flights/', include('flights.urls')),
    path('trains/', include('trains.urls')),
    path('cabs/', include('cabs.urls')),
    path('booking/', include('booking.urls')),
    path('invoice/', include('payments.urls')),
    path('owner/dashboard/', include('dashboard_owner.urls')),
    path('admin/dashboard/', include('dashboard_admin.urls')),
    path('finance/dashboard/', include('dashboard_finance.urls')),
    path('admin/', admin.site.urls),
]

handler403 = 'core.views.permission_denied'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
