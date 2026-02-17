import logging
from django.core.paginator import Paginator
from django.shortcuts import render
from ..services import CabListService
from ..forms import CabFilterForm

logger = logging.getLogger(__name__)


def _empty_cab_list_context():
	page_obj = Paginator([], 20).get_page(1)
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
		},
		"form": CabFilterForm(),
	}


def cab_list(request):
	try:
		dto = CabListService(request.GET).execute()
		return render(request, "cabs/list.html", dto)
	except Exception:
		logger.exception("CAB_LIST_VIEW_FAILURE")
		fallback = _empty_cab_list_context()
		fallback["meta"]["error_message"] = "We hit a snag loading cabs. Please try again."
		return render(request, "cabs/list.html", fallback, status=500)
