# Search ranking algorithm service
# Composite scoring: rating + price + distance + popularity + availability

from typing import Dict, List, Optional
from decimal import Decimal
from django.db.models import QuerySet, F, Case, When, FloatField, Value
from django.utils import timezone
from apps.hotels.constants import (
	RANKING_WEIGHT_RATING,
	RANKING_WEIGHT_PRICE,
	RANKING_WEIGHT_DISTANCE,
	RANKING_WEIGHT_POPULARITY,
	RANKING_WEIGHT_AVAILABILITY,
	MIN_RATING_TOP_RATED,
	MIN_BOOKINGS_TRENDING,
	MIN_BOOKINGS_POPULAR,
	MIN_BOOKINGS_WEEK_POPULAR,
	PRICE_THRESHOLD_BUDGET,
	PRICE_THRESHOLD_MODERATE,
	PRICE_THRESHOLD_PREMIUM,
	PRICE_THRESHOLD_LUXURY,
	PRICE_THRESHOLD_ULTRA,
)


class SearchRankingService:
	"""
	Production-grade search ranking algorithm
	Combines multiple signals into composite relevance score
	
	Scoring weights (total = 1.0):
	- Rating quality: 30%
	- Price competitiveness: 20% 
	- Distance proximity: 25%
	- Popularity signals: 15%
	- Availability: 10%
	"""
	
	def __init__(self, queryset: QuerySet, params: Dict):
		self.queryset = queryset
		self.params = params
		self.user_lat = self._parse_float(params.get('lat'))
		self.user_lng = self._parse_float(params.get('lng'))
	
	def apply_ranking(self) -> QuerySet:
		"""Apply composite ranking score and sort by relevance"""
		# Normalize scores to 0-1 range
		qs = self.queryset.annotate(
			rating_score=self._rating_score(),
			price_score=self._price_score(),
			distance_score=self._distance_score(),
			popularity_score_normalized=self._popularity_score(),
			availability_score=self._availability_score(),
		)
		
		# Composite relevance score
		qs = qs.annotate(
			relevance_score=(
				F('rating_score') * RANKING_WEIGHT_RATING +
				F('price_score') * RANKING_WEIGHT_PRICE +
				F('distance_score') * RANKING_WEIGHT_DISTANCE +
				F('popularity_score_normalized') * RANKING_WEIGHT_POPULARITY +
				F('availability_score') * RANKING_WEIGHT_AVAILABILITY
			)
		)
		
		return qs.order_by('-relevance_score', '-rating', 'min_room_price')
	
	def _rating_score(self):
		"""Rating quality (0-5) normalized to 0-1"""
		return Case(
			When(rating__gte=4.5, then=Value(1.0)),
			When(rating__gte=4.0, then=Value(0.85)),
			When(rating__gte=3.5, then=Value(0.70)),
			When(rating__gte=3.0, then=Value(0.55)),
			When(rating__gte=2.5, then=Value(0.40)),
			When(rating__gte=2.0, then=Value(0.25)),
			default=Value(0.10),
			output_field=FloatField()
		)
	
	def _price_score(self):
		"""Price competitiveness - inverse scoring (lower price = higher score)"""
		# TODO: Implement percentile-based scoring across result set
		# For now, use simple inverse: cheaper properties score higher
		return Case(
			When(min_room_price__lte=PRICE_THRESHOLD_BUDGET, then=Value(1.0)),
			When(min_room_price__lte=PRICE_THRESHOLD_MODERATE, then=Value(0.80)),
			When(min_room_price__lte=PRICE_THRESHOLD_PREMIUM, then=Value(0.60)),
			When(min_room_price__lte=PRICE_THRESHOLD_LUXURY, then=Value(0.40)),
			When(min_room_price__lte=PRICE_THRESHOLD_ULTRA, then=Value(0.20)),
			default=Value(0.05),
			output_field=FloatField()
		)
	
	def _distance_score(self):
		"""Distance proximity - requires lat/lng in params"""
		if not self.user_lat or not self.user_lng:
			return Value(0.5, output_field=FloatField())  # Neutral score if no location
		
		# TODO: Implement Haversine distance calculation in database
		# For now, return neutral score
		return Value(0.5, output_field=FloatField())
	
	def _popularity_score(self):
		"""Popularity from booking signals"""
		return Case(
			When(is_trending=True, then=Value(1.0)),
			When(bookings_today__gte=MIN_BOOKINGS_TRENDING, then=Value(0.90)),
			When(bookings_today__gte=MIN_BOOKINGS_POPULAR, then=Value(0.75)),
			When(bookings_today__gte=1, then=Value(0.60)),
			When(bookings_this_week__gte=MIN_BOOKINGS_WEEK_POPULAR, then=Value(0.50)),
			When(popularity_score__gte=80, then=Value(0.40)),
			default=Value(0.20),
			output_field=FloatField()
		)
	
	def _availability_score(self):
		"""Availability signal - properties with rooms available score higher"""
		# TODO: Check RoomInventory for date range availability
		# For now, assume all properties available (neutral score)
		return Value(0.7, output_field=FloatField())
	
	@staticmethod
	def _parse_float(value: Optional[str]) -> Optional[float]:
		"""Safely parse float from query param"""
		if not value:
			return None
		try:
			return float(value)
		except (ValueError, TypeError):
			return None


# Import from sibling search.py module
import os
import sys
import importlib.util

# Get path to search.py (sibling of this __init__.py)
parent_dir = os.path.dirname(os.path.dirname(__file__))
search_py_path = os.path.join(parent_dir, 'search.py')

if os.path.exists(search_py_path):
	spec = importlib.util.spec_from_file_location("hotels_search_module", search_py_path)
	search_module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(search_module)
	ProductionSearchEngine = search_module.ProductionSearchEngine
	FilterAggregator = search_module.FilterAggregator
