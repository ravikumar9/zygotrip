from django.contrib import admin
from .models import Review


class ReviewAdmin(admin.ModelAdmin):
	fieldsets = (
		('Review Info', {
			'fields': ('property', 'user', 'rating', 'title', 'comment', 'is_verified_booking')
		}),
		('Media', {
			'fields': ('image_url', 'image_file'),
			'description': 'Upload review image or provide URL'
		}),
		('Moderation', {
			'fields': ('status',),
			'description': 'Approve or reject reviews before they appear on site'
		}),
	)
	list_display = ('user', 'property', 'rating', 'status', 'is_verified_booking', 'created_at')
	list_filter = ('status', 'rating', 'property', 'is_verified_booking')
	search_fields = ('user__email', 'property__name', 'comment', 'title')
	readonly_fields = ('created_at', 'updated_at')
	actions = ['approve_reviews', 'reject_reviews']
	
	def approve_reviews(self, request, queryset):
		updated = queryset.update(status=Review.STATUS_APPROVED)
		self.message_user(request, f'{updated} reviews approved.')
	approve_reviews.short_description = 'Approve selected reviews'
	
	def reject_reviews(self, request, queryset):
		updated = queryset.update(status=Review.STATUS_REJECTED)
		self.message_user(request, f'{updated} reviews rejected.')
	reject_reviews.short_description = 'Reject selected reviews'


admin.site.register(Review, ReviewAdmin)

# Register your models here.
