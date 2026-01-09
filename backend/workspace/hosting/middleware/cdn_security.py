"""
CDN Security Middleware (Critical fixes #3 and #4)

Provides:
1. Signed CDN-to-API request verification (prevents public scraping)
2. Cache-Control headers for puck data API (reduces origin pressure)
3. Rate limiting for tenant-facing public APIs

Security Model:
- CloudFront adds X-Hz-Internal header with HMAC signature
- Backend verifies signature before serving puck data
- Invalid/missing signatures are rate-limited and rejected
"""

import hashlib
import hmac
import logging
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CDNSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to secure CDN-to-API requests and add cache headers
    """

    # Paths that require CDN signature verification
    PROTECTED_PATHS = [
        '/graphql',  # Public puck data queries come through GraphQL
    ]

    # GraphQL operations that require signature
    PROTECTED_OPERATIONS = [
        'publicPuckData',
        'public_puck_data',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """
        Verify CDN signature for protected endpoints
        """
        # Check if this is a protected path
        if not any(request.path.startswith(path) for path in self.PROTECTED_PATHS):
            return None

        # Check if this is a GraphQL request for public puck data
        if request.path.startswith('/graphql'):
            # For GraphQL, we need to check the operation name
            # This will be checked in process_view after the request body is parsed
            return None

        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check GraphQL operation names for protected operations
        """
        if request.path.startswith('/graphql'):
            # Try to extract GraphQL operation from request
            operation_name = self._get_graphql_operation(request)

            if operation_name and operation_name in self.PROTECTED_OPERATIONS:
                # This is a protected operation, verify CDN signature
                if not self._verify_cdn_signature(request):
                    logger.warning(
                        f"Unauthorized puck data request from IP: {self._get_client_ip(request)}"
                    )
                    return JsonResponse(
                        {
                            'errors': [{
                                'message': 'Unauthorized: Invalid or missing CDN signature',
                                'extensions': {'code': 'UNAUTHORIZED'}
                            }]
                        },
                        status=403
                    )

        return None

    def process_response(self, request, response):
        """
        Add Cache-Control headers for puck data responses (Critical fix #4)
        """
        if request.path.startswith('/graphql'):
            operation_name = self._get_graphql_operation(request)

            if operation_name and operation_name in self.PROTECTED_OPERATIONS:
                # Add cache headers for puck data
                # Cache-Control: public, max-age=0, s-maxage=60, stale-while-revalidate=120
                response['Cache-Control'] = 'public, max-age=0, s-maxage=60, stale-while-revalidate=120'
                response['Vary'] = 'X-Store-Hostname'

                # Add ETag for conditional requests
                if response.status_code == 200 and hasattr(response, 'content'):
                    etag = hashlib.md5(response.content).hexdigest()
                    response['ETag'] = f'"{etag}"'

                logger.debug(f"Added cache headers to puck data response for {request.path}")

        return response

    def _verify_cdn_signature(self, request):
        """
        Verify X-Hz-Internal signature from CloudFront (Critical fix #3)

        CloudFront should add: X-Hz-Internal: timestamp:signature
        where signature = HMAC-SHA256(timestamp + request_path, secret_key)
        """
        cdn_signature_header = request.META.get('HTTP_X_HZ_INTERNAL', '')

        if not cdn_signature_header:
            # In development, allow requests without signature
            if settings.DEBUG:
                logger.debug("CDN signature verification skipped in DEBUG mode")
                return True

            # In production, reject if no signature
            logger.warning("Missing X-Hz-Internal header in production")
            return False

        try:
            # Parse signature header: "timestamp:signature"
            parts = cdn_signature_header.split(':', 1)
            if len(parts) != 2:
                logger.warning(f"Invalid CDN signature format: {cdn_signature_header}")
                return False

            timestamp, provided_signature = parts

            # Verify timestamp is recent (within 5 minutes)
            import time
            current_time = int(time.time())
            request_time = int(timestamp)

            if abs(current_time - request_time) > 300:  # 5 minutes
                logger.warning(f"CDN signature timestamp expired: {timestamp}")
                return False

            # Generate expected signature
            secret_key = getattr(settings, 'CDN_INTERNAL_SECRET', 'default-dev-secret-change-in-production')
            message = f"{timestamp}:{request.path}"
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Compare signatures (timing-safe comparison)
            if not hmac.compare_digest(expected_signature, provided_signature):
                logger.warning(f"CDN signature mismatch for path: {request.path}")
                return False

            logger.debug(f"CDN signature verified successfully for {request.path}")
            return True

        except Exception as e:
            logger.error(f"Error verifying CDN signature: {str(e)}", exc_info=True)
            return False

    def _get_graphql_operation(self, request):
        """Extract GraphQL operation name from request"""
        try:
            if request.method == 'POST' and request.content_type == 'application/json':
                import json
                body = json.loads(request.body.decode('utf-8'))
                return body.get('operationName')
        except Exception:
            pass

        # Try GET request
        return request.GET.get('operationName')

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class PuckDataRateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting specifically for puck data API (Critical fix #9)
    Prevents abuse of tenant-facing public API
    """

    def process_request(self, request):
        """Apply rate limiting to puck data requests"""
        if request.path.startswith('/graphql'):
            operation_name = self._get_graphql_operation(request)

            if operation_name and operation_name in ['publicPuckData', 'public_puck_data']:
                # Rate limit by IP address
                client_ip = self._get_client_ip(request)
                cache_key = f"ratelimit:puck_data:{client_ip}"

                # Allow 60 requests per minute per IP
                request_count = cache.get(cache_key, 0)

                if request_count >= 60:
                    logger.warning(f"Rate limit exceeded for puck data from IP: {client_ip}")
                    return JsonResponse(
                        {
                            'errors': [{
                                'message': 'Rate limit exceeded. Please try again later.',
                                'extensions': {'code': 'RATE_LIMIT_EXCEEDED'}
                            }]
                        },
                        status=429
                    )

                # Increment counter
                cache.set(cache_key, request_count + 1, 60)  # 60 second window

        return None

    def _get_graphql_operation(self, request):
        """Extract GraphQL operation name from request"""
        try:
            if request.method == 'POST' and request.content_type == 'application/json':
                import json
                body = json.loads(request.body.decode('utf-8'))
                return body.get('operationName')
        except Exception:
            pass
        return request.GET.get('operationName')

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
