import logging
import math
import json
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import login
from django.utils import timezone
from accounts.models import Role, User, UserRole
from accounts.selectors import user_has_role
from booking.forms import BookingCreateForm
from booking.services import create_booking
from core.date_utils import get_date_for_template
from hotels.models import Category
from .selectors import public_properties_queryset, apply_hotel_filters, get_property_detail
from .search import SearchRankingService
from .constants import (
	CACHE_TTL_HOTEL_LIST,
	CACHE_TTL_CATEGORIES,
	DEFAULT_PAGE_SIZE,
	AMENITIES_CARD_COUNT,
)


logger = logging.getLogger(__name__)


class CategoriesService:
	@staticmethod
	def list_categories():
		cache_key = "categories:homepage"
		cached = cache.get(cache_key)
		if cached:
			return cached
		categories = list(Category.objects.all().order_by("name"))
		result = []
		for category in categories:
			result.append({
				"name": category.name,
				"slug": category.slug,
				"description": category.description,
				"icon": category.icon,
				"banner_url": f"/static/img/categories/{category.slug}.svg",
			})
		cache.set(cache_key, result, CACHE_TTL_CATEGORIES)
		return result


class HotelHighlightService:
	@staticmethod
	def featured_properties(limit=6):
		queryset = public_properties_queryset().prefetch_related("images")
		results = []
		for property_obj in queryset[:limit]:
			image = property_obj.images.first()
			results.append({
				"id": property_obj.id,
				"name": property_obj.name,
				"city": property_obj.city,
				"country": property_obj.country,
				"rating": float(property_obj.rating),
				"image_url": image.image_url if image else "",
				"cta_url": f"/hotels/{property_obj.id}/",
			})
		return results


