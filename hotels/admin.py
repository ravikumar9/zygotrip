from django.contrib import admin
from .models import Property, PropertyAmenity, PropertyImage, PropertyPolicy


class PropertyImageInline(admin.TabularInline):
	model = PropertyImage
	extra = 1
	fields = ('image_url', 'is_featured')


class PropertyAmenityInline(admin.TabularInline):
	model = PropertyAmenity
	extra = 1
	fields = ('name', 'icon')


class PropertyPolicyInline(admin.TabularInline):
	model = PropertyPolicy
	extra = 1
	fields = ('title', 'description')


class PropertyAdmin(admin.ModelAdmin):
	fieldsets = (
		('Basic Info', {
			'fields': ('name', 'owner', 'city', 'country', 'address', 'description', 'rating')
		}),
		('Location (Google Maps)', {
			'fields': ('latitude', 'longitude'),
			'description': 'Enter property coordinates for map display'
		}),
		('Pricing', {
			'fields': ('base_price', 'discount_price', 'dynamic_price'),
			'description': 'Set base, discount, and dynamic pricing'
		}),
	)
	list_display = ('name', 'city', 'owner', 'rating', 'latitude', 'longitude')
	list_filter = ('city', 'country', 'rating')
	search_fields = ('name', 'address')
	inlines = [PropertyImageInline, PropertyAmenityInline, PropertyPolicyInline]


admin.site.register(Property, PropertyAdmin)
admin.site.register(PropertyImage)
admin.site.register(PropertyPolicy)
admin.site.register(PropertyAmenity)

# Register your models here.
