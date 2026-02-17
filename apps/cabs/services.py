import logging
from django.core.paginator import Paginator
from django.core.cache import cache
from cabs.forms import CabFilterForm
from .selectors import active_cabs_queryset, apply_cab_filters

CAB_LIST_CACHE_TTL = 60

logger = logging.getLogger(__name__)


class CabListService:
	def __init__(self, params):
		self.params = params

	def execute(self):
		try:
			cache_key = self._cache_key()
			cached = cache.get(cache_key)
			if cached:
				return cached

			queryset = active_cabs_queryset()
			filter_data = apply_cab_filters(queryset, self.params)
			queryset = filter_data["queryset"]

			cards = []
			for cab in queryset:
				primary_image = cab.images.first()
				cards.append({
					"id": cab.id,
					"name": cab.name,
					"city": cab.get_city_display(),
					"seats": cab.get_seats_display(),
					"fuel_type": cab.get_fuel_type_display(),
					"price_per_km": str(cab.system_price_per_km),
					"image_url": primary_image.image_url if primary_image else "",
					"cta_url": f"/cabs/{cab.id}/",
				})

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
					"selected_seats": filter_data["selected_seats"],
					"selected_fuels": filter_data["selected_fuels"],
					"min_price": filter_data["min_price"] or "0",
					"max_price": filter_data["max_price"] or "500",
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
				},
				"form": CabFilterForm(),
			}
			cache.set(cache_key, response, CAB_LIST_CACHE_TTL)
			return response
		except Exception as exc:
			logger.exception("CAB_LIST_CRASH", exc_info=exc)
			return {
				"results": [],
				"filters": {
					"search_query": "",
					"selected_cities": [],
					"selected_seats": [],
					"selected_fuels": [],
					"min_price": "0",
					"max_price": "500",
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
					"error": "Unable to load cabs",
				},
				"form": CabFilterForm(),
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
		return f"cabs:list:{params_str}"
