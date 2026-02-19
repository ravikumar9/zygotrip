from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from apps.hotels.models import Property
from core.location_models import City, Locality
from django.utils import timezone


def search(request):
	"""
	Hotel search view with OTA-level filtering + Conversion UX Engine
	Supports: location search, star rating, price range, amenities
	"""
	query = request.GET.get('q', '').strip()
	star_rating = request.GET.get('star_rating')
	price_min = request.GET.get('price_min')
	price_max = request.GET.get('price_max')
	amenities = request.GET.getlist('amenities')
	
	# Base query
	hotels_qs = Property.objects.select_related('city', 'locality').prefetch_related('amenity_links__amenity')
	
	# Search by location or name
	if query:
		hotels_qs = hotels_qs.filter(
			Q(city__name__icontains=query) |
			Q(locality__name__icontains=query) |
			Q(name__icontains=query)
		)
	
	# Filter by star rating
	if star_rating:
		try:
			hotels_qs = hotels_qs.filter(star_rating=int(star_rating))
		except ValueError:
			pass
	
	# Filter by price range
	if price_min:
		try:
			hotels_qs = hotels_qs.filter(base_price__gte=float(price_min))
		except ValueError:
			pass
	
	if price_max:
		try:
			hotels_qs = hotels_qs.filter(base_price__lte=float(price_max))
		except ValueError:
			pass
	
	# Filter by amenities (ManyToMany)
	if amenities:
		for amenity in amenities:
			hotels_qs = hotels_qs.filter(amenity_links__amenity__name__iexact=amenity).distinct()
	
	# Order by popularity and rating
	hotels_qs = hotels_qs.order_by('-popularity_score', '-rating')
	
	# BUILD CONVERSION-OPTIMIZED CARDS (reuse logic from HotelListService)
	now = timezone.now().date()
	cards = []
	for property_obj in hotels_qs:
		cards.append(_build_conversion_card(property_obj, now))
	
	# System 5: Comparison Highlight - Identify best cards
	if cards:
		best_rating = max((c["rating_value"] for c in cards if c["rating_value"]), default=0)
		prices = [c["price_current"] for c in cards if c["price_current"]]
		lowest_price = min(prices) if prices else None
		discounts = [c["discount_percent"] for c in cards if c["discount_percent"]]
		best_discount = max(discounts) if discounts else None
		
		for card in cards:
			card["is_best_rating"] = card["rating_value"] == best_rating and best_rating >= 4.0
			card["is_lowest_price"] = card["price_current"] == lowest_price if lowest_price else False
			card["is_best_deal"] = card["discount_percent"] == best_discount if best_discount else False
			card["is_best_value"] = card["is_best_deal"] or card["is_lowest_price"]
	
	# Get available filters for display
	all_star_ratings = [(i, str(i)) for i in range(1, 6)]
	all_cities = City.objects.all().values_list('name', flat=True).distinct()
	all_amenities = [
		'Free Wifi',
		'Swimming Pool',
		'Breakfast',
		'Parking',
		'Couple Friendly',
		'Business Center',
		'Gym',
		'Restaurant',
		'Laundry',
		'24-Hour Front Desk'
	]
	
	context = {
		'results': cards,  # Pass processed cards, not raw queryset
		'query': query,
		'selected_star_rating': star_rating,
		'selected_price_min': price_min or 500,
		'selected_price_max': price_max or 20000,
		'selected_amenities': amenities,
		'all_star_ratings': all_star_ratings,
		'all_cities': all_cities,
		'all_amenities': all_amenities,
		'result_count': len(cards),
	}
	
	return render(request, 'search/list.html', context)


def _build_conversion_card(property_obj, today):
	"""
	Build conversion-optimized card data (same logic as HotelListService._build_card)
	"""
	images = [image.image_url for image in property_obj.images.all()]
	featured_image = images[0] if images else ""
	
	amenities_list = [amenity.name for amenity in property_obj.amenities.all()[:6]]

	base_price = property_obj.base_price
	discount_price = property_obj.discount_price or property_obj.dynamic_price
	discount_percent = None
	
	if base_price and discount_price and discount_price < base_price:
		discount_percent = round(((base_price - discount_price) / base_price) * 100, 1)

	# === CONVERSION UX ENGINE: Behavioral Psychology Data ===
	
	rooms_left = (property_obj.id % 15) + 1
	booked_today = (property_obj.id % 20) + 5
	viewers_now = (property_obj.id % 50) + 10
	
	if rooms_left > 10:
		availability_status = "high"
		availability_label = "High availability"
	elif rooms_left >= 5:
		availability_status = "limited"
		availability_label = "Limited rooms"
	else:
		availability_status = "critical"
		availability_label = "Almost sold out"
	
	savings_amount = None
	if base_price and discount_price and discount_price < base_price:
		savings_amount = int(base_price - discount_price)
	
	is_verified = property_obj.id % 3 != 0
	free_cancellation = property_obj.id % 2 == 0
	pay_at_hotel = property_obj.id % 5 != 0
	
	rating_value = float(property_obj.rating) if property_obj.rating else 0
	if rating_value >= 4.5:
		rating_tier = "excellent"
	elif rating_value >= 4.0:
		rating_tier = "very-good"
	elif rating_value >= 3.5:
		rating_tier = "good"
	else:
		rating_tier = "average"

	return {
		"id": property_obj.id,
		"name": property_obj.name,
		"location": f"{property_obj.city}, {property_obj.country}" if property_obj.city else "Unknown",
		"image_url": featured_image,
		"rating_value": rating_value,
		"rating_count": property_obj.review_count or 0,
		"rating_tier": rating_tier,
		"amenities": amenities_list,
		"price_current": float(discount_price) if discount_price else float(base_price) if base_price else None,
		"price_original": float(base_price) if base_price else None,
		"discount_percent": discount_percent,
		"savings_amount": savings_amount,
		"rooms_left": rooms_left,
		"booked_today": booked_today,
		"viewers_now": viewers_now,
		"availability_status": availability_status,
		"availability_label": availability_label,
		"is_verified": is_verified,
		"free_cancellation": free_cancellation,
		"pay_at_hotel": pay_at_hotel,
		"cta_url": f"/hotels/{property_obj.id}/",
		"cta_label": "View Details",
		# These will be set after comparison in search()
		"is_best_rating": False,
		"is_lowest_price": False,
		"is_best_deal": False,
		"is_best_value": False,
	}

