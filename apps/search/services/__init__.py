import hashlib
import json
import logging
import math
import time
from django.core.cache import cache
from ..selectors import searchable_properties, filter_search

SEARCH_CACHE_TTL = 30

logger = logging.getLogger(__name__)


def _hash_params(params):
	encoded = json.dumps(params, sort_keys=True, separators=(",", ":"))
	return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _score_field(query, value):
	if not value:
		return 0
	value = value.lower()
	if value == query:
		return 100
	if value.startswith(query):
		return 50
	if query in value:
		return 20
	return 0


class SearchService:
	@staticmethod
	def search(query):
		start = time.monotonic()
		logger.info("SEARCH_START")
		try:
			query = (query or "").strip()
			cache_key = f"search:{_hash_params({'q': query.lower()})}"
			cached = cache.get(cache_key)
			if cached is not None:
				logger.info("SEARCH_END duration_ms=%s", int((time.monotonic() - start) * 1000))
				return cached

			queryset = filter_search(searchable_properties(), query)
			results = []
			seen = set()
			query_lower = query.lower()
			for prop in queryset[:50]:
				if prop.id in seen:
					continue
				seen.add(prop.id)
				score = 0
				for value in [prop.name, prop.city, prop.area, prop.landmark, prop.slug]:
					score += _score_field(query_lower, value)
				rating_boost = float(getattr(prop, "rating", 0) or 0)
				review_count = getattr(prop, "review_count", 0) or 0
				review_boost = math.log1p(review_count)
				score += rating_boost + review_boost
				results.append({
					"id": prop.id,
					"name": prop.name,
					"slug": prop.slug,
					"city": prop.city,
					"area": prop.area,
					"landmark": prop.landmark,
					"rating": float(getattr(prop, "rating", 0) or 0),
					"review_count": review_count,
					"cta_url": f"/hotels/{prop.id}/",
					"score": score,
				})

			results.sort(key=lambda item: (-item["score"], -item["rating"], -item["review_count"]))

			response = {
				"results": results,
				"filters": {
					"query": query,
				},
				"pagination": {
					"page": 1,
					"num_pages": 1,
				},
				"meta": {
					"total_results": len(results),
				},
			}
			cache.set(cache_key, response, SEARCH_CACHE_TTL)
			logger.info("SEARCH_END duration_ms=%s", int((time.monotonic() - start) * 1000))
			return response
		except Exception:
			logger.exception("SEARCH_FAILURE")
			raise