class HotelListService:
	def __init__(self, params, user=None):
		self.params = params
		self.user = user

	def execute(self):
		try:
			cache_key = self._cache_key()
			cached = cache.get(cache_key)
			if cached:
				return cached

			base_qs = public_properties_queryset().prefetch_related(
				"images",
				"amenities",
				"policies",
				"offers",
			)
			filter_data = apply_hotel_filters(base_qs, self.params)
			queryset = filter_data["queryset"]
			
			# Apply intelligent ranking if not explicitly sorting
			if not filter_data.get("sort_by"):
				ranking_service = SearchRankingService(queryset, self.params)
				queryset = ranking_service.apply_ranking()

			cards = []
			now = timezone.now().date()
			for property_obj in queryset:
				cards.append(self._build_card(property_obj, now))

			paginator = Paginator(cards, DEFAULT_PAGE_SIZE)
			page = self.params.get("page") or 1
			try:
				page_num = int(page)
				if page_num < 1:
					page_num = 1
				page_obj = paginator.get_page(page_num)
			except (ValueError, TypeError):
				page_obj = paginator.get_page(1)

			response = {
				"results": list(page_obj.object_list),
				"filters": {
					"search_query": filter_data["search_query"],
					"selected_cities": filter_data["selected_cities"],
					"selected_ratings": filter_data["selected_ratings"],
					"selected_amenities": filter_data["selected_amenities"],
					"selected_category": filter_data.get("selected_category"),
					"min_price": filter_data["min_price"] or "",
					"max_price": filter_data["max_price"] or "",
					"city_options": ["delhi", "mumbai", "bangalore", "chennai", "goa", "jaipur"],
					"rating_options": ["4.5", "4.0", "3.5"],
					"amenity_options": ["wifi", "breakfast", "pool", "parking"],
				},
				"pagination": {
					"page_obj": page_obj,
					"page": page_obj.number,
					"num_pages": page_obj.paginator.num_pages,
					"has_previous": page_obj.has_previous(),
					"has_next": page_obj.has_next(),
					"previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
					"next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
				},
				"meta": {
					"total_results": paginator.count,
					"query": filter_data["search_query"],
				},
			}
			cache.set(cache_key, response, CACHE_TTL_HOTEL_LIST)
			return response
		except Exception as exc:
			logger.exception("HOTEL_LIST_CRASH", exc_info=exc)
			return {
				"results": [],
				"filters": {
					"search_query": "",
					"selected_cities": [],
					"selected_ratings": [],
					"selected_amenities": [],
					"selected_category": "",
					"min_price": "",
					"max_price": "",
					"city_options": ["delhi", "mumbai", "bangalore", "chennai", "goa", "jaipur"],
					"rating_options": ["4.5", "4.0", "3.5"],
					"amenity_options": ["wifi", "breakfast", "pool", "parking"],
				},
				"pagination": {
					"page_obj": Paginator([], 20).get_page(1),
					"page": 1,
					"num_pages": 1,
					"has_previous": False,
					"has_next": False,
					"previous_page_number": None,
					"next_page_number": None,
				},
				"meta": {
					"total_results": 0,
					"query": "",
					"error": "Unable to load hotels",
				},
			}

	def _cache_key(self):
		parts = []
		for key in sorted(self.params.keys()):
			values = self.params.getlist(key)
			if not values:
				values = [self.params.get(key)]
			for value in values:
				parts.append(f"{key}={value}")
		params_str = "&".join(parts)
		return f"hotels:list:{params_str}"

	def _build_card(self, property_obj, today):
		images = [image.image_url for image in property_obj.images.all()]
		featured_image = images[0] if images else ""
		
		# SIMPLIFIED FORMAT: STRING ARRAY FOR AMENITIES (template requirement)
		amenities_list = [amenity.name for amenity in property_obj.amenities.all()[:AMENITIES_CARD_COUNT]]

		# Pricing logic - use annotated min_room_price
		base_price = property_obj.min_room_price if hasattr(property_obj, 'min_room_price') else None
		discount_price = None  # Discounts moved to offers and room-level pricing
		discount_percent = None
		
		# Use PropertyOffer for discount calculations if active offers exist
		active_offer = property_obj.offers.filter(is_active=True, valid_from__lte=today, valid_until__gte=today).first()
		if active_offer and base_price:
			if active_offer.discount_percentage:
				discount_price = base_price * (1 - active_offer.discount_percentage / 100)
				discount_percent = float(active_offer.discount_percentage)
			elif active_offer.discount_amount:
				discount_price = base_price - active_offer.discount_amount
				discount_percent = round(((base_price - discount_price) / base_price) * 100, 1)

		return {
			"id": property_obj.id,
			"name": property_obj.name,
			"location": f"{property_obj.city}, {property_obj.country}",
			"image_url": featured_image,
			"rating_value": float(property_obj.rating) if property_obj.rating else 0,
			"rating_count": property_obj.review_count or 0,
			"amenities": amenities_list,  # STRING ARRAY (not dicts)
			"price_current": float(discount_price) if discount_price else float(base_price) if base_price else None,
			"price_original": float(base_price) if base_price else None,
			"discount_percent": discount_percent,
			"cta_url": f"/hotels/{property_obj.id}/",
			"cta_label": "View Details",
		}

	def _calculate_distance(self, property_obj):
		try:
			lat = float(self.params.get("lat"))
			lng = float(self.params.get("lng"))
			if property_obj.latitude is None or property_obj.longitude is None:
				return None
			return round(self._haversine(lat, lng, float(property_obj.latitude), float(property_obj.longitude)), 1)
		except (TypeError, ValueError):
			return None

	@staticmethod
	def _haversine(lat1, lon1, lat2, lon2):
		radius = 6371
		phi1 = math.radians(lat1)
		phi2 = math.radians(lat2)
		delta_phi = math.radians(lat2 - lat1)
		delta_lambda = math.radians(lon2 - lon1)
		a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
		return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class HotelDetailService:
	def __init__(self, request, pk):
		self.request = request
		self.pk = pk

	def execute(self):
		property_obj = get_property_detail(self.pk)
		if not property_obj:
			return {
				"template": "hotels/not_found.html",
				"context": {},
				"status": 200,
			}

		form = BookingCreateForm(self.request.POST or None, property_obj=property_obj)
		if self.request.method == "POST":
			if form.is_valid():
				booking_user = self.request.user
				if not self.request.user.is_authenticated:
					guest_email = form.cleaned_data["guest_email"]
					if not guest_email:
						form.add_error("guest_email", "Email is required for guest booking.")
						messages.error(self.request, "Please provide an email to continue as guest.")
						return self._build_response(property_obj, form)
					booking_user, created = User.objects.get_or_create(
						email=guest_email,
						defaults={"full_name": form.cleaned_data["guest_full_name"]},
					)
					if created:
						booking_user.set_unusable_password()
						booking_user.save(update_fields=["password", "updated_at"])
					role = Role.objects.get(code="customer")
					UserRole.objects.get_or_create(user=booking_user, role=role)
					login(self.request, booking_user, backend="django.contrib.auth.backends.ModelBackend")
				elif not user_has_role(self.request.user, "customer"):
					raise PermissionDenied
				create_booking(
					user=booking_user,
					property_obj=property_obj,
					room_type=form.cleaned_data["room_type"],
					quantity=form.cleaned_data["quantity"],
					meal_plan=form.cleaned_data["meal_plan"],
					check_in=form.cleaned_data["check_in"],
					check_out=form.cleaned_data["check_out"],
					guests=[{"full_name": form.cleaned_data["guest_full_name"]}],
				)
				messages.success(self.request, "Booking created successfully.")
				return self._build_response(property_obj, form)

		return self._build_response(property_obj, form)

	def _build_response(self, property_obj, form):
		room_prices = {room.id: str(room.base_price) for room in property_obj.room_types.all()}
		meal_prices = {meal.id: str(meal.price) for meal in property_obj.meal_plans.all()}
		return {
			"template": "hotels/detail.html",
			"context": {
				"property": property_obj,
				"form": form,
				"room_prices_json": json.dumps(room_prices),
				"meal_prices_json": json.dumps(meal_prices),
				"today": get_date_for_template(),
			},
			"status": 200,
		}
