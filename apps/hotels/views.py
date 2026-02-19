import logging
from django.shortcuts import render
from .services import HotelListService, HotelDetailService
from .serializers import RenderReadySerializer

logger = logging.getLogger(__name__)


def hotel_list(request):
	"""
	LAYOUT FOUNDATION: Hotel list view with render-ready data contract.
	
	Data format contract enforced:
	- Cards use string arrays for amenities (never dicts)
	- Prices are floats (never objects)
	- All data is pre-formatted before template
	"""
	dto = HotelListService(request.GET, user=request.user).execute()
	
	# Service already builds render-ready cards, just rename for template
	if 'results' in dto:
		dto['cards'] = dto['results']
		# Remove raw results from template context
		del dto['results']

	# Normalize card fields for template compatibility
	for card in dto.get('cards', []):
		if 'price' not in card:
			card['price'] = card.get('price_current') or card.get('price_original')
		if 'city' not in card:
			card['city'] = card.get('location')

	# Provide hotels alias for template loop
	dto['hotels'] = dto.get('cards', [])
	
	# Preserve filters from service and add filter options
	service_filters = dto.get('filters', {})
	dto['filters'] = service_filters
	dto['filter_options'] = RenderReadySerializer.serialize_filters()
	
	# Filter labels for sidebar
	dto['filter_labels'] = ['Price Range', 'Star Rating', 'Amenities']
	
	# Page title for head
	dto['page_title'] = 'Hotels - Zygotrip'
	
	# Empty state flag
	dto['empty_state'] = len(dto.get('cards', [])) == 0
	
	# Ensure pagination and meta are preserved from service
	# (already in dto from service)
	
	return render(request, "hotels/list.html", dto)


def hotel_detail(request, pk):
	response = HotelDetailService(request, pk).execute()
	return render(request, response["template"], response["context"], status=response["status"])
