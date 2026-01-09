"""
Modern Authentication Middleware for HustlerzCamp
- JWT Token Authentication
- Session Management
- Security Headers
"""
import jwt
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

User = get_user_model()
from django.conf import settings
from .models import UserSession
from .services import TokenService, SessionService, SecurityService
import logging

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """JWT Token authentication middleware"""
    
    def process_request(self, request):
        """Process request for JWT authentication"""
        
        # Skip authentication for certain paths
        skip_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/refresh/',
            '/api/public/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            request.user = AnonymousUser()
            return None
        
        # Get token from header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            request.user = AnonymousUser()
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verify token
            payload = TokenService.verify_access_token(token)
            
            # Get user
            user = User.objects.get(id=payload['user_id'])
            
            if not user.is_active:
                return JsonResponse({
                    'error': 'Account is disabled'
                }, status=401)
            
            # Attach user to request
            request.user = user
            request.jwt_payload = payload
            
            # Update session if authenticated
            SessionService.update_session_activity(request, 'authenticated_request')
            
        except jwt.InvalidTokenError as e:
            if request.path.startswith('/api/workspace/') or request.path.startswith('/api/auth/'):
                return JsonResponse({
                    'error': 'Invalid or expired token',
                    'code': 'TOKEN_INVALID'
                }, status=401)
            else:
                request.user = AnonymousUser()
        
        except User.DoesNotExist:
            if request.path.startswith('/api/workspace/') or request.path.startswith('/api/auth/'):
                return JsonResponse({
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }, status=401)
            else:
                request.user = AnonymousUser()
        
        except Exception as e:
            logger.error(f"JWT Authentication error: {str(e)}")
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Authentication failed',
                    'code': 'AUTH_ERROR'
                }, status=500)
            else:
                request.user = AnonymousUser()
        
        return None


class SessionTrackingMiddleware(MiddlewareMixin):
    """Track user sessions and activity"""
    
    def process_request(self, request):
        """Initialize or update user session"""
        
        # Skip for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
        
        # Create or get session
        user = getattr(request, 'user', None)
        if hasattr(user, 'is_authenticated') and not user.is_anonymous:
            # Authenticated user
            session = SessionService.create_session(request, user)
        else:
            # Guest user
            session = SessionService.create_session(request)
        
        # Attach session to request
        request.user_session = session
        
        return None
    
    def process_response(self, request, response):
        """Update session activity on response"""
        
        # Skip for static files
        if request.path.startswith('/static/'):
            return response
        
        # Update session activity
        if request.method == 'GET':
            SessionService.update_session_activity(request, 'page_view')
        else:
            SessionService.update_session_activity(request, 'action')
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses"""
    
    def process_response(self, request, response):
        """Add security headers"""
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP for production
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-src 'none';"
            )
        
        return response


class AuthenticationPromptMiddleware(MiddlewareMixin):
    """Handle smart authentication prompting for guests"""
    
    def process_response(self, request, response):
        """Add authentication prompt headers for eligible guests"""
        
        # Only for HTML responses to guest users
        if (not hasattr(request, 'user') or 
            request.user.is_authenticated or
            not response.get('Content-Type', '').startswith('text/html')):
            return response
        
        # Check if should show auth prompt
        session = getattr(request, 'user_session', None)
        if session and session.should_show_auth_prompt():
            # Add header to trigger frontend prompt
            response['X-Auth-Prompt'] = 'suggest'
            response['X-Auth-Context'] = self._get_auth_context(request, session)
        
        return response
    
    def _get_auth_context(self, request, session):
        """Get authentication context for smart prompting"""
        
        context = 'general'
        
        # Determine context based on user activity
        if 'wishlist' in request.path or 'cart' in request.path:
            context = 'shopping'
        elif 'store' in request.path:
            context = 'store_browsing'
        elif 'product' in request.path:
            context = 'product_interest'
        elif session.page_views >= 10:
            context = 'engaged_browsing'
        
        return context


class RateLimitingMiddleware(MiddlewareMixin):
    """Simple rate limiting for authentication endpoints"""
    
    def process_request(self, request):
        """Check rate limits for sensitive endpoints"""
        
        # Rate limit authentication endpoints
        auth_endpoints = ['/api/auth/login/', '/api/auth/register/']
        
        if request.path in auth_endpoints:
            ip_address = self._get_client_ip(request)
            
            # Check rate limit (5 attempts per minute)
            cache_key = f"auth_rate_limit_{ip_address}"
            from django.core.cache import cache
            
            attempts = cache.get(cache_key, 0)
            if attempts >= 5:
                return JsonResponse({
                    'error': 'Too many authentication attempts. Please try again later.',
                    'code': 'RATE_LIMITED'
                }, status=429)
            
            # Increment counter
            cache.set(cache_key, attempts + 1, 60)  # 1 minute timeout
        
        return None
    
    def _get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CORSMiddleware(MiddlewareMixin):
    """Handle CORS for API endpoints"""
    
    def process_response(self, request, response):
        """Add CORS headers"""
        
        if request.path.startswith('/api/'):
            # Allow specific origins in production
            allowed_origins = getattr(settings, 'ALLOWED_ORIGINS', ['http://localhost:3000'])
            origin = request.META.get('HTTP_ORIGIN')
            
            if origin in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
            
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Authorization, Content-Type, X-Requested-With, Accept, Origin'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
        
        return response
    
    def process_request(self, request):
        """Handle preflight requests"""
        
        if request.method == 'OPTIONS' and request.path.startswith('/api/'):
            response = JsonResponse({'status': 'ok'})
            return self.process_response(request, response)
        
        return None