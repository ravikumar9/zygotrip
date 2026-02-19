from django.db.models import Count, Min, Q
from dashboard_admin.models import PropertyApproval
from apps.hotels.models import Property


def public_properties_queryset():
	return (
		Property.objects.filter(
			is_active=True,
			approval__status=PropertyApproval.STATUS_APPROVED,
			approval__is_active=True,
		)
		.select_related("approval", "owner", "city", "locality")
		.prefetch_related("images", "amenities", "policies", "offers")
		.annotate(
			min_room_price=Min("room_types__base_price"),
			# review_count is now a model field, not an annotation
		)
	)


def get_property_detail(pk):
	return (
		Property.objects.filter(
			pk=pk,
			is_active=True,
			approval__status=PropertyApproval.STATUS_APPROVED,
			approval__is_active=True,
		)
		.select_related("approval", "owner")
		.prefetch_related(
			"images",
			"amenities",
			"policies",
			"offers",
			"room_types",
			"meal_plans",
		)
		.first()
	)


def apply_hotel_filters(queryset, params):
	search_query = (params.get("q") or "").strip()
	selected_cities = [city.strip() for city in params.getlist("city") if city.strip()]
	selected_ratings = [rating.strip() for rating in params.getlist("rating") if rating.strip()]
	selected_amenities = [amenity.strip() for amenity in params.getlist("amenities") if amenity.strip()]
	min_price = params.get("min_price") or ""
	max_price = params.get("max_price") or ""
	selected_category = (params.get("category") or "").strip()

	if search_query:
		queryset = queryset.filter(
			Q(name__icontains=search_query)
			| Q(city__name__icontains=search_query)
			| Q(city__display_name__icontains=search_query)
			| Q(city_text__icontains=search_query)
			| Q(legacy_city__icontains=search_query)
			| Q(area__icontains=search_query)
			| Q(landmark__icontains=search_query)
			| Q(slug__icontains=search_query)
		)

	if selected_cities:
		city_query = Q()
		for city in selected_cities:
			city_query |= Q(city__name__iexact=city)
			city_query |= Q(city__display_name__iexact=city)
			city_query |= Q(city_text__iexact=city)
			city_query |= Q(legacy_city__iexact=city)
		queryset = queryset.filter(city_query)

	if selected_ratings:
		try:
			rating_thresholds = [float(value) for value in selected_ratings]
			min_rating = min(rating_thresholds)
			queryset = queryset.filter(rating__gte=min_rating)
		except (ValueError, TypeError):
			pass

	if min_price:
		try:
			from decimal import Decimal, InvalidOperation
			min_price_decimal = Decimal(str(min_price).strip())
			queryset = queryset.filter(base_price__gte=min_price_decimal)
		except (ValueError, TypeError, InvalidOperation):
			pass

	if max_price:
		try:
			from decimal import Decimal, InvalidOperation
			max_price_decimal = Decimal(str(max_price).strip())
			queryset = queryset.filter(base_price__lte=max_price_decimal)
		except (ValueError, TypeError, InvalidOperation):
			pass

	if selected_amenities:
		amenity_map = {
			"wifi": "Free WiFi",
			"breakfast": "Breakfast Included",
			"pool": "Pool",
			"parking": "Parking",
		}
		amenity_names = [amenity_map.get(value, value) for value in selected_amenities]
		queryset = queryset.filter(amenities__name__in=amenity_names).distinct()

	if selected_category:
		queryset = queryset.filter(categories__category__slug=selected_category)

	return {
		"queryset": queryset,
		"search_query": search_query,
		"selected_cities": selected_cities,
		"selected_ratings": selected_ratings,
		"selected_amenities": selected_amenities,
		"min_price": min_price,
		"max_price": max_price,
		"selected_category": selected_category,
	}
