import json
import logging
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("zygotrip")


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware that uses Redis to track request counts.
    Prevents abuse by limiting requests per IP per endpoint.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.config = settings.RATE_LIMIT_CONFIG
        super().__init__(get_response)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def get_endpoint_limit(self, path):
        limits = self.config.get("requests_per_window", {})
        for endpoint_pattern, limit in limits.items():
            if endpoint_pattern in path:
                return limit
        return limits.get("default", 100)

    def process_request(self, request):
        if not self.config.get("enabled", True):
            return None
        if request.path.startswith("/static/") or request.path.startswith("/admin/"):
            return None

        try:
            client_ip = self.get_client_ip(request)
            endpoint_pattern = request.path.split("?")[0]
            limit = self.get_endpoint_limit(endpoint_pattern)

            cache_key = (
                f"{self.config.get('redis_key_prefix', 'ratelimit:')}"
                f"{client_ip}:{endpoint_pattern}"
            )

            current_count = cache.get(cache_key, 0)
            if current_count >= limit:
                logger.warning(
                    "Rate limit exceeded for %s on %s",
                    client_ip,
                    endpoint_pattern,
                    extra={
                        "client_ip": client_ip,
                        "endpoint": endpoint_pattern,
                        "limit": limit,
                        "current_count": current_count,
                    },
                )
                return JsonResponse(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {limit} requests per minute allowed",
                        "retry_after": self.config.get("window_size", 60),
                    },
                    status=429,
                )

            window_size = self.config.get("window_size", 60)
            cache.set(cache_key, current_count + 1, window_size)

        except BaseException as exc:
            logger.warning(
                "Rate limit middleware error (falling back to no limits): %s",
                exc,
            )

        return None
