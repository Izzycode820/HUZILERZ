"""
Subscription Claims Management Service
Handles subscription state changes and JWT cache invalidation for webhook-driven system
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class SubscriptionClaimsService:
    """Service for managing subscription claims and token lifecycle"""

    @staticmethod
    def handle_subscription_change(subscription, change_type='updated'):
        """
        Handle subscription changes and invalidate related JWT caches

        Args:
            subscription: Subscription instance
            change_type: Type of change (created, updated, deleted, expired)
        """
        try:
            user_id = subscription.user.id

            # Invalidate subscription claims cache
            from authentication.services.jwt_subscription_service import JWTSubscriptionService
            JWTSubscriptionService.invalidate_subscription_cache(user_id)

            # Invalidate all user tokens to force refresh with new claims
            from authentication.services.jwt_security_service import JWTSecurityService
            JWTSecurityService.invalidate_all_user_tokens(
                user_id,
                reason=f"Subscription {change_type}"
            )

            logger.info(f"Subscription {change_type} for user {user_id} - JWT cache invalidated")

            return True

        except Exception as e:
            logger.error(f"Failed to handle subscription change: {str(e)}")
            return False

    @staticmethod
    def handle_plans_yaml_update():
        """
        Handle plans.yaml file updates
        Invalidates capabilities version cache so new version hash is generated

        Call this after running: python manage.py sync_plans
        """
        try:
            from authentication.services.jwt_subscription_service import JWTSubscriptionService

            # Invalidate capabilities version cache
            JWTSubscriptionService.invalidate_capabilities_version_cache()

            logger.info("Plans YAML updated - capabilities version cache invalidated")
            return True

        except Exception as e:
            logger.error(f"Failed to handle YAML update: {str(e)}")
            return False


# Signal handlers for automatic subscription change handling
@receiver(post_save, sender='subscription.Subscription')
def handle_subscription_save(sender, instance, created, **kwargs):
    """Handle subscription creation/updates"""
    change_type = 'created' if created else 'updated'
    SubscriptionClaimsService.handle_subscription_change(instance, change_type)


@receiver(post_delete, sender='subscription.Subscription')
def handle_subscription_delete(sender, instance, **kwargs):
    """Handle subscription deletion"""
    SubscriptionClaimsService.handle_subscription_change(instance, 'deleted')





