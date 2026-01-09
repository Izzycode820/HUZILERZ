"""
Rate limiting system for Fapshi API calls and payment processing
Based on token bucket algorithm with Redis backing
"""
import time
import threading
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class FapshiRateLimiter:
    """
    Rate limiter for Fapshi API calls and payment endpoints
    Implements token bucket algorithm with Redis backing
    """
    
    def __init__(self, max_requests=300, window_seconds=60):
        """
        Initialize rate limiter
        Default: 300 requests per minute (conservative for payment APIs)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.lock = threading.Lock()
    
    def can_make_request(self, identifier=None):
        """
        Check if request can be made
        Returns (can_proceed: bool, wait_time: int)
        """
        cache_key = f"fapshi_rate_limit:{identifier or 'global'}"
        
        with self.lock:
            current_time = int(time.time())
            window_start = current_time - self.window_seconds
            
            # Get current request count for this window
            requests_data = cache.get(cache_key, {})
            
            # Clean old entries
            cleaned_requests = {
                timestamp: count for timestamp, count in requests_data.items()
                if int(timestamp) > window_start
            }
            
            # Count total requests in current window
            total_requests = sum(cleaned_requests.values())
            
            if total_requests < self.max_requests:
                # Update request count
                minute_key = str(current_time // 60 * 60)  # Round to minute
                cleaned_requests[minute_key] = cleaned_requests.get(minute_key, 0) + 1
                
                # Save back to cache
                cache.set(cache_key, cleaned_requests, self.window_seconds + 10)
                return True, 0
            else:
                # Calculate wait time until window resets
                oldest_request = min(int(k) for k in cleaned_requests.keys())
                wait_time = oldest_request + self.window_seconds - current_time
                return False, max(wait_time, 1)
    
    def wait_if_needed(self, identifier=None, max_wait=30):
        """
        Wait if rate limited, up to max_wait seconds
        Returns True if can proceed, False if still rate limited
        """
        can_proceed, wait_time = self.can_make_request(identifier)
        
        if can_proceed:
            return True
        
        if wait_time <= max_wait:
            time.sleep(wait_time)
            can_proceed, _ = self.can_make_request(identifier)
            return can_proceed
        
        return False


class PaymentRateLimiter:
    """
    Specialized rate limiter for payment operations
    More restrictive limits for critical payment endpoints
    """
    
    def __init__(self):
        self.payment_limiter = FapshiRateLimiter(max_requests=60, window_seconds=60)  # 1 per second
        self.webhook_limiter = FapshiRateLimiter(max_requests=300, window_seconds=60)  # More lenient for webhooks
        self.status_limiter = FapshiRateLimiter(max_requests=120, window_seconds=60)  # 2 per second
    
    def can_initiate_payment(self, user_id):
        """Check if user can initiate payment"""
        return self.payment_limiter.can_make_request(f"payment:{user_id}")
    
    def can_check_status(self, user_id):
        """Check if user can check payment status"""
        return self.status_limiter.can_make_request(f"status:{user_id}")
    
    def can_process_webhook(self, source_ip=None):
        """Check if webhook can be processed"""
        return self.webhook_limiter.can_make_request(f"webhook:{source_ip or 'unknown'}")


# Global instances
fapshi_rate_limiter = FapshiRateLimiter()
payment_rate_limiter = PaymentRateLimiter()


def rate_limited_api(limiter_type='default', identifier_func=None):
    """
    Decorator for rate limiting API requests
    
    Args:
        limiter_type: 'payment', 'status', 'webhook', or 'default'
        identifier_func: Function to extract identifier from request
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifier (usually user_id or IP)
            identifier = None
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            elif args and hasattr(args[0], 'user'):
                identifier = getattr(args[0].user, 'id', None)
            
            # Choose appropriate limiter
            if limiter_type == 'payment':
                can_proceed, wait_time = payment_rate_limiter.can_initiate_payment(identifier)
            elif limiter_type == 'status':
                can_proceed, wait_time = payment_rate_limiter.can_check_status(identifier)
            elif limiter_type == 'webhook':
                can_proceed, wait_time = payment_rate_limiter.can_process_webhook(identifier)
            else:
                can_proceed, wait_time = fapshi_rate_limiter.can_make_request(identifier)
            
            if not can_proceed:
                from rest_framework.response import Response
                from rest_framework import status
                return Response({
                    'error': 'Rate limit exceeded',
                    'retry_after': wait_time,
                    'message': f'Too many requests. Please wait {wait_time} seconds.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limited_payment(func):
    """Decorator for payment initiation endpoints"""
    return rate_limited_api('payment')(func)


def rate_limited_status(func):
    """Decorator for payment status endpoints"""
    return rate_limited_api('status')(func)


def rate_limited_webhook(func):
    """Decorator for webhook endpoints"""
    def get_ip(request, *args, **kwargs):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    return rate_limited_api('webhook', get_ip)(func)

def rate_limited_batch(func):
    """Decorator for batch operation endpoints"""
    return rate_limited_api('default')(func)


# Usage tracking for monitoring
class RateLimitMonitor:
    """Monitor rate limiting events for analytics"""
    
    @staticmethod
    def log_rate_limit_hit(endpoint, identifier, limit_type):
        """Log when rate limit is hit"""
        logger.warning(f"Rate limit hit - Endpoint: {endpoint}, ID: {identifier}, Type: {limit_type}")
        
        # Cache metrics for monitoring dashboard
        cache_key = f"rate_limit_metrics:{endpoint}:{limit_type}"
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, timeout=3600)  # 1 hour
    
    @staticmethod
    def get_rate_limit_metrics():
        """Get rate limiting metrics for monitoring"""
        metrics = {}
        
        # Get all rate limit metric keys
        # Note: This is a simplified version, in production use Redis SCAN
        for endpoint in ['payment', 'status', 'webhook']:
            for limit_type in ['payment', 'status', 'webhook', 'default']:
                key = f"rate_limit_metrics:{endpoint}:{limit_type}"
                count = cache.get(key, 0)
                if count > 0:
                    metrics[f"{endpoint}_{limit_type}"] = count
        
        return metrics