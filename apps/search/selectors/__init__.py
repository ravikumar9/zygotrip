from django.db.models import Count, Q
from hotels.models import Property
from dashboard_admin.models import PropertyApproval


def searchable_properties():
	return (
		Property.objects.filter(
			is_active=True,
			approval__status=PropertyApproval.STATUS_APPROVED,
			approval__is_active=True,
		)
		.select_related("approval", "city", "locality")
		# review_count is now a model field, not annotation
	)


def filter_search(queryset, query):
	if not query:
		return queryset.none()
	return queryset.filter(
		Q(name__icontains=query)
		| Q(city__name__icontains=query)  # FK lookup
		| Q(city_text__icontains=query)  # Fallback to old text field
		| Q(area__icontains=query)
		| Q(landmark__icontains=query)
		| Q(slug__icontains=query)
	)
