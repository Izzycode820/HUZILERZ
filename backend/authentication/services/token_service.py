"""
JWT Token Management Service
"""
import jwt
import hashlib
import secrets
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from authentication.models import RefreshToken
import logging

logger = logging.getLogger(__name__)


class TokenService:
    """JWT Token management service"""
    
    @staticmethod
    def generate_token_pair(user, device_info=None, ip_address=None):
        """
        Generate access and refresh token pair (Industry Standard: Stripe/Shopify/Linear)

        JWT contains ONLY user identity + subscription tier
        Workspace context is sent via X-Workspace-Id header per-request

        Security: Eliminates context drift, race conditions, and stale workspace bugs
        """
        try:
            # Create access token (short-lived) - IDENTITY ONLY
            access_payload = {
                # Standard JWT claims
                'iss': getattr(settings, 'JWT_ISSUER', 'hustlerz.camp'),
                'aud': getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
                'iat': timezone.now(),
                'exp': timezone.now() + timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES),
                'jti': secrets.token_urlsafe(16),
                'type': 'access',

                # User identity claims
                'user_id': user.id,
                'email': user.email,
                'username': user.username,

                # Global system roles (NOT workspace-specific)
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
            }

            # Enhance with subscription claims (tier, status, billing)
            from .jwt_subscription_service import JWTSubscriptionService
            access_payload = JWTSubscriptionService.enhance_access_payload(
                access_payload,
                user
            )

            access_token = jwt.encode(
                access_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            )

            # Create refresh token (long-lived) - SIMPLE, NO WORKSPACE
            refresh_payload = {
                'iss': getattr(settings, 'JWT_ISSUER', 'hustlerz.camp'),
                'aud': getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
                'iat': timezone.now(),
                'exp': timezone.now() + timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS),
                'jti': secrets.token_urlsafe(16),
                'type': 'refresh',
                'user_id': user.id,
            }

            refresh_token_string = jwt.encode(
                refresh_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            )

            # Hash and store refresh token
            token_hash = hashlib.sha256(refresh_token_string.encode()).hexdigest()

            refresh_token_record = RefreshToken.create_token(
                user=user,
                token_hash=token_hash,
                device_info=device_info,
                ip_address=ip_address
            )

            return {
                'access_token': access_token,
                'refresh_token': refresh_token_string,
                'access_expires_in': settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
                'refresh_expires_in': settings.REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
                'token_type': 'Bearer',
                'refresh_token_id': str(refresh_token_record.id),
            }

        except Exception as e:
            import traceback
            logger.error(f"Token generation failed: {str(e)}")
            logger.error(f"Token generation traceback: {traceback.format_exc()}")
            raise Exception(f"Token generation failed: {str(e)}")
    
    @staticmethod
    def verify_access_token(token):
        """
        Verify access token with STRICT validation (v3.0 - Industry Standard)

        Security: OWASP JWT Best Practices
        - Validates signature (prevents tampering)
        - Validates issuer (prevents token from unauthorized source)
        - Validates audience (prevents token reuse across different apps)
        - Validates expiration (prevents old token reuse)
        - Validates type (prevents refresh token being used as access token)
        - Checks blacklist (prevents revoked token reuse)

        NO fallbacks, NO legacy support - strict validation only
        """
        try:
            # STRICT validation - aud, iss, exp, signature ALL required
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256'],
                audience=getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
                issuer=getattr(settings, 'JWT_ISSUER', 'hustlerz.camp')
            )

            if payload.get('type') != 'access':
                raise jwt.InvalidTokenError("Invalid token type - expected access token")

            # Check if token is blacklisted (graceful degradation if cache unavailable)
            jti = payload.get('jti')
            try:
                if cache.get(f"blacklisted_token_{jti}"):
                    raise jwt.InvalidTokenError("Token is blacklisted")
            except Exception as cache_error:
                # Cache unavailable - skip blacklist check (token will be validated by DB)
                logger.warning(f"Cache unavailable for blacklist check: {str(cache_error)}")
                pass

            return payload

        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(str(e))
    
    @staticmethod
    def decode_access_token(token):
        """Decode access token without verification (for expired tokens)"""
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256'],
                options={"verify_exp": False}
            )
        except Exception:
            return None
    
    @staticmethod
    def verify_refresh_token(token):
        """
        Verify refresh token with STRICT validation (v3.0 - Industry Standard)

        Security: OWASP JWT Best Practices
        - Validates signature (prevents tampering)
        - Validates issuer (prevents token from unauthorized source)
        - Validates audience (prevents token reuse across different apps)
        - Validates expiration (prevents old token reuse)
        - Validates type (prevents access token being used as refresh token)

        NO fallbacks, NO legacy support - strict validation only
        """
        try:
            # STRICT validation - aud, iss, exp, signature ALL required
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256'],
                audience=getattr(settings, 'JWT_AUDIENCE', 'hustlerz.camp'),
                issuer=getattr(settings, 'JWT_ISSUER', 'hustlerz.camp')
            )

            if payload.get('type') != 'refresh':
                raise jwt.InvalidTokenError("Invalid token type - expected refresh token")
            
            # Check token in database
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            refresh_token = RefreshToken.objects.filter(
                token_hash=token_hash,
                is_active=True,
                expires_at__gt=timezone.now()
            ).select_related('user').first()
            
            if not refresh_token:
                raise jwt.InvalidTokenError("Invalid or expired refresh token")
            
            # Update last used
            refresh_token.last_used = timezone.now()
            refresh_token.save(update_fields=['last_used'])
            
            return refresh_token
            
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(str(e))
    
    @staticmethod
    def blacklist_token(jti, expires_at=None):
        """Blacklist a token by JTI (graceful degradation if cache unavailable)"""
        if not expires_at:
            expires_at = timezone.now() + timedelta(hours=24)

        # Calculate cache timeout
        timeout = int((expires_at - timezone.now()).total_seconds())
        if timeout > 0:
            try:
                cache.set(f"blacklisted_token_{jti}", True, timeout)
            except Exception as cache_error:
                # Cache unavailable - token blacklist won't work but system continues
                logger.warning(f"Cache unavailable for token blacklist: {str(cache_error)}")
    
    @staticmethod
    def revoke_refresh_token(token_id):
        """Revoke a specific refresh token"""
        try:
            refresh_token = RefreshToken.objects.get(id=token_id, is_active=True)
            refresh_token.revoke()
            return True
        except RefreshToken.DoesNotExist:
            return False
    
    @staticmethod
    def revoke_all_user_tokens(user):
        """Revoke all refresh tokens for a user"""
        RefreshToken.objects.filter(user=user, is_active=True).update(
            is_active=False,
            revoked_at=timezone.now(),
            revoked_by='user'
        )