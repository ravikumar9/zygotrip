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
		.select_related("approval")
		.annotate(review_count=Count("reviews", distinct=True))
	)


def filter_search(queryset, query):
	if not query:
		return queryset.none()
	return queryset.filter(
		Q(name__icontains=query)
		| Q(city__icontains=query)
		| Q(area__icontains=query)
		| Q(landmark__icontains=query)
		| Q(slug__icontains=query)
	)
