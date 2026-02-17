from django.db.models import Q
from cabs.models import Cab


def active_cabs_queryset():
	return (
		Cab.objects.filter(is_active=True)
		.select_related("owner")
		.prefetch_related("images")
		.order_by("-created_at")
	)


def apply_cab_filters(queryset, params):
	search_query = (params.get("q") or "").strip()
	selected_cities = params.getlist("city") or []
	selected_seats = params.getlist("seats") or []
	selected_fuels = params.getlist("fuel_type") or []
	min_price = params.get("min_price") or ""
	max_price = params.get("max_price") or ""

	if search_query:
		queryset = queryset.filter(Q(name__icontains=search_query))
	if selected_cities:
		queryset = queryset.filter(city__in=selected_cities)
	if selected_seats:
		try:
			selected_seats = [int(seats) for seats in selected_seats]
			queryset = queryset.filter(seats__in=selected_seats)
		except (ValueError, TypeError):
			selected_seats = []
	if selected_fuels:
		queryset = queryset.filter(fuel_type__in=selected_fuels)
	if max_price:
		try:
			queryset = queryset.filter(system_price_per_km__lte=max_price)
		except (ValueError, TypeError):
			max_price = ""
	if min_price:
		try:
			queryset = queryset.filter(system_price_per_km__gte=min_price)
		except (ValueError, TypeError):
			min_price = ""

	return {
		"queryset": queryset,
		"search_query": search_query,
		"selected_cities": selected_cities,
		"selected_seats": selected_seats,
		"selected_fuels": selected_fuels,
		"min_price": min_price,
		"max_price": max_price,
	}
