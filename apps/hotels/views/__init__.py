import logging
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from ..services import HotelListService, HotelDetailService

logger = logging.getLogger(__name__)


def _empty_hotel_list_context():
	page_obj = Paginator([], 20).get_page(1)
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
			"page_obj": page_obj,
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
		},
	}


def hotel_list(request):
	try:
		dto = HotelListService(request.GET, user=request.user).execute()
		# Service returns 'results', but template expects 'cards'
		if 'results' in dto:
			dto['cards'] = dto['results']
			del dto['results']
		# Set empty_state flag
		dto['empty_state'] = len(dto.get('cards', [])) == 0
		return render(request, "hotels/list.html", dto)
	except Exception:
		logger.exception("HOTEL_LIST_VIEW_FAILURE")
		fallback = _empty_hotel_list_context()
		fallback["meta"]["error_message"] = "We hit a snag loading hotels. Please try again."
		return render(request, "hotels/list.html", fallback, status=500)


def hotel_detail(request, pk):
	try:
		response = HotelDetailService(request, pk).execute()
		if isinstance(response, dict) and response.get("redirect_to"):
			return redirect(response["redirect_to"], **response.get("redirect_kwargs", {}))
		return render(request, response["template"], response["context"], status=response["status"])
	except Exception:
		logger.exception("HOTEL_DETAIL_VIEW_FAILURE")
		return render(
			request,
			"hotels/not_found.html",
			{"error_message": "We could not load this property right now."},
			status=500,
		)
