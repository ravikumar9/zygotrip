"""
REST API v1 - Property Search & Detail
Built with Django REST Framework for mobile-readiness, standardised responses,
and proper pagination/filtering.

Endpoints:
  GET  /api/v1/properties/          - Filtered hotel listing
  GET  /api/v1/properties/<id>/     - Property detail with rooms, images, amenities
  GET  /api/v1/search/              - Full-text + ranked search

All responses follow the envelope:
  { "success": true,  "data": { ... } }
  { "success": false, "error": { "code": "...", "message": "..." } }
"""
import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from apps.hotels.ota_selectors import (
    ota_visible_properties,
    apply_search_filters,
    apply_date_inventory_filter,
    apply_sorting,
)
from apps.hotels.selectors import get_property_detail
from .serializers import PropertyCardSerializer, PropertyDetailSerializer

logger = logging.getLogger('zygotrip.api.hotels')


class HotelPagination(PageNumberPagination):
    """Standardised pagination for hotel listing endpoints."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'data': {
                'results': data,
                'pagination': {
                    'count': self.page.paginator.count,
                    'total_pages': self.page.paginator.num_pages,
                    'current_page': self.page.number,
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
            },
        })


def _base_queryset():
    """Single source of truth for the public hotel queryset."""
    return ota_visible_properties().prefetch_related('images', 'amenities', 'room_types')


@api_view(['GET'])
@permission_classes([AllowAny])
def property_list_api(request):
    """
    GET /api/v1/properties/

    Supported query parameters:
      location, city, min_price, max_price, free_cancellation,
      amenity (repeatable), property_type (repeatable),
      checkin (YYYY-MM-DD), checkout (YYYY-MM-DD),
      sort (popular|price_asc|price_desc|rating|newest),
      page, page_size
    """
    start = timezone.now()

    qs = _base_queryset()
    qs = apply_search_filters(qs, request.GET)
    qs = apply_date_inventory_filter(qs, request.GET)
    qs = apply_sorting(qs, request.GET.get('sort', 'popular'))

    paginator = HotelPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = PropertyCardSerializer(page, many=True, context={'request': request})

    query_ms = round((timezone.now() - start).total_seconds() * 1000, 2)
    logger.debug("property_list_api: %d results in %sms", len(page), query_ms)

    response = paginator.get_paginated_response(serializer.data)
    response.data['meta'] = {
        'query_time_ms': query_ms,
        'filters_applied': {
            'location': request.GET.get('location', ''),
            'sort': request.GET.get('sort', 'popular'),
        },
    }
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def property_search_api(request):
    """
    GET /api/v1/search/

    Text search with OTA-grade multi-field scoring.

    Additional params (same as list) plus:
      q  - free-text search query (name, city, area, landmark)
    """
    start = timezone.now()

    query = (request.GET.get('q') or request.GET.get('location') or '').strip()
    params = request.GET.copy()
    if query and 'location' not in params:
        params['location'] = query

    qs = _base_queryset()
    qs = apply_search_filters(qs, params)
    qs = apply_date_inventory_filter(qs, params)
    qs = apply_sorting(qs, params.get('sort', 'popular'))

    paginator = HotelPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = PropertyCardSerializer(page, many=True, context={'request': request})

    query_ms = round((timezone.now() - start).total_seconds() * 1000, 2)
    logger.debug("property_search_api: q=%s %d results in %sms", query, len(page), query_ms)

    response = paginator.get_paginated_response(serializer.data)
    response.data['meta'] = {'query': query, 'query_time_ms': query_ms}
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def property_detail_api(request, property_id):
    """
    GET /api/v1/properties/<id>/

    <id> can be either a numeric pk or a slug string.
    """
    property_obj = get_property_detail(property_id)
    if not property_obj:
        return Response(
            {
                'success': False,
                'error': {
                    'code': 'not_found',
                    'message': 'Property not found or not available.',
                    'detail': None,
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = PropertyDetailSerializer(property_obj, context={'request': request})
    return Response({'success': True, 'data': serializer.data})
