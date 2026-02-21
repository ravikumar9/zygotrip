from django.contrib import admin
from .models import Booking, BookingGuest, BookingPriceBreakdown, BookingStatusHistory


admin.site.register(Booking)
# admin.site.register(BookingRoom)  # Model is commented out in models.py
admin.site.register(BookingGuest)
admin.site.register(BookingPriceBreakdown)
admin.site.register(BookingStatusHistory)

# Register your models here.