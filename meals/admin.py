from django.contrib import admin
from .models import MealPlan


class MealPlanAdmin(admin.ModelAdmin):
	fieldsets = (
		('Basic Info', {
			'fields': ('property', 'meal_type', 'name', 'description')
		}),
		('Pricing & Display', {
			'fields': ('price', 'icon'),
			'description': 'Price per meal and icon/emoji for display'
		}),
	)
	list_display = ('meal_type', 'property', 'name', 'price', 'icon')
	list_filter = ('property', 'meal_type')
	search_fields = ('name', 'property__name')


admin.site.register(MealPlan, MealPlanAdmin)

# Register your models here.
