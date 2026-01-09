"""
JWT Subscription Claims Service
Minimal JWT with tier + version hash (Industry Standard: Stripe/GitHub/Vercel)
Full capabilities fetched separately via /api/me/capabilities endpoint
"""
import hashlib
import logging
import os
from pathlib import Path
from django.core.cache import cache
from django.utils import timezone
from .jwt_security_service import JWTSecurityService

logger = logging.getLogger(__name__)


class JWTSubscriptionService(JWTSecurityService):
    """
    Enhanced JWT service with minimal subscription claims

    JWT contains: tier, status, expires_at, capabilities_version
    Capabilities are fetched separately via API for true dynamic updates
    """

    # Cache keys
    SUBSCRIPTION_CACHE_PREFIX = 'subscription_claims_'
    CAPABILITIES_VERSION_CACHE = 'capabilities_version_hash'

    @staticmethod
    def create_subscription_claims(user):
        """
        Generate MINIMAL subscription claims for JWT payload
        Industry-standard: JWT = identity + tier, not full capabilities

        NO workspace context in JWT - workspace is sent via X-Workspace-Id header

        Args:
            user: User instance

        Returns:
            dict: Minimal subscription claims for JWT
        """
        try:
            # Check cache first for performance (graceful degradation if Redis down)
            cache_key = f"{JWTSubscriptionService.SUBSCRIPTION_CACHE_PREFIX}{user.id}"
            cached_claims = None

            try:
                cached_claims = cache.get(cache_key)
                if cached_claims:
                    logger.debug(f"Cache HIT for subscription claims user {user.id}")
                    return cached_claims
            except Exception as cache_error:
                logger.warning(f"Cache unavailable for user {user.id}: {str(cache_error)}")

            # Cache miss or error - get from authoritative source (DATABASE)
            logger.debug(f"Cache MISS for subscription claims user {user.id} - querying DB")

            from subscription.models import Subscription

            # Get subscription (signals.py guarantees every user has one)
            subscription = Subscription.objects.select_related('plan').get(user=user)

            # Generate MINIMAL claims (industry standard)
            claims = JWTSubscriptionService._create_minimal_subscription_claims(subscription)

            # Add trial claims
            claims['trial'] = JWTSubscriptionService._create_trial_claims(user)

            # Add template claims
            claims['templates'] = JWTSubscriptionService._create_template_claims(user)

            # Try to cache for 5 minutes (graceful if cache unavailable)
            try:
                cache.set(cache_key, claims, timeout=300)
                logger.debug(f"Cached subscription claims for user {user.id}")
            except Exception as cache_error:
                logger.warning(f"Cache write failed for user {user.id}: {str(cache_error)}")

            return claims

        except Exception as e:
            logger.error(f"Subscription claims generation error for user {user.id}: {str(e)}")
            return JWTSubscriptionService._create_error_claims()

    @staticmethod
    def _create_minimal_subscription_claims(subscription):
        """
        Create MINIMAL claims for subscription (Industry Standard: Stripe/Auth0/Shopify)

        JWT contains only:
        - tier (what subscription they have)
        - status (is it active?)
        - expires_at (when does it end?)
        - capabilities_version (hash of YAML file for cache invalidation)
        - billing_cycle, currency (billing info)

        Full capabilities are fetched separately via /api/me/capabilities
        This allows YAML changes without invalidating all JWTs
        """
        plan = subscription.plan

        return {
            'tier': plan.tier,
            'status': subscription.status,
            'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
            'capabilities_version': JWTSubscriptionService._get_capabilities_version(),
            'billing_cycle': subscription.billing_cycle,
            'currency': subscription.currency,
        }

    @staticmethod
    def _create_error_claims():
        """Create minimal claims for error cases"""
        return {
            'tier': 'free',
            'status': 'error',
            'expires_at': None,
            'capabilities_version': 'error',
            'billing_cycle': 'monthly',
            'currency': 'XAF',
        }

    @staticmethod
    def _get_capabilities_version():
        """
        Generate version hash from plans.yaml file
        When YAML changes, hash changes → frontend detects and refetches capabilities

        Industry standard: GitHub uses commit SHA, Vercel uses deployment ID
        We use file modification time hash (simpler)

        Returns:
            str: Version hash (e.g., 'v2_abc123de')
        """
        try:
            # Check cache first (1 hour TTL)
            cached_version = cache.get(JWTSubscriptionService.CAPABILITIES_VERSION_CACHE)
            if cached_version:
                return cached_version

            # Generate new version from YAML file modification time
            from subscription.services.capability_engine import PLANS_YAML_PATH

            if not PLANS_YAML_PATH.exists():
                logger.warning(f"plans.yaml not found at {PLANS_YAML_PATH}")
                return 'v1_fallback'

            # Use file modification time + size for version
            stat = os.stat(PLANS_YAML_PATH)
            version_data = f"{stat.st_mtime}_{stat.st_size}"
            version_hash = hashlib.md5(version_data.encode()).hexdigest()[:8]
            version = f"v2_{version_hash}"

            # Cache for 1 hour
            cache.set(JWTSubscriptionService.CAPABILITIES_VERSION_CACHE, version, timeout=3600)

            return version

        except Exception as e:
            logger.error(f"Failed to generate capabilities version: {str(e)}")
            return 'v1_error'

    @staticmethod
    def invalidate_subscription_cache(user_id):
        """
        Invalidate subscription claims cache for user
        Call this when subscription changes

        Args:
            user_id: User ID to invalidate cache for
        """
        try:
            cache_key = f"{JWTSubscriptionService.SUBSCRIPTION_CACHE_PREFIX}{user_id}"
            cache.delete(cache_key)
            logger.debug(f"Invalidated subscription cache for user {user_id}")
        except Exception as cache_error:
            logger.warning(f"Cache delete failed for user {user_id}: {str(cache_error)}")

    @staticmethod
    def invalidate_capabilities_version_cache():
        """
        Invalidate capabilities version cache
        Call this after plans.yaml changes (e.g., after sync_plans command)
        """
        try:
            cache.delete(JWTSubscriptionService.CAPABILITIES_VERSION_CACHE)
            logger.info("Invalidated capabilities version cache - new version will be generated")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate capabilities version cache: {str(cache_error)}")

    @staticmethod
    def enhance_access_payload(payload, user):
        """
        Enhance existing JWT payload with subscription claims
        Non-destructive enhancement of existing tokens

        NO workspace context - workspace sent via X-Workspace-Id header

        Args:
            payload: Existing JWT payload dict
            user: User instance

        Returns:
            dict: Enhanced payload with subscription claims
        """
        try:
            subscription_claims = JWTSubscriptionService.create_subscription_claims(user)

            # Add subscription claims to payload
            payload['subscription'] = subscription_claims

            return payload

        except Exception as e:
            logger.error(f"JWT payload enhancement failed for user {user.id}: {str(e)}")
            # Return original payload if enhancement fails
            return payload

    @staticmethod
    def verify_subscription_claims(payload):
        """
        Verify subscription claims are valid and not tampered

        Args:
            payload: JWT payload dict

        Returns:
            dict: Verification result
        """
        try:
            subscription_claims = payload.get('subscription', {})

            if not subscription_claims:
                return {'valid': True, 'tier': 'free'}  # No claims = free tier

            # Basic validation
            required_fields = ['tier', 'status', 'capabilities_version']
            for field in required_fields:
                if field not in subscription_claims:
                    return {'valid': False, 'error': f'Missing {field} in subscription claims'}

            # Validate tier
            valid_tiers = ['free', 'beginner', 'pro', 'enterprise']
            if subscription_claims['tier'] not in valid_tiers:
                return {'valid': False, 'error': 'Invalid subscription tier'}

            return {
                'valid': True,
                'tier': subscription_claims['tier'],
                'status': subscription_claims['status'],
                'version': subscription_claims['capabilities_version']
            }

        except Exception as e:
            logger.error(f"Subscription claims verification error: {str(e)}")
            return {'valid': False, 'error': 'Claims verification failed'}

    @staticmethod
    def get_user_capabilities(user):
        """
        Get full capabilities for user's current tier
        This is what /api/me/capabilities endpoint should call

        Args:
            user: User instance

        Returns:
            dict: Full capabilities from YAML
        """
        try:
            from subscription.models import Subscription
            from subscription.services.capability_engine import CapabilityEngine

            # Get user's subscription
            subscription = Subscription.objects.select_related('plan').get(user=user)
            tier = subscription.plan.tier

            # Get capabilities from YAML
            capabilities = CapabilityEngine.get_plan_capabilities(tier)

            return {
                'tier': tier,
                'status': subscription.status,
                'capabilities': capabilities,
                'version': JWTSubscriptionService._get_capabilities_version(),
                'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
            }

        except Exception as e:
            logger.error(f"Failed to get capabilities for user {user.id}: {str(e)}")
            # Fallback to free tier
            from subscription.services.capability_engine import CapabilityEngine
            return {
                'tier': 'free',
                'status': 'error',
                'capabilities': CapabilityEngine.get_plan_capabilities('free'),
                'version': 'error',
                'expires_at': None,
            }

    @staticmethod
    def _create_trial_claims(user):
        """
        Create trial-specific claims for JWT - secure and robust version

        INDUSTRY STANDARD (Stripe/Chargebee): Trial eligibility revoked on paid subscription activation
        - Active paid subscription (tier != 'free') → eligible: false
        - Trial already used → eligible: false
        - Otherwise → eligible: true
        """
        if not user or not hasattr(user, 'id'):
            logger.error("Invalid user object passed to trial claims")
            return JWTSubscriptionService._create_safe_trial_fallback()

        try:
            from subscription.models import Trial, Subscription
            from django.db import transaction

            # Single atomic query to get trial state
            with transaction.atomic():
                # Check if user has active PAID subscription
                has_paid_subscription = Subscription.objects.filter(
                    user=user,
                    status='active'
                ).exclude(plan__tier='free').exists()

                # Check user eligibility (database authoritative)
                trial_used = user.trial_used_at is not None

                # Get active trial with single optimized query
                active_trial = None
                try:
                    active_trial = Trial.objects.select_related().get(
                        user=user,
                        status='active'
                    )
                    # Verify trial hasn't expired
                    if active_trial.is_expired:
                        active_trial.expire()  # Update status
                        active_trial = None
                except Trial.DoesNotExist:
                    pass
                except Trial.MultipleObjectsReturned:
                    # Data integrity issue - log and use most recent
                    logger.warning(f"Multiple active trials found for user {user.id}")
                    active_trial = Trial.objects.filter(
                        user=user,
                        status='active'
                    ).order_by('-created_at').first()

                # Build claims based on state (priority order matters)
                if active_trial:
                    # User has active trial right now
                    return {
                        'eligible': False,
                        'used_trial': True,
                        'current_tier': active_trial.tier,
                        'expires_at': active_trial.expires_at.isoformat(),
                        'can_upgrade': active_trial.can_upgrade,
                        'days_remaining': max(0, active_trial.days_remaining),
                        'used_at': user.trial_used_at.isoformat() if user.trial_used_at else None
                    }
                elif trial_used:
                    # User already used their one-time trial
                    return {
                        'eligible': False,
                        'used_trial': True,
                        'current_tier': user.trial_tier_used,
                        'expires_at': None,
                        'can_upgrade': False,
                        'days_remaining': 0,
                        'used_at': user.trial_used_at.isoformat()
                    }
                elif has_paid_subscription:
                    # User has paid subscription - trial revoked (industry standard)
                    return {
                        'eligible': False,
                        'used_trial': False,
                        'current_tier': None,
                        'expires_at': None,
                        'can_upgrade': False,
                        'days_remaining': 0,
                        'used_at': None,
                        'ineligible_reason': 'paid_subscription_active'
                    }
                else:
                    # User is eligible for trial
                    return {
                        'eligible': True,
                        'used_trial': False,
                        'current_tier': None,
                        'expires_at': None,
                        'can_upgrade': False,
                        'days_remaining': 0,
                        'used_at': None
                    }

        except Exception as e:
            logger.error(f"Trial claims generation error for user {user.id}: {str(e)}")
            return JWTSubscriptionService._create_safe_trial_fallback(user)

    @staticmethod
    def _create_safe_trial_fallback(user=None):
        """Safe fallback for trial claims in error cases"""
        return {
            'eligible': False if (user and user.trial_used_at) else True,
            'used_trial': bool(user and user.trial_used_at),
            'current_tier': None,
            'expires_at': None,
            'can_upgrade': False,
            'days_remaining': 0,
            'used_at': user.trial_used_at.isoformat() if (user and user.trial_used_at) else None
        }

    @staticmethod
    def _create_template_claims(user):
        """Create template ownership claims for JWT"""
        try:
            from subscription.models import TemplatePurchase

            # Get user's template purchases
            purchases = TemplatePurchase.objects.filter(buyer=user).select_related('template')
            owned_templates = [str(p.template.id) for p in purchases]

            return {
                'owned_count': len(owned_templates),
                'owned_templates': owned_templates,
            }

        except Exception as e:
            logger.error(f"Template claims generation error for user {user.id}: {str(e)}")
            return {
                'owned_count': 0,
                'owned_templates': [],
            }
