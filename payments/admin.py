from django.contrib import admin
from .models import Invoice, Payment


admin.site.register(Payment)
admin.site.register(Invoice)

# Register your models here.
