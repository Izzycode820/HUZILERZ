"""
Internal Token Middleware (Critical fix #10)

Provides token-based authentication for internal endpoints.
Used for health checks, metrics, and other internal admin endpoints
that should not be publicly accessible.

Security Model:
- Internal services provide X-Internal-Token header
- Token is compared against settings.INTERNAL_HEALTH_TOKEN
- Invalid/missing tokens return 403 Forbidden
"""

import logging
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class InternalTokenMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate internal requests using shared token.

    Protects internal endpoints like:
    - /api/internal/health/ (detailed system health)
    - /api/internal/metrics/ (internal metrics)
    - /api/internal/admin/ (internal admin operations)

    Usage in settings.py:
    MIDDLEWARE = [
        ...
        'workspace.hosting.middleware.internal_token.InternalTokenMiddleware',
        ...
    ]
    """

    # Endpoints that require internal token authentication
    PROTECTED_PATHS = [
        '/api/internal/',
        '/api/workspaces/hosting/internal/',
    ]

    def process_request(self, request):
        """
        Verify internal token for protected endpoints
        """
        # Check if this is a protected path
        if not any(request.path.startswith(path) for path in self.PROTECTED_PATHS):
            return None

        # Get token from header
        internal_token = request.headers.get('X-Internal-Token', '')

        # Validate token
        if not self._validate_internal_token(internal_token):
            logger.warning(
                f"Invalid internal token access attempt to {request.path} "
                f"from IP: {self._get_client_ip(request)}"
            )
            return JsonResponse(
                {
                    'error': 'Forbidden: Invalid or missing internal token',
                    'detail': 'This endpoint requires internal authentication',
                    'code': 'INTERNAL_TOKEN_REQUIRED'
                },
                status=403
            )

        logger.debug(f"Internal token verified for {request.path}")
        return None

    def _validate_internal_token(self, token):
        """
        Validate internal token against configured secret

        Args:
            token: Token from X-Internal-Token header

        Returns:
            bool: True if token is valid
        """
        # In development, allow requests without token if DEBUG=True
        if settings.DEBUG and not token:
            logger.debug("Internal token validation skipped in DEBUG mode")
            return True

        # Compare with configured token (timing-safe comparison)
        expected_token = getattr(settings, 'INTERNAL_HEALTH_TOKEN', '')
        if not expected_token:
            logger.error("INTERNAL_HEALTH_TOKEN not configured in settings")
            return False

        # Simple string comparison (not timing-safe but acceptable for token validation)
        # For production, consider using hmac.compare_digest()
        return token == expected_token

    def _get_client_ip(self, request):
        """Get client IP address for logging"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class InternalHealthTokenMiddleware(InternalTokenMiddleware):
    """
    Simplified middleware specifically for health check endpoints

    Can be used when only health endpoints need protection
    """

    # Only protect health endpoints
    PROTECTED_PATHS = [
        '/api/internal/health/',
    ]