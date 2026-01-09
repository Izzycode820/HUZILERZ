"""
Bandwidth tracking middleware
Tracks response sizes and syncs to HostingEnvironment
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from decimal import Decimal

logger = logging.getLogger(__name__)


class BandwidthTrackingMiddleware(MiddlewareMixin):
    """
    Track bandwidth usage per request
    Aggregates in Redis/cache then syncs to database periodically
    """

    def process_response(self, request, response):
        """Track response bandwidth for authenticated users"""

        # Skip tracking for non-authenticated requests
        if not hasattr(request, 'user') or request.user is None or not request.user.is_authenticated:
            return response

        # Skip tracking for admin, static, media, health check paths
        skip_paths = ['/admin/', '/static/', '/media/', '/health/', '/metrics/']
        if any(request.path.startswith(path) for path in skip_paths):
            return response

        try:
            # Calculate response size in bytes
            response_size_bytes = 0

            # Get content length from response
            if hasattr(response, 'content'):
                response_size_bytes = len(response.content)
            elif 'Content-Length' in response:
                response_size_bytes = int(response['Content-Length'])

            # Only track significant bandwidth (> 1KB)
            if response_size_bytes < 1024:
                return response

            # Convert to GB
            response_size_gb = Decimal(str(response_size_bytes)) / Decimal('1073741824')

            # Get user's hosting environment (cached for performance)
            user_id = request.user.id
            cache_key = f'hosting_env:user:{user_id}'

            hosting_env_id = cache.get(cache_key)

            if not hosting_env_id:
                # Query database and cache for 5 minutes
                from workspace.hosting.models import HostingEnvironment
                try:
                    hosting_env = HostingEnvironment.objects.filter(user_id=user_id).first()
                    if hosting_env:
                        hosting_env_id = hosting_env.id
                        cache.set(cache_key, hosting_env_id, 300)
                except Exception as e:
                    logger.error(f"Failed to get HostingEnvironment for user {user_id}: {e}")
                    return response

            if not hosting_env_id:
                return response

            # Aggregate bandwidth in cache (flush every 5 minutes via celery beat)
            bandwidth_cache_key = f'bandwidth:hosting_env:{hosting_env_id}'
            current_bandwidth = cache.get(bandwidth_cache_key, Decimal('0'))
            cache.set(
                bandwidth_cache_key,
                current_bandwidth + response_size_gb,
                3600  # 1 hour TTL
            )

            # Also increment request count
            requests_cache_key = f'requests:hosting_env:{hosting_env_id}'
            current_count = cache.get(requests_cache_key, 0)
            cache.set(requests_cache_key, current_count + 1, 3600)

        except Exception as e:
            # Never fail request due to tracking errors
            logger.error(f"Bandwidth tracking error: {e}")

        return response
