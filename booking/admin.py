from django.contrib import admin
from .models import Booking, BookingGuest, BookingPriceBreakdown, BookingRoom, BookingStatusHistory


admin.site.register(Booking)
admin.site.register(BookingRoom)
admin.site.register(BookingGuest)
admin.site.register(BookingPriceBreakdown)
admin.site.register(BookingStatusHistory)

# Register your models here.
