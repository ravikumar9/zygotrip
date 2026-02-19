"""
REST API v1 - Property Search & Detail
JSON endpoints for API-first architecture

Endpoints:
- GET /api/v1/properties/ - List all properties with filters
- GET /api/v1/search/ - Search with ranking algorithm
- GET /api/v1/properties/<id>/ - Property detail with room types
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.utils import timezone
from apps.hotels.selectors import public_properties_queryset, apply_hotel_filters
from apps.hotels.search import SearchRankingService
import logging

logger = logging.getLogger(__name__)


@require_GET
def property_list_api(request):
	"""
	GET /api/v1/properties/
	
	Query params:
	- page: int (default 1)
	- page_size: int (default 20, max 100)
	- city: str (filter by city)
	- min_price: decimal
	- max_price: decimal
	- rating: str (e.g., "4.5")
	- amenities: str (comma-separated)
	
	Returns:
	{
		"results": [...],
		"pagination": {"page": 1, "total_pages": 5, "total_results": 87},
		"meta": {"query_time_ms": 45}
	}
	"""
	try:
		start_time = timezone.now()
		
		# Pagination
		page = int(request.GET.get('page', 1))
		page_size = min(int(request.GET.get('page_size', 20)), 100)
		
		# Base queryset with prefetch
		qs = public_properties_queryset().prefetch_related(
			'images', 'amenities', 'room_types', 'offers'
		)
		
		# Apply filters
		filter_data = apply_hotel_filters(qs, request.GET)
		queryset = filter_data['queryset']
		
		# Paginate
		paginator = Paginator(queryset, page_size)
		page_obj = paginator.get_page(page)
		
		# Serialize results
		results = []
		for property_obj in page_obj.object_list:
			results.append(_serialize_property_card(property_obj))
		
		query_time = (timezone.now() - start_time).total_seconds() * 1000
		
		return JsonResponse({
			'results': results,
			'pagination': {
				'page': page_obj.number,
				'total_pages': paginator.num_pages,
				'total_results': paginator.count,
				'has_next': page_obj.has_next(),
				'has_previous': page_obj.has_previous(),
			},
			'meta': {
				'query_time_ms': round(query_time, 2),
				'filters_applied': {
					'city': filter_data.get('selected_cities', []),
					'rating': filter_data.get('selected_ratings', []),
					'price_range': {
						'min': filter_data.get('min_price'),
						'max': filter_data.get('max_price'),
					}
				}
			}
		})
	except Exception as exc:
		logger.exception("API property_list_api error", exc_info=exc)
		return JsonResponse({'error': 'Internal server error'}, status=500)


@require_GET
def property_search_api(request):
	"""
	GET /api/v1/search/
	
	Search with intelligent ranking algorithm
	
	Query params:
	- q: str (search query)
	- lat: float (user latitude for distance scoring)
	- lng: float (user longitude)
	- city: str
	- min_price, max_price, rating, amenities (same as list)
	- page, page_size
	
	Returns: Same structure as property_list_api with relevance_score
	"""
	try:
		start_time = timezone.now()
		
		page = int(request.GET.get('page', 1))
		page_size = min(int(request.GET.get('page_size', 20)), 100)
		
		qs = public_properties_queryset().prefetch_related(
			'images', 'amenities', 'room_types', 'offers'
		)
		
		filter_data = apply_hotel_filters(qs, request.GET)
		queryset = filter_data['queryset']
		
		# Apply ranking algorithm
		ranking_service = SearchRankingService(queryset, dict(request.GET))
		queryset = ranking_service.apply_ranking()
		
		paginator = Paginator(queryset, page_size)
		page_obj = paginator.get_page(page)
		
		results = []
		for property_obj in page_obj.object_list:
			card = _serialize_property_card(property_obj)
			# Add relevance score if available
			if hasattr(property_obj, 'relevance_score'):
				card['relevance_score'] = round(float(property_obj.relevance_score), 3)
			results.append(card)
		
		query_time = (timezone.now() - start_time).total_seconds() * 1000
		
		return JsonResponse({
			'results': results,
			'pagination': {
				'page': page_obj.number,
				'total_pages': paginator.num_pages,
				'total_results': paginator.count,
				'has_next': page_obj.has_next(),
				'has_previous': page_obj.has_previous(),
			},
			'meta': {
				'query_time_ms': round(query_time, 2),
				'search_query': filter_data.get('search_query', ''),
				'ranking_applied': True,
			}
		})
	except Exception as exc:
		logger.exception("API property_search_api error", exc_info=exc)
		return JsonResponse({'error': 'Internal server error'}, status=500)


@require_GET
def property_detail_api(request, property_id):
	"""
	GET /api/v1/properties/<id>/
	
	Returns detailed property information including room types
	"""
	try:
		from apps.hotels.selectors import get_property_detail
		
		property_obj = get_property_detail(property_id)
		if not property_obj:
			return JsonResponse({'error': 'Property not found'}, status=404)
		
		# Serialize full property detail
		data = {
			'id': property_obj.id,
			'name': property_obj.name,
			'slug': property_obj.slug,
			'property_type': property_obj.property_type,
			'description': property_obj.description,
			'location': {
				'city': property_obj.city.name if property_obj.city else None,
				'locality': property_obj.locality.name if property_obj.locality else None,
				'address': property_obj.address,
				'country': property_obj.country,
				'coordinates': {
					'latitude': float(property_obj.latitude),
					'longitude': float(property_obj.longitude),
				}
			},
			'rating': {
				'value': float(property_obj.rating),
				'count': property_obj.review_count,
			},
			'images': [
				{
					'url': img.image_url,
					'caption': img.caption,
					'is_featured': img.is_featured,
				}
				for img in property_obj.images.all()
			],
			'amenities': [
				{'name': amenity.name, 'icon': amenity.icon}
				for amenity in property_obj.amenities.all()
			],
			'room_types': [
				{
					'id': room.id,
					'name': room.name,
					'description': room.description,
					'base_price': float(room.base_price),
					'max_guests': room.max_guests,
					'bed_type': room.bed_type,
					'room_size_sqm': room.room_size_sqm,
				}
				for room in property_obj.room_types.all()
			],
			'policies': [
				{
					'title': policy.title,
					'description': policy.description,
					'policy_type': policy.policy_type,
				}
				for policy in property_obj.policies.all()
			],
			'offers': [
				{
					'title': offer.title,
					'description': offer.description,
					'discount_percentage': float(offer.discount_percentage) if offer.discount_percentage else None,
					'discount_amount': float(offer.discount_amount) if offer.discount_amount else None,
					'valid_from': offer.valid_from.isoformat(),
					'valid_until': offer.valid_until.isoformat(),
				}
				for offer in property_obj.offers.filter(is_active=True)
			],
			'booking_signals': {
				'bookings_today': property_obj.bookings_today,
				'bookings_this_week': property_obj.bookings_this_week,
				'is_trending': property_obj.is_trending,
			},
			'cancellation': {
				'has_free_cancellation': property_obj.has_free_cancellation,
				'cancellation_hours': property_obj.cancellation_hours,
			}
		}
		
		return JsonResponse(data)
	except Exception as exc:
		logger.exception(f"API property_detail_api error for property_id={property_id}", exc_info=exc)
		return JsonResponse({'error': 'Internal server error'}, status=500)


def _serialize_property_card(property_obj):
	"""
	Standardized JSON structure for property cards
	Used in list and search endpoints
	"""
	images = [img.image_url for img in property_obj.images.all()]
	featured_image = images[0] if images else None
	
	# Get minimum room price
	min_price = property_obj.min_room_price if hasattr(property_obj, 'min_room_price') else None
	
	# Calculate discount from active offers
	discount_percent = None
	active_offer = property_obj.offers.filter(
		is_active=True,
		valid_from__lte=timezone.now().date(),
		valid_until__gte=timezone.now().date()
	).first()
	
	if active_offer and min_price:
		if active_offer.discount_percentage:
			discount_percent = float(active_offer.discount_percentage)
		elif active_offer.discount_amount and min_price > 0:
			discount_percent = round((float(active_offer.discount_amount) / float(min_price)) * 100, 1)
	
	return {
		'id': property_obj.id,
		'name': property_obj.name,
		'slug': property_obj.slug,
		'location': {
			'city': property_obj.city.name if property_obj.city else None,
			'locality': property_obj.locality.name if property_obj.locality else None,
			'country': property_obj.country,
		},
		'rating': {
			'value': float(property_obj.rating),
			'count': property_obj.review_count,
		},
		'price': {
			'base': float(min_price) if min_price else None,
			'currency': 'INR',
			'per_night': True,
		},
		'discount': {
			'percentage': discount_percent,
		} if discount_percent else None,
		'images': {
			'featured': featured_image,
			'gallery': images,
		},
		'amenities_preview': [
			amenity.name for amenity in property_obj.amenities.all()[:5]
		],
		'badges': _generate_badges(property_obj),
		'cta': {
			'url': f'/hotels/{property_obj.id}/',
			'label': 'View Details',
		}
	}


def _generate_badges(property_obj):
	"""Generate dynamic trust signal badges using TrustSignalService"""
	from apps.hotels.services.trust_signals import TrustSignalService
	
	service = TrustSignalService(property_obj)
	return service.generate_badges()
