import logging
from django.shortcuts import render
from ..services import SearchService

logger = logging.getLogger(__name__)


def search(request):
	query = request.GET.get("q") or ""
	try:
		results = SearchService.search(query)
		results['filter_labels'] = ['Category', 'Price Range', 'Location']
		return render(request, "search/list.html", results)
	except Exception:
		logger.exception("SEARCH_VIEW_FAILURE")
		return render(
			request,
			"search/list.html",
			{
				"results": [],
				"filter_labels": ['Category', 'Price Range', 'Location'],
				"filters": {"query": query},
				"pagination": {"page": 1, "num_pages": 1},
				"meta": {"total_results": 0, "error_message": "Search failed. Please try again."},
			},
			status=500,
		)
