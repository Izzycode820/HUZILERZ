"""
Subscription Middleware
Validates subscription claims in JWT tokens and enforces feature access
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(MiddlewareMixin):
    """
    Middleware to validate subscription claims and enforce feature access
    Runs after JWT authentication middleware
    """
    
    # Paths that require subscription validation
    SUBSCRIPTION_REQUIRED_PATHS = [
        '/api/workspace/',
        '/api/hosting/',
        '/api/analytics/',
        '/api/domains/',
    ]
    
    # Paths that are exempt from subscription checks
    EXEMPT_PATHS = [
        '/api/auth/',
        '/api/subscriptions/pricing/',
        '/api/health/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        """Process incoming request and validate subscription claims"""
        
        # Skip non-API requests and exempt paths
        if not self._should_validate_subscription(request):
            return None
        
        # Get JWT payload from request (set by authentication middleware)
        jwt_payload = getattr(request, 'jwt_payload', None)
        
        if not jwt_payload:
            # No JWT payload means authentication failed - let auth middleware handle
            return None
        
        # Validate subscription claims
        validation_result = self._validate_subscription_claims(jwt_payload)
        
        if not validation_result['valid']:
            return JsonResponse({
                'error': 'Invalid subscription claims',
                'detail': validation_result.get('error'),
                'code': 'SUBSCRIPTION_VALIDATION_FAILED'
            }, status=403)
        
        # Add subscription info to request
        request.subscription_tier = validation_result.get('tier', 'free')
        request.subscription_status = validation_result.get('status', 'none')
        request.features_bitmap = validation_result.get('features', 0)
        
        # Check feature access for specific endpoints
        feature_check_result = self._check_feature_access(request)
        
        if not feature_check_result['allowed']:
            return JsonResponse({
                'error': 'Feature not available in your subscription plan',
                'detail': feature_check_result.get('message'),
                'required_tier': feature_check_result.get('required_tier'),
                'current_tier': request.subscription_tier,
                'upgrade_url': '/api/subscriptions/pricing/',
                'code': 'FEATURE_ACCESS_DENIED'
            }, status=403)
        
        return None
    
    def _should_validate_subscription(self, request):
        """Determine if request should be validated for subscription"""
        path = request.path
        
        # Skip exempt paths
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return False
        
        # Check if path requires subscription validation
        for required_path in self.SUBSCRIPTION_REQUIRED_PATHS:
            if path.startswith(required_path):
                return True
        
        # Default to no validation for unlisted paths
        return False
    
    def _validate_subscription_claims(self, jwt_payload):
        """Validate subscription claims in JWT payload"""
        try:
            from subscription.services.subscription_claims_service import SubscriptionClaimsService
            return SubscriptionClaimsService.validate_token_subscription_claims(jwt_payload)
            
        except Exception as e:
            logger.error(f"Subscription claims validation error: {str(e)}")
            return {'valid': False, 'error': 'Validation failed'}
    
    def _check_feature_access(self, request):
        """Check if current subscription tier allows access to requested feature"""
        path = request.path
        features_bitmap = request.features_bitmap
        
        # Map paths to required features
        feature_requirements = {
            '/api/hosting/deploy': ('deployment', 'beginning'),
            '/api/workspace/create': ('multiple_workspaces', 'pro'),
            '/api/analytics/advanced': ('advanced_analytics', 'pro'),
            '/api/domains/custom': ('custom_domains', 'beginning'),
            '/api/workspace/bulk': ('bulk_operations', 'enterprise'),
            '/api/branding/white-label': ('white_label', 'enterprise'),
        }
        
        # Check specific feature requirements
        for path_pattern, (feature_name, min_tier) in feature_requirements.items():
            if path.startswith(path_pattern):
                return self._check_specific_feature(
                    features_bitmap, feature_name, min_tier, request.subscription_tier
                )
        
        # Default allow for paths without specific requirements
        return {'allowed': True}
    
    def _check_specific_feature(self, features_bitmap, feature_name, min_tier, current_tier):
        """Check access to a specific feature"""
        try:
            from authentication.services.jwt_subscription_service import JWTSubscriptionService
            
            # Check if feature is enabled in bitmap
            has_feature = JWTSubscriptionService.has_feature_access(features_bitmap, feature_name)
            
            if has_feature:
                return {'allowed': True}
            
            return {
                'allowed': False,
                'message': f'Feature "{feature_name}" requires {min_tier} plan or higher',
                'required_tier': min_tier,
                'feature': feature_name
            }
            
        except Exception as e:
            logger.error(f"Feature access check failed: {str(e)}")
            return {
                'allowed': False,
                'message': 'Feature access validation failed'
            }


class SubscriptionDebugMiddleware(MiddlewareMixin):
    """
    Debug middleware for development - logs subscription claims
    Only active when DEBUG=True
    """
    
    def process_request(self, request):
        """Log subscription claims for debugging"""
        
        if not settings.DEBUG:
            return None
        
        # Only log API requests
        if not request.path.startswith('/api/'):
            return None
        
        jwt_payload = getattr(request, 'jwt_payload', None)
        
        if jwt_payload:
            subscription_claims = jwt_payload.get('subscription', {})
            
            if subscription_claims:
                logger.debug(
                    f"Subscription Debug - Path: {request.path}, "
                    f"Tier: {subscription_claims.get('tier')}, "
                    f"Features: {subscription_claims.get('features_bitmap')}, "
                    f"Status: {subscription_claims.get('status')}"
                )
        
        return None


class UsageLimitMiddleware(MiddlewareMixin):
    """
    Middleware to enforce usage limits based on subscription claims
    Prevents API abuse and enforces plan limits
    """
    
    # Rate limits per tier (requests per hour)
    TIER_RATE_LIMITS = {
        'free': 100,
        'beginning': 500,
        'pro': 2000,
        'enterprise': 10000,
    }
    
    def process_request(self, request):
        """Enforce usage limits based on subscription tier"""
        
        # Skip non-API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Skip auth endpoints
        if request.path.startswith('/api/auth/'):
            return None
        
        jwt_payload = getattr(request, 'jwt_payload', None)
        
        if not jwt_payload:
            return None
        
        subscription_claims = jwt_payload.get('subscription', {})
        tier = subscription_claims.get('tier', 'free')
        
        # Check rate limit
        if self._is_rate_limited(request, tier):
            return JsonResponse({
                'error': 'API rate limit exceeded',
                'detail': f'Exceeded {self.TIER_RATE_LIMITS[tier]} requests per hour for {tier} tier',
                'tier': tier,
                'upgrade_url': '/api/subscriptions/pricing/',
                'code': 'RATE_LIMIT_EXCEEDED'
            }, status=429)
        
        return None
    
    def _is_rate_limited(self, request, tier):
        """Check if user has exceeded rate limit for their tier"""
        try:
            from django.core.cache import cache
            import time
            
            # Get user ID from JWT
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return False
            
            # Create cache key
            cache_key = f"rate_limit_{user_id}_{int(time.time() // 3600)}"  # Per hour
            
            # Get current count
            current_count = cache.get(cache_key, 0)
            
            # Get limit for tier
            limit = self.TIER_RATE_LIMITS.get(tier, self.TIER_RATE_LIMITS['free'])
            
            if current_count >= limit:
                return True
            
            # Increment counter
            cache.set(cache_key, current_count + 1, timeout=3600)  # 1 hour TTL
            
            return False
            
        except Exception as e:
            logger.error(f"Rate limiting check failed: {str(e)}")
            return False  # Allow request if check fails