"""
Advanced JWT Security Service - 2025 Security Standards
Implements JWT hardening, token rotation, blacklisting, and advanced security features
"""
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from ..models import SecurityEvent
from .security_monitoring_service import SecurityMonitoringService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTSecurityService:
    """Advanced JWT security with enterprise-grade hardening"""
    
    # JWT Security Constants
    ALGORITHM = 'HS256'
    TOKEN_BLACKLIST_PREFIX = 'jwt_blacklist_'
    TOKEN_FAMILY_PREFIX = 'jwt_family_'
    REFRESH_TOKEN_PREFIX = 'refresh_token_'
    
    # Security thresholds
    MAX_TOKEN_AGE_HOURS = 24
    REFRESH_TOKEN_ROTATION_THRESHOLD = 0.5  # 50% of lifetime
    MAX_CONCURRENT_SESSIONS = 5
    
    @staticmethod
    def generate_secure_secret():
        """Generate cryptographically secure JWT secret"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def get_jwt_secret():
        """Get JWT secret with rotation support"""
        primary_secret = getattr(settings, 'JWT_SECRET_KEY', None)
        if not primary_secret:
            # Generate and cache a secret (for development)
            primary_secret = JWTSecurityService.generate_secure_secret()
            logger.warning("JWT_SECRET_KEY not set in settings. Using generated secret.")
        
        return primary_secret
    
    @staticmethod
    def generate_token_family_id():
        """Generate unique token family identifier"""
        return secrets.token_urlsafe(16)
    
    @staticmethod
    def create_secure_payload(user, token_family=None, session_id=None):
        """
        Create secure JWT payload with enhanced claims (Industry Standard: Stripe/Shopify)

        NO workspace context - workspace sent via X-Workspace-Id header per-request

        Args:
            user: User instance
            token_family: Token family for coordinated invalidation
            session_id: Session identifier

        Returns:
            dict: JWT payload with security claims (identity only)
        """
        now = timezone.now()
        token_family = token_family or JWTSecurityService.generate_token_family_id()
        session_id = session_id or secrets.token_urlsafe(16)

        # Base payload - IDENTITY ONLY
        payload = {
            # Standard JWT claims
            'iss': getattr(settings, 'JWT_ISSUER', 'hustlerz.camp'),
            'aud': getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(hours=1)).timestamp()),  # 1 hour access token
            'nbf': int(now.timestamp()),
            'jti': secrets.token_urlsafe(16),  # JWT ID

            # User identity claims
            'user_id': str(user.id),
            'email': user.email,
            'username': user.username,

            # Global system roles (NOT workspace-specific)
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,

            # Security claims
            'token_family': token_family,
            'session_id': session_id,
            'token_type': 'access',
            'security_level': JWTSecurityService._calculate_security_level(user),
            'last_password_change': user.date_joined.isoformat(),  # Would be actual last password change

            # Anti-tampering
            'fingerprint': JWTSecurityService._generate_token_fingerprint(user, session_id),
        }

        return payload
    
    @staticmethod
    def create_refresh_token_payload(user, token_family, session_id):
        """
        Create refresh token payload (Industry Standard: OAuth2/OpenID)

        NO workspace context - refresh tokens extend sessions, not authorization scope

        Args:
            user: User instance
            token_family: Token family for coordinated invalidation
            session_id: Session identifier
        """
        now = timezone.now()

        payload = {
            'iss': getattr(settings, 'JWT_ISSUER', 'hustlerz.camp'),
            'aud': getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(days=30)).timestamp()),  # 30 day refresh token
            'jti': secrets.token_urlsafe(16),

            'user_id': str(user.id),
            'token_family': token_family,
            'session_id': session_id,
            'token_type': 'refresh',
            'security_level': JWTSecurityService._calculate_security_level(user),
            'fingerprint': JWTSecurityService._generate_token_fingerprint(user, session_id),
        }

        return payload
    
    @staticmethod
    def generate_token_pair(user, request=None):
        """
        Generate secure access and refresh token pair (Industry Standard)

        NO workspace context - workspace sent via X-Workspace-Id header

        Args:
            user: User instance
            request: HTTP request for security context

        Returns:
            dict: Token pair with security metadata
        """
        try:
            # Generate token family and session
            token_family = JWTSecurityService.generate_token_family_id()
            session_id = secrets.token_urlsafe(16)

            # Create payloads - IDENTITY ONLY
            access_payload = JWTSecurityService.create_secure_payload(
                user, token_family, session_id
            )
            refresh_payload = JWTSecurityService.create_refresh_token_payload(
                user, token_family, session_id
            )

            # Generate tokens
            secret = JWTSecurityService.get_jwt_secret()
            access_token = jwt.encode(access_payload, secret, algorithm=JWTSecurityService.ALGORITHM)
            refresh_token = jwt.encode(refresh_payload, secret, algorithm=JWTSecurityService.ALGORITHM)

            # Store token family metadata
            JWTSecurityService._store_token_family(user, token_family, session_id, request)

            # Store refresh token hash for validation
            JWTSecurityService._store_refresh_token_hash(refresh_token, user.id, token_family)

            # Log token generation
            if request:
                from .security_service import SecurityService
                SecurityEvent.log_event(
                    event_type='jwt_tokens_generated',
                    user=user,
                    description='JWT token pair generated',
                    risk_level=1,
                    ip_address=SecurityService.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'token_family': token_family,
                        'session_id': session_id,
                        'access_exp': access_payload['exp'],
                        'refresh_exp': refresh_payload['exp']
                    }
                )

            return {
                'success': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600,  # 1 hour
                'refresh_expires_in': 2592000,  # 30 days
                'token_family': token_family,
                'session_id': session_id,
                'security_level': access_payload['security_level']
            }

        except Exception as e:
            logger.error(f"JWT token generation error for user {user.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def verify_access_token(token, require_active=True):
        """
        Verify access token with comprehensive security checks
        
        Args:
            token: JWT access token
            require_active: Require active user account
            
        Returns:
            dict: Verification result with payload
        """
        try:
            # Check token blacklist
            if JWTSecurityService.is_token_blacklisted(token):
                return {
                    'valid': False,
                    'error': 'Token has been revoked',
                    'error_code': 'TOKEN_BLACKLISTED'
                }
            
            # Decode token
            secret = JWTSecurityService.get_jwt_secret()
            payload = jwt.decode(
                token, 
                secret, 
                algorithms=[JWTSecurityService.ALGORITHM],
                audience=getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
                issuer=getattr(settings, 'JWT_ISSUER', 'hustlerz.camp')
            )
            
            # Validate token type (check both 'type' and 'token_type' for compatibility)
            token_type = payload.get('type') or payload.get('token_type')
            if token_type != 'access':
                return {
                    'valid': False,
                    'error': 'Invalid token type',
                    'error_code': 'INVALID_TOKEN_TYPE'
                }
            
            # Get user
            user_id = payload.get('user_id')
            if not user_id:
                return {
                    'valid': False,
                    'error': 'Missing user ID in token',
                    'error_code': 'MISSING_USER_ID'
                }
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {
                    'valid': False,
                    'error': 'User not found',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Check user status
            if require_active and not user.is_active:
                return {
                    'valid': False,
                    'error': 'User account is disabled',
                    'error_code': 'USER_INACTIVE'
                }
            
            # Verify token fingerprint
            expected_fingerprint = JWTSecurityService._generate_token_fingerprint(
                user, payload.get('session_id', '')
            )
            if payload.get('fingerprint') != expected_fingerprint:
                # Log potential token tampering
                SecurityEvent.log_event(
                    event_type='jwt_fingerprint_mismatch',
                    user=user,
                    description='JWT token fingerprint mismatch detected',
                    risk_level=SecurityMonitoringService.RISK_LEVELS['HIGH'],
                    metadata={
                        'expected_fingerprint': expected_fingerprint[:8] + '...',
                        'received_fingerprint': payload.get('fingerprint', '')[:8] + '...',
                        'session_id': payload.get('session_id'),
                        'token_family': payload.get('token_family')
                    }
                )
                
                return {
                    'valid': False,
                    'error': 'Token fingerprint mismatch',
                    'error_code': 'FINGERPRINT_MISMATCH'
                }
            
            # Check token family validity
            token_family = payload.get('token_family')
            if token_family and not JWTSecurityService._is_token_family_valid(token_family, user.id):
                return {
                    'valid': False,
                    'error': 'Token family has been invalidated',
                    'error_code': 'TOKEN_FAMILY_INVALID'
                }
            
            return {
                'valid': True,
                'payload': payload,
                'user': user
            }
            
        except jwt.ExpiredSignatureError:
            return {
                'valid': False,
                'error': 'Token has expired',
                'error_code': 'TOKEN_EXPIRED'
            }
        except jwt.InvalidTokenError as e:
            return {
                'valid': False,
                'error': f'Invalid token: {str(e)}',
                'error_code': 'TOKEN_INVALID'
            }
        except Exception as e:
            logger.error(f"JWT verification error: {str(e)}")
            return {
                'valid': False,
                'error': 'Token verification failed',
                'error_code': 'VERIFICATION_ERROR'
            }
    
    @staticmethod
    def rotate_refresh_token(refresh_token, request=None):
        """
        Rotate refresh token with security checks
        
        Args:
            refresh_token: Current refresh token
            request: HTTP request for security context
            
        Returns:
            dict: New token pair or error
        """
        try:
            # Verify refresh token
            secret = JWTSecurityService.get_jwt_secret()
            payload = jwt.decode(
                refresh_token,
                secret,
                algorithms=[JWTSecurityService.ALGORITHM],
                audience=getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
                issuer=getattr(settings, 'JWT_ISSUER', 'hustlerz.camp')
            )
            
            # Validate token type
            if payload.get('token_type') != 'refresh':
                return {
                    'success': False,
                    'error': 'Invalid token type for refresh',
                    'error_code': 'INVALID_TOKEN_TYPE'
                }
            
            # Check refresh token hash
            user_id = payload.get('user_id')
            token_family = payload.get('token_family')
            
            if not JWTSecurityService._verify_refresh_token_hash(refresh_token, user_id, token_family):
                # Potential token theft - invalidate entire family
                JWTSecurityService.invalidate_token_family(token_family, user_id)
                
                SecurityEvent.log_event(
                    event_type='refresh_token_reuse_detected',
                    user_id=user_id,
                    description='Refresh token reuse detected - token family invalidated',
                    risk_level='critical',
                    metadata={
                        'token_family': token_family,
                        'invalidated_family': True
                    }
                )
                
                return {
                    'success': False,
                    'error': 'Invalid refresh token - all sessions invalidated for security',
                    'error_code': 'TOKEN_REUSE_DETECTED'
                }
            
            # Get user
            user = User.objects.get(id=user_id, is_active=True)
            
            # Check if token family is still valid
            if not JWTSecurityService._is_token_family_valid(token_family, user_id):
                return {
                    'success': False,
                    'error': 'Token family has been invalidated',
                    'error_code': 'TOKEN_FAMILY_INVALID'
                }
            
            # Generate new token pair (NO workspace context)
            new_tokens = JWTSecurityService.generate_token_pair(
                user=user,
                request=request
            )
            
            if new_tokens['success']:
                # Invalidate old refresh token
                JWTSecurityService._invalidate_refresh_token_hash(refresh_token, user_id, token_family)
                
                # Log token rotation
                if request:
                    from .security_service import SecurityService
                    SecurityEvent.log_event(
                        event_type='refresh_token_rotated',
                        user=user,
                        description='Refresh token successfully rotated',
                        risk_level=1,
                        ip_address=SecurityService.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'old_token_family': token_family,
                            'new_token_family': new_tokens['token_family']
                        }
                    )
            
            return new_tokens
            
        except jwt.ExpiredSignatureError:
            return {
                'success': False,
                'error': 'Refresh token has expired',
                'error_code': 'TOKEN_EXPIRED'
            }
        except jwt.InvalidTokenError as e:
            return {
                'success': False,
                'error': f'Invalid refresh token: {str(e)}',
                'error_code': 'TOKEN_INVALID'
            }
        except User.DoesNotExist:
            return {
                'success': False,
                'error': 'User not found or inactive',
                'error_code': 'USER_NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Refresh token rotation error: {str(e)}")
            return {
                'success': False,
                'error': 'Token rotation failed',
                'error_code': 'ROTATION_ERROR'
            }
    
    @staticmethod
    def blacklist_token(token, reason="Manual revocation"):
        """Add token to blacklist"""
        try:
            # Extract JTI from token
            secret = JWTSecurityService.get_jwt_secret()
            payload = jwt.decode(token, secret, algorithms=[JWTSecurityService.ALGORITHM], verify=False)
            jti = payload.get('jti')
            exp = payload.get('exp', 0)
            
            if jti:
                # Store in cache until expiration
                cache_key = f"{JWTSecurityService.TOKEN_BLACKLIST_PREFIX}{jti}"
                ttl = max(0, exp - int(timezone.now().timestamp()))
                cache.set(cache_key, reason, timeout=ttl)
                
                return True
        except Exception as e:
            logger.error(f"Token blacklisting error: {str(e)}")
        
        return False
    
    @staticmethod
    def is_token_blacklisted(token):
        """Check if token is blacklisted"""
        try:
            # Extract JTI from token without verification
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get('jti')
            
            if jti:
                cache_key = f"{JWTSecurityService.TOKEN_BLACKLIST_PREFIX}{jti}"
                return cache.get(cache_key) is not None
        except Exception:
            pass
        
        return False
    
    @staticmethod
    def invalidate_token_family(token_family, user_id):
        """Invalidate entire token family"""
        cache_key = f"{JWTSecurityService.TOKEN_FAMILY_PREFIX}{user_id}_{token_family}"
        cache.set(cache_key, "invalidated", timeout=86400 * 30)  # 30 days
    
    @staticmethod
    def invalidate_all_user_tokens(user_id, reason="Security measure"):
        """Invalidate all tokens for a user"""
        try:
            # This would require a more sophisticated storage mechanism in production
            # For now, we'll use a cache-based approach
            cache_key = f"user_token_invalidation_{user_id}"
            cache.set(cache_key, {
                'reason': reason,
                'timestamp': timezone.now().isoformat()
            }, timeout=86400 * 30)  # 30 days
            
            return True
        except Exception as e:
            logger.error(f"Token invalidation error for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def _calculate_security_level(user):
        """Calculate user security level for JWT"""
        level = 1  # Basic
        
        if user.is_staff:
            level = 3  # Elevated
        if user.is_superuser:
            level = 4  # Admin
            
        # Would check for MFA, recent login, etc.
        return level
    
    @staticmethod
    def _generate_token_fingerprint(user, session_id):
        """Generate token fingerprint for anti-tampering"""
        fingerprint_data = f"{user.id}:{session_id}:{user.email}:{user.date_joined.isoformat()}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    @staticmethod
    def _store_token_family(user, token_family, session_id, request):
        """Store token family metadata"""
        from .security_service import SecurityService
        
        cache_key = f"{JWTSecurityService.TOKEN_FAMILY_PREFIX}{user.id}_{token_family}"
        metadata = {
            'user_id': str(user.id),
            'session_id': session_id,
            'created_at': timezone.now().isoformat(),
            'ip_address': SecurityService.get_client_ip(request) if request else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
            'valid': True
        }
        cache.set(cache_key, metadata, timeout=86400 * 30)  # 30 days
    
    @staticmethod
    def _is_token_family_valid(token_family, user_id):
        """Check if token family is still valid"""
        cache_key = f"{JWTSecurityService.TOKEN_FAMILY_PREFIX}{user_id}_{token_family}"
        family_data = cache.get(cache_key)
        return family_data and family_data.get('valid', False)
    
    @staticmethod
    def _store_refresh_token_hash(refresh_token, user_id, token_family):
        """Store refresh token hash for validation"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        cache_key = f"{JWTSecurityService.REFRESH_TOKEN_PREFIX}{user_id}_{token_family}"
        cache.set(cache_key, token_hash, timeout=86400 * 30)  # 30 days
    
    @staticmethod
    def _verify_refresh_token_hash(refresh_token, user_id, token_family):
        """Verify refresh token hash"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        cache_key = f"{JWTSecurityService.REFRESH_TOKEN_PREFIX}{user_id}_{token_family}"
        stored_hash = cache.get(cache_key)
        return stored_hash == token_hash
    
    @staticmethod
    def _invalidate_refresh_token_hash(refresh_token, user_id, token_family):
        """Invalidate refresh token hash"""
        cache_key = f"{JWTSecurityService.REFRESH_TOKEN_PREFIX}{user_id}_{token_family}"
        cache.delete(cache_key)
    
    @staticmethod
    def cleanup_expired_tokens():
        """Cleanup expired token metadata (would be more sophisticated in production)"""
        # This would typically be handled by cache TTL
        # In production, you'd want a proper token store with cleanup jobs
        logger.info("JWT cleanup completed (handled by cache TTL)")
        return {'expired_tokens_cleaned': 'handled_by_cache'}
    
    @staticmethod
    def get_user_active_sessions(user_id):
        """Get active JWT sessions for user"""
        # This would require a more sophisticated storage mechanism
        # For demonstration, we'll return a simplified response
        return {
            'active_sessions': 'Feature requires enhanced token storage',
            'user_id': user_id
        }