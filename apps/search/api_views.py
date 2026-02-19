# Location autocomplete endpoints
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET
from apps.hotels.models import Property
from core.location_models import City, Locality


@require_GET
def autocomplete_locations(request):
	"""
	AJAX endpoint for location autocomplete
	Returns cities, localities, and hotels matching query
	GET /api/locations/autocomplete/?q=coo
	"""
	query = request.GET.get('q', '').strip()
	
	if not query or len(query) < 2:
		return JsonResponse({'results': []})
	
	results = []
	
	# Search cities
	cities = City.objects.filter(name__icontains=query).values('id', 'name')[:5]
	for city in cities:
		results.append({
			'type': 'city',
			'id': city['id'],
			'name': city['name'],
			'display': f"📍 {city['name']} (City)"
		})
	
	# Search localities
	localities = Locality.objects.filter(name__icontains=query).values('id', 'name', 'city__name')[:5]
	for loc in localities:
		results.append({
			'type': 'locality',
			'id': loc['id'],
			'name': loc['name'],
			'city': loc['city__name'],
			'display': f"📍 {loc['name']}, {loc['city__name']}"
		})
	
	# Search hotels
	hotels = Property.objects.filter(
		Q(name__icontains=query) | Q(city__name__icontains=query) | Q(locality__name__icontains=query)
	).select_related('city', 'locality').values('id', 'slug', 'name', 'city__name', 'locality__name')[:5]
	
	for hotel in hotels:
		location = hotel['locality__name'] or hotel['city__name']
		results.append({
			'type': 'hotel',
			'id': hotel['id'],
			'slug': hotel['slug'],
			'name': hotel['name'],
			'location': location,
			'display': f"🏨 {hotel['name']}, {location}"
		})
	
	return JsonResponse({'results': results})


@require_GET
def search_hotels(request):
	"""
	Main hotel search view with advanced filtering
	GET /search/hotels/?q=coorg&star_rating=3&price_max=5000&amenities=wifi,pool
	"""
	query = request.GET.get('q', '').strip()
	star_rating = request.GET.get('star_rating')
	price_min = request.GET.get('price_min')
	price_max = request.GET.get('price_max')
	amenities = request.GET.getlist('amenities')
	
	# Base query: filter by search term
	hotels = Property.objects.select_related('city', 'locality').prefetch_related('amenity_links__amenity')
	
	if query:
		hotels = hotels.filter(
			Q(city__name__icontains=query) |
			Q(locality__name__icontains=query) |
			Q(name__icontains=query)
		)
	
	# Star rating filter
	if star_rating:
		try:
			hotels = hotels.filter(star_rating=int(star_rating))
		except ValueError:
			pass
	
	# Price range filter
	if price_min:
		try:
			hotels = hotels.filter(base_price__gte=float(price_min))
		except ValueError:
			pass
	
	if price_max:
		try:
			hotels = hotels.filter(base_price__lte=float(price_max))
		except ValueError:
			pass
	
	# Amenities filter (ManyToMany) - disabled for now
	# if amenities:
	#     for amenity in amenities:
	#         hotels = hotels.filter(amenity_links__amenity__name__iexact=amenity).distinct()
	
	# Order by popularity/relevance
	hotels = hotels.order_by('-popularity_score', '-rating')
	
	# Pagination
	page = int(request.GET.get('page', 1))
	per_page = 20
	start = (page - 1) * per_page
	end = start + per_page
	
	total = hotels.count()
	hotels_page = hotels[start:end]
	
	# Build response
	results = []
	for hotel in hotels_page:
		results.append({
			'id': hotel.id,
			'name': hotel.name,
			'slug': hotel.slug,
			'city_id': hotel.city_id,
			'city': hotel.city.name,
			'locality': hotel.locality.name if hotel.locality else '',
			'star_rating': hotel.star_rating,
			'rating': float(hotel.rating),
			'review_count': hotel.review_count,
			'base_price': float(hotel.base_price),
			'address': hotel.address,
			'latitude': float(hotel.latitude),
			'longitude': float(hotel.longitude),
		})
	
	return JsonResponse({
		'results': results,
		'total': total,
		'page': page,
		'pages': (total + per_page - 1) // per_page
	})
