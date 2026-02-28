"""Cache manager for search results and autocomplete payloads."""

from django.core.cache import cache


class CacheManager:
    """Cache helper for search engine payloads."""

    def __init__(self, prefix: str = "search"):
        self.prefix = prefix

    def _key(self, suffix: str) -> str:
        return f"{self.prefix}:{suffix}"

    def get(self, key):
        return cache.get(self._key(key))

    def set(self, key, value, ttl=None):
        cache.set(self._key(key), value, ttl)

    def delete(self, key):
        cache.delete(self._key(key))

    def clear(self):
        # No global clear to avoid nuking unrelated cache entries.
        return None

    def get_search_results(self, query, filters=None):
        key = self._search_key(query, filters)
        return self.get(key)

    def set_search_results(self, query, payload, filters=None, ttl=900):
        key = self._search_key(query, filters)
        self.set(key, payload, ttl)

    def get_autocomplete_results(self, query):
        return self.get(f"autocomplete:{query.lower()}")

    def set_autocomplete_results(self, query, payload, ttl=900):
        self.set(f"autocomplete:{query.lower()}", payload, ttl)

    def get_filters(self):
        return self.get("filters")

    def set_filters(self, payload, ttl=1800):
        self.set("filters", payload, ttl)

    @staticmethod
    def _search_key(query, filters=None):
        if not filters:
            return f"search:{query.lower()}"
        normalized = []
        for key, value in sorted(filters.items()):
            if isinstance(value, list):
                normalized.append((key, tuple(value)))
            else:
                normalized.append((key, value))
        return f"search:{query.lower()}:{hash(tuple(normalized))}"




