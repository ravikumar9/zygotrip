import json
import logging
import time
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('zygotrip')
access_logger = logging.getLogger('access')


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware that uses Redis to track request counts.
    Prevents abuse by limiting requests per IP per endpoint.
    
    Configuration via settings.RATE_LIMIT_CONFIG:
    - enabled: Enable/disable rate limiting
    - window_size: Time window in seconds
    - requests_per_window: Dict of endpoint patterns and their limits
    - redis_key_prefix: Prefix for Redis keys
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.config = settings.RATE_LIMIT_CONFIG
        super().__init__(get_response)
    
    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_endpoint_limit(self, path):
        """Get rate limit for specific endpoint"""
        limits = self.config.get('requests_per_window', {})
        
        # Check for specific endpoint matches
        for endpoint_pattern, limit in limits.items():
            if endpoint_pattern in path:
                return limit
        
        # Return default limit
        return limits.get('default', 100)
    
    def process_request(self, request):
        """Check rate limit before processing request"""
        if not self.config.get('enabled', True):
            return None
        
        # Skip rate limiting for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
        
        try:
            client_ip = self.get_client_ip(request)
            endpoint_pattern = request.path.split('?')[0]  # Remove query params
            limit = self.get_endpoint_limit(endpoint_pattern)
            
            # Build cache key
            cache_key = f"{self.config.get('redis_key_prefix', 'ratelimit:')}"\
                       f"{client_ip}:{endpoint_pattern}"
            
            # Get current request count
            current_count = cache.get(cache_key, 0)
            
            if current_count >= limit:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {endpoint_pattern}",
                    extra={
                        'client_ip': client_ip,
                        'endpoint': endpoint_pattern,
                        'limit': limit,
                        'current_count': current_count,
                    }
                )
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {limit} requests per minute allowed',
                        'retry_after': self.config.get('window_size', 60),
                    },
                    status=429,
                )
            
            # Increment counter and set expiry
            window_size = self.config.get('window_size', 60)
            cache.set(cache_key, current_count + 1, window_size)
        
        except BaseException as e:
            # Gracefully degrade: if Redis fails, log warning but let request through
            logger.warning(f"Rate limit middleware error (falling back to no limits): {e}")
        
        return None


class StructuredLoggingMiddleware(MiddlewareMixin):
    """
    Structured logging middleware that logs all requests in JSON format.
    Captures request/response details for monitoring and debugging.
    """
    
    def process_request(self, request):
        """Capture request start time and client info"""
        request._start_time = time.time()
        request._client_ip = self.get_client_ip(request)
        return None
    
    def process_response(self, request, response):
        """Log request/response with structured data"""
        # Calculate request duration
        start_time = getattr(request, '_start_time', time.time())
        duration = (time.time() - start_time) * 1000  # Convert to ms
        
        # Build log data
        log_data = {
            'timestamp': time.time(),
            'method': request.method,
            'path': request.path,
            'ip': getattr(request, '_client_ip', self.get_client_ip(request)),
            'status_code': response.status_code,
            'duration_ms': round(duration, 2),
            'user_id': request.user.id if request.user.is_authenticated else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'referer': request.META.get('HTTP_REFERER', ''),
        }
        
        # Log at different levels based on status
        if response.status_code >= 500:
            access_logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            access_logger.warning(json.dumps(log_data))
        else:
            access_logger.info(json.dumps(log_data))
        
        # Add custom headers for debugging
        if settings.DEBUG:
            response['X-Request-ID'] = f"{request._client_ip}-{int(start_time*1000)}"
            response['X-Process-Time'] = str(round(duration, 2))
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
