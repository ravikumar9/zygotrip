import hashlib
import json
import logging
import math
import time
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
from apps.hotels.models import Category
from ..selectors import public_properties_queryset, apply_hotel_filters, get_property_detail


HOTEL_LIST_CACHE_TTL = 60
CATEGORY_CACHE_TTL = 3600

logger = logging.getLogger(__name__)


def _hash_params(params):
	payload = {}
	for key in sorted(params.keys()):
		values = params.getlist(key)
		if not values:
			value = params.get(key)
			values = [value] if value is not None else []
		payload[key] = sorted([str(value) for value in values])
	encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
	return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class CategoriesService:
	@staticmethod
	def list_categories():
		start = time.monotonic()
		logger.info("CATEGORIES_LIST_START")
		try:
			cache_key = "categories:homepage"
			cached = cache.get(cache_key)
			if cached:
				logger.info("CATEGORIES_LIST_END duration_ms=%s", int((time.monotonic() - start) * 1000))
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
			cache.set(cache_key, result, CATEGORY_CACHE_TTL)
			logger.info("CATEGORIES_LIST_END duration_ms=%s", int((time.monotonic() - start) * 1000))
			return result
		except Exception:
			logger.exception("CATEGORIES_LIST_FAILURE")
			raise


class HotelHighlightService:
	@staticmethod
	def featured_properties(limit=6):
		start = time.monotonic()
		logger.info("HOTEL_HIGHLIGHT_START")
		try:
			queryset = public_properties_queryset()
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
			logger.info("HOTEL_HIGHLIGHT_END duration_ms=%s", int((time.monotonic() - start) * 1000))
			return results
		except Exception:
			logger.exception("HOTEL_HIGHLIGHT_FAILURE")
			raise


class HotelListService:
	def __init__(self, params, user=None):
		self.params = params
		self.user = user

	def execute(self):
		start = time.monotonic()
		logger.info("HOTEL_LIST_START")
		try:
			cache_key = f"hotels:list:{_hash_params(self.params)}"
			cached = cache.get(cache_key)
			if cached:
				logger.info("HOTEL_LIST_END duration_ms=%s", int((time.monotonic() - start) * 1000))
				return cached

			base_qs = public_properties_queryset()
			filter_data = apply_hotel_filters(base_qs, self.params)
			queryset = filter_data["queryset"]

			cards = []
			now = timezone.now().date()
			for property_obj in queryset:
				cards.append(self._build_card(property_obj, now))

			paginator = Paginator(cards, 20)
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
			cache.set(cache_key, response, HOTEL_LIST_CACHE_TTL)
			logger.info("HOTEL_LIST_END duration_ms=%s", int((time.monotonic() - start) * 1000))
			return response
		except Exception:
			logger.exception("HOTEL_LIST_FAILURE")
			raise

	def _build_card(self, property_obj, today):
		images = [image.image_url for image in property_obj.images.all()]
		featured_image = images[0] if images else ""
		
		# SIMPLIFIED FORMAT: STRING ARRAY FOR AMENITIES (template requirement)
		amenities_list = [amenity.name for amenity in property_obj.amenities.all()[:6]]

		# Pricing logic
		base_price = property_obj.base_price
		discount_price = property_obj.discount_price or property_obj.dynamic_price
		discount_percent = None
		
		if base_price and discount_price and discount_price < base_price:
			discount_percent = round(((base_price - discount_price) / base_price) * 100, 1)

		return {
			"id": property_obj.id,
			"name": property_obj.name,
			"location": f"{property_obj.city}, {property_obj.country}" if property_obj.city else "Unknown",
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
		start = time.monotonic()
		logger.info("HOTEL_DETAIL_START")
		try:
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
					booking = create_booking(
						user=booking_user,
						property_obj=property_obj,
						room_type=form.cleaned_data["room_type"],
						quantity=form.cleaned_data["quantity"],
						meal_plan=form.cleaned_data["meal_plan"],
						check_in=form.cleaned_data["check_in"],
						check_out=form.cleaned_data["check_out"],
						guests=[{
							"full_name": form.cleaned_data["guest_full_name"],
							"age": form.cleaned_data["guest_age"],
							"email": form.cleaned_data["guest_email"],
						}],
						promo_code=form.cleaned_data.get("promo_code") or "",
					)
					messages.success(self.request, "Booking created successfully.")
					return {
						"redirect_to": "booking:review",
						"redirect_kwargs": {"uuid": booking.uuid},
					}

			response = self._build_response(property_obj, form)
			logger.info("HOTEL_DETAIL_END duration_ms=%s", int((time.monotonic() - start) * 1000))
			return response
		except Exception:
			logger.exception("HOTEL_DETAIL_FAILURE")
			raise

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
