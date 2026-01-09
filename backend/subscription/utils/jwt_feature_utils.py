"""
JWT Feature Utilities
Helper functions for JWT-based feature gating in views and APIs
"""
import logging
from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)


def require_subscription_feature(feature_name, min_tier=None):
    """
    Decorator to require specific subscription features for views
    Uses JWT claims for O(1) feature checking
    
    Args:
        feature_name: Feature name to check (e.g., 'deployment', 'analytics')
        min_tier: Minimum tier required (optional)
    
    Usage:
        @require_subscription_feature('deployment', 'beginning')
        def deploy_website(request):
            # View logic here
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get JWT payload from request
            jwt_payload = getattr(request, 'jwt_payload', None)
            
            if not jwt_payload:
                return JsonResponse({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }, status=401)
            
            # Check feature access using JWT claims
            access_result = check_jwt_feature_access(jwt_payload, feature_name, min_tier)
            
            if not access_result['allowed']:
                return JsonResponse({
                    'error': 'Feature not available',
                    'detail': access_result['message'],
                    'feature': feature_name,
                    'current_tier': access_result['current_tier'],
                    'required_tier': access_result['required_tier'],
                    'upgrade_url': '/api/subscriptions/pricing/',
                    'code': 'FEATURE_ACCESS_DENIED'
                }, status=403)
            
            # Add feature info to request for view usage
            request.feature_access = access_result
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def check_jwt_feature_access(jwt_payload, feature_name, min_tier=None):
    """
    Check feature access using JWT subscription claims
    
    Args:
        jwt_payload: JWT payload dict
        feature_name: Feature to check
        min_tier: Minimum tier required
        
    Returns:
        dict: Access result with allowed status
    """
    try:
        from authentication.services.jwt_subscription_service import JWTSubscriptionService
        
        subscription_claims = jwt_payload.get('subscription', {})
        
        if not subscription_claims:
            return {
                'allowed': False,
                'message': 'No subscription information found',
                'current_tier': 'free',
                'required_tier': min_tier or 'beginning'
            }
        
        current_tier = subscription_claims.get('tier', 'free')
        features_bitmap = subscription_claims.get('features_bitmap', 0)
        status = subscription_claims.get('status', 'none')
        
        # Check if subscription is active
        if status not in ['active', 'grace_period']:
            return {
                'allowed': False,
                'message': f'Subscription is {status}',
                'current_tier': current_tier,
                'required_tier': 'active_subscription'
            }
        
        # Check minimum tier requirement
        if min_tier:
            tier_hierarchy = ['free', 'beginning', 'pro', 'enterprise']
            
            try:
                current_index = tier_hierarchy.index(current_tier)
                required_index = tier_hierarchy.index(min_tier)
                
                if current_index < required_index:
                    return {
                        'allowed': False,
                        'message': f'{feature_name} requires {min_tier} plan or higher',
                        'current_tier': current_tier,
                        'required_tier': min_tier
                    }
            except ValueError:
                logger.warning(f"Invalid tier in JWT claims: {current_tier} or {min_tier}")
        
        # Check feature bitmap
        has_feature = JWTSubscriptionService.has_feature_access(features_bitmap, feature_name)
        
        if not has_feature:
            return {
                'allowed': False,
                'message': f'{feature_name} not available in {current_tier} plan',
                'current_tier': current_tier,
                'required_tier': get_minimum_tier_for_feature(feature_name)
            }
        
        return {
            'allowed': True,
            'current_tier': current_tier,
            'feature': feature_name,
            'expires_at': subscription_claims.get('expires_at')
        }
        
    except Exception as e:
        logger.error(f"JWT feature access check failed: {str(e)}")
        return {
            'allowed': False,
            'message': 'Feature access validation failed',
            'current_tier': 'unknown',
            'required_tier': min_tier or 'beginning'
        }


def get_minimum_tier_for_feature(feature_name):
    """Get minimum tier required for a feature"""
    feature_tier_map = {
        'deployment': 'beginning',
        'analytics': 'pro',
        'custom_domains': 'beginning',
        'white_label': 'pro',
        'dedicated_support': 'pro',
        'multiple_workspaces': 'pro',
        'advanced_analytics': 'pro',
        'bulk_operations': 'enterprise'
    }
    
    return feature_tier_map.get(feature_name, 'beginning')


def get_user_subscription_summary(jwt_payload):
    """
    Extract subscription summary from JWT for frontend display
    
    Args:
        jwt_payload: JWT payload dict
        
    Returns:
        dict: Subscription summary for frontend
    """
    subscription_claims = jwt_payload.get('subscription', {})
    
    if not subscription_claims:
        return {
            'tier': 'free',
            'status': 'none',
            'features': [],
            'expires_at': None,
            'limits': {}
        }
    
    # Convert bitmap back to feature list
    features_bitmap = subscription_claims.get('features_bitmap', 0)
    enabled_features = []
    
    try:
        from authentication.services.jwt_subscription_service import JWTSubscriptionService
        enabled_features = JWTSubscriptionService.get_feature_list_from_bitmap(features_bitmap)
    except Exception as e:
        logger.warning(f"Failed to convert bitmap to features: {str(e)}")
    
    return {
        'tier': subscription_claims.get('tier', 'free'),
        'status': subscription_claims.get('status', 'none'),
        'features': enabled_features,
        'expires_at': subscription_claims.get('expires_at'),
        'limits': subscription_claims.get('limits', {}),
        'plan_id': subscription_claims.get('plan_id')
    }


def cache_subscription_data(user_id, data, timeout=300):
    """
    Cache subscription data for performance
    
    Args:
        user_id: User ID for cache key
        data: Data to cache
        timeout: Cache timeout in seconds (default 5 minutes)
    """
    cache_key = f"subscription_data_{user_id}"
    cache.set(cache_key, data, timeout)


def get_cached_subscription_data(user_id):
    """
    Get cached subscription data
    
    Args:
        user_id: User ID for cache key
        
    Returns:
        dict or None: Cached data or None if not found
    """
    cache_key = f"subscription_data_{user_id}"
    return cache.get(cache_key)


class FeatureAccessMixin:
    """
    Mixin for views that need subscription feature access checks
    Provides common methods for feature gating
    """
    
    def check_subscription_feature(self, feature_name, min_tier=None):
        """
        Check if current user has access to feature
        
        Args:
            feature_name: Feature to check
            min_tier: Minimum tier required
            
        Returns:
            dict: Access result
        """
        jwt_payload = getattr(self.request, 'jwt_payload', None)
        
        if not jwt_payload:
            return {
                'allowed': False,
                'message': 'Authentication required'
            }
        
        return check_jwt_feature_access(jwt_payload, feature_name, min_tier)
    
    def require_feature_or_403(self, feature_name, min_tier=None):
        """
        Check feature access and raise 403 if not allowed
        
        Args:
            feature_name: Feature to check
            min_tier: Minimum tier required
            
        Raises:
            PermissionDenied: If feature access denied
        """
        from django.core.exceptions import PermissionDenied
        
        access_result = self.check_subscription_feature(feature_name, min_tier)
        
        if not access_result['allowed']:
            raise PermissionDenied(access_result['message'])
    
    def get_subscription_context(self):
        """
        Get subscription context for template rendering
        
        Returns:
            dict: Subscription context
        """
        jwt_payload = getattr(self.request, 'jwt_payload', None)
        
        if not jwt_payload:
            return {'subscription': None}
        
        return {
            'subscription': get_user_subscription_summary(jwt_payload)
        }


def validate_subscription_webhook_signature(request, secret_key):
    """
    Validate webhook signature for subscription updates
    
    Args:
        request: HTTP request object
        secret_key: Webhook secret key
        
    Returns:
        bool: True if signature is valid
    """
    try:
        import hmac
        import hashlib
        
        signature = request.headers.get('X-Signature')
        if not signature:
            return False
        
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Webhook signature validation failed: {str(e)}")
        return False