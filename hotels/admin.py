from django.contrib import admin
from .models import (
    Property, PropertyAmenity, PropertyImage, PropertyPolicy,
    PropertyOffer, RatingAggregate, Category, PropertyCategory
)
from rooms.models import RoomType, RoomImage
from meals.models import MealPlan


class PropertyImageInline(admin.TabularInline):
	model = PropertyImage
	extra = 1
	fields = ('image_url', 'caption', 'is_featured', 'display_order')


class PropertyAmenityInline(admin.TabularInline):
	model = PropertyAmenity
	extra = 1
	fields = ('name', 'icon')


class PropertyPolicyInline(admin.TabularInline):
	model = PropertyPolicy
	extra = 1
	fields = ('title', 'description')


class RoomTypeInline(admin.TabularInline):
	model = RoomType
	extra = 0
	fields = ('name', 'max_guests', 'base_price')


class PropertyOfferInline(admin.TabularInline):
	model = PropertyOffer
	extra = 0
	fields = ('title', 'discount_percentage', 'valid_from', 'valid_until', 'is_active')


class PropertyAdmin(admin.ModelAdmin):
	fieldsets = (
		('Basic Info', {
			'fields': ('name', 'owner', 'city', 'country', 'address', 'description', 'rating')
		}),
		('Location (Google Maps)', {
			'fields': ('latitude', 'longitude'),
			'description': 'Enter property coordinates for map display'
		}),
		('Note', {
			'description': 'Pricing is managed via RoomType model (room types below). Property-level pricing removed as part of architectural refactor.'
		}),
	)
	list_display = ('name', 'city', 'owner', 'rating')
	list_filter = ('city', 'country', 'rating')
	search_fields = ('name', 'address')
	inlines = [PropertyImageInline, RoomTypeInline, PropertyOfferInline, PropertyAmenityInline, PropertyPolicyInline]


class RoomImageInline(admin.TabularInline):
	model = RoomImage
	extra = 1
	fields = ('image_url', 'is_featured', 'display_order')


# RoomType and MealPlan are already registered in their respective apps (rooms, meals)


@admin.register(PropertyOffer)
class PropertyOfferAdmin(admin.ModelAdmin):
	list_display = ('property', 'title', 'discount_percentage', 'valid_from', 'valid_until', 'is_active')
	list_filter = ('is_active', 'valid_from', 'valid_until')
	search_fields = ('title', 'code', 'property__name')


@admin.register(RatingAggregate)
class RatingAggregateAdmin(admin.ModelAdmin):
	list_display = ('property', 'cleanliness', 'service', 'location', 'amenities', 'value_for_money', 'total_reviews')
	search_fields = ('property__name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug', 'icon')
	prepopulated_fields = {'slug': ('name',)}


admin.site.register(Property, PropertyAdmin)
admin.site.register(PropertyImage)
admin.site.register(PropertyPolicy)
admin.site.register(PropertyAmenity)
