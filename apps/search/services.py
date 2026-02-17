from django.core.cache import cache
from .selectors import searchable_properties, filter_search

SEARCH_CACHE_TTL = 30


class SearchService:
	@staticmethod
	def search(query):
		query = (query or "").strip()
		cache_key = f"search:{query.lower()}"
		cached = cache.get(cache_key)
		if cached is not None:
			return cached

		queryset = filter_search(searchable_properties(), query)
		results = []
		seen = set()
		for prop in queryset[:50]:
			if prop.id in seen:
				continue
			seen.add(prop.id)
			score = 0
			query_lower = query.lower()
			if query_lower in (prop.name or "").lower():
				score += 5
			if query_lower in (prop.city or "").lower():
				score += 3
			if query_lower in (prop.area or "").lower():
				score += 2
			if query_lower in (prop.landmark or "").lower():
				score += 2
			if query_lower in (prop.slug or "").lower():
				score += 1
			results.append({
				"id": prop.id,
				"name": prop.name,
				"slug": prop.slug,
				"city": prop.city,
				"area": prop.area,
				"landmark": prop.landmark,
				"rating": float(prop.rating),
				"cta_url": f"/hotels/{prop.id}/",
				"score": score,
			})

		results.sort(key=lambda item: (-item["score"], -item["rating"]))

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
		return response
