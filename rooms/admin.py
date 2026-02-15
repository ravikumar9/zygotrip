from django.contrib import admin
from .models import RoomImage, RoomInventory, RoomType, RoomAmenity


class RoomImageInline(admin.TabularInline):
	model = RoomImage
	extra = 1
	fields = ('image_url', 'image_file', 'is_featured', 'display_order')


class RoomAmenityInline(admin.TabularInline):
	model = RoomAmenity
	extra = 1
	fields = ('name', 'icon')


class RoomTypeAdmin(admin.ModelAdmin):
	fieldsets = (
		('Basic Info', {
			'fields': ('property', 'name', 'description', 'base_price')
		}),
		('Room Details', {
			'fields': ('bed_type', 'max_guests', 'room_size_sqm'),
			'description': 'Bed type, guest capacity, and size information'
		}),
	)
	list_display = ('name', 'property', 'base_price', 'bed_type', 'max_guests', 'room_size_sqm')
	list_filter = ('property', 'bed_type')
	search_fields = ('name', 'property__name')
	inlines = [RoomImageInline, RoomAmenityInline]


class RoomInventoryAdmin(admin.ModelAdmin):
	list_display = ('room_type', 'date', 'available_count')
	list_filter = ('room_type', 'date')
	search_fields = ('room_type__name',)


admin.site.register(RoomType, RoomTypeAdmin)
admin.site.register(RoomImage)
admin.site.register(RoomAmenity)
admin.site.register(RoomInventory, RoomInventoryAdmin)

# Register your models here.
