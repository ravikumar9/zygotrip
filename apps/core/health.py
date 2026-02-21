"""
Health Check Views
PHASE 5: Failure prevention
PHASE 6: Enhanced diagnostics
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'zygotrip'
    })


def health_check_detailed(request):
    """
    PHASE 6: Enhanced health check with comprehensive diagnostics
    Returns database, cache, and celery status
    """
    status = 'healthy'
    checks = {}
    start_time = time.time()
    
    # Check database
    db_start = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            db_latency = round((time.time() - db_start) * 1000, 2)
            checks['database'] = {
                'status': 'healthy',
                'latency_ms': db_latency
            }
    except Exception as e:
        checks['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        status = 'unhealthy'
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check Redis cache
    cache_start = time.time()
    try:
        cache_key = f'health_check_{int(time.time())}'
        cache.set(cache_key, 'test', 10)
        result = cache.get(cache_key)
        cache.delete(cache_key)
        cache_latency = round((time.time() - cache_start) * 1000, 2)
        
        if result == 'test':
            checks['cache'] = {
                'status': 'healthy',
                'latency_ms': cache_latency
            }
        else:
            checks['cache'] = {
                'status': 'degraded',
                'error': 'Cache read/write mismatch'
            }
            if status == 'healthy':
                status = 'degraded'
    except Exception as e:
        checks['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        # Cache failure is not critical
        if status == 'healthy':
            status = 'degraded'
        logger.warning(f"Cache health check failed: {str(e)}")
    
    # Check Celery
    celery_start = time.time()
    try:
        from celery import current_app
        
        # Check if Celery is configured
        if hasattr(settings, 'CELERY_BROKER_URL'):
            # Try to get worker stats (non-blocking)
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            celery_latency = round((time.time() - celery_start) * 1000, 2)
            
            if stats:
                worker_count = len(stats)
                checks['celery'] = {
                    'status': 'healthy',
                    'workers': worker_count,
                    'latency_ms': celery_latency
                }
            else:
                checks['celery'] = {
                    'status': 'degraded',
                    'workers': 0,
                    'error': 'No workers available'
                }
                if status == 'healthy':
                    status = 'degraded'
        else:
            checks['celery'] = {
                'status': 'not_configured',
                'message': 'Celery not configured'
            }
    except Exception as e:
        checks['celery'] = {
            'status': 'unknown',
            'error': str(e)
        }
        # Celery failure is not critical
        logger.info(f"Celery health check note: {str(e)}")
    
    # Total check time
    total_latency = round((time.time() - start_time) * 1000, 2)
    
    http_status = 200 if status == 'healthy' else 503
    
    return JsonResponse({
        'status': status,
        'service': 'zygotrip',
        'checks': checks,
        'total_latency_ms': total_latency,
        'timestamp': int(time.time())
    }, status=http_status)