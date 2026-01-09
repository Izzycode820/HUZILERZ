"""
Hosting Environment Provisioning Tasks
Async tasks for creating/managing HostingEnvironment per user
Separate from hosting_capabilities.py (which handles entitlement updates)
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from workspace.hosting.services.hosting_environment_service import HostingEnvironmentService
from subscription.models import SubscriptionEventLog
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    name='workspace_hosting.provision_hosting_environment'
)
def provision_hosting_environment(self, user_id, subscription_id):
    """
    Provision HostingEnvironment when subscription activates

    This creates the user-level hosting account that tracks:
    - Resource quotas (storage_gb, bandwidth, etc.)
    - Hosting capabilities (deployment_allowed, custom_domain, etc.)
    - Current usage (storage_used_gb, active_sites_count)

    Triggered by: subscription_activated signal
    Called from: hosting/receivers.py

    Args:
        user_id: UUID string of user
        subscription_id: UUID string of subscription

    Returns:
        dict: Provisioning result
    """
    from subscription.models import Subscription

    try:
        user = User.objects.get(id=user_id)
        subscription = Subscription.objects.get(id=subscription_id)

        logger.info(
            f"Provisioning HostingEnvironment for {user.email} "
            f"(Tier: {subscription.plan.tier})"
        )

        # Call service to create HostingEnvironment
        hosting_env, created = HostingEnvironmentService.create_for_user(user, subscription)

        # Log event
        try:
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='hosting_environment_provisioned',
                description=f'HostingEnvironment {"created" if created else "updated"}',
                metadata={
                    'hosting_env_id': str(hosting_env.id),
                    'tier': subscription.plan.tier,
                    'created': created,
                    'status': hosting_env.status,
                    'capabilities': hosting_env.capabilities
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log hosting provisioning event: {log_error}")

        logger.info(
            f"HostingEnvironment provisioned for {user.email} "
            f"(Created: {created}, ID: {hosting_env.id})"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'hosting_env_id': str(hosting_env.id),
            'created': created,
            'tier': subscription.plan.tier,
            'capabilities': hosting_env.capabilities
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for HostingEnvironment provisioning")
        raise

    except Subscription.DoesNotExist:
        logger.error(f"Subscription {subscription_id} not found")
        raise

    except Exception as exc:
        logger.error(
            f"Failed to provision HostingEnvironment for {user_id}: {exc}",
            exc_info=True
        )

        # Log failure
        try:
            user = User.objects.get(id=user_id)
            subscription = Subscription.objects.get(id=subscription_id)
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='hosting_environment_provisioning_failed',
                description=f'Failed to provision HostingEnvironment: {str(exc)}',
                metadata={
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log provisioning failure: {log_error}")

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries * 60, 3600))


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='workspace_hosting.update_hosting_environment_capabilities'
)
def update_hosting_environment_capabilities(self, user_id, new_tier, event_type):
    """
    Update HostingEnvironment capabilities when subscription tier changes

    Handles both scenarios gracefully:
    - Existing HostingEnvironment: Updates capabilities to new tier
    - Missing HostingEnvironment: Creates it first, then sets capabilities

    Called when:
    - Subscription activates (registration or upgrade)
    - User upgrades/downgrades subscription
    - Subscription expires (downgrade to free)

    Args:
        user_id: UUID string of user
        new_tier: New tier slug (free, beginner, pro, enterprise)
        event_type: Event that triggered this (activated, upgraded, downgraded, expired, etc.)

    Returns:
        dict: Update result
    """
    try:
        user = User.objects.get(id=user_id)

        logger.info(
            f"Updating HostingEnvironment capabilities for {user.email} "
            f"(New tier: {new_tier}, Event: {event_type})"
        )

        # Update capabilities to new tier
        # Note: HostingEnvironment MUST exist at this point (created via provision_hosting_environment task)
        # If missing, this will raise HostingEnvironment.DoesNotExist and trigger retry
        hosting_env = HostingEnvironmentService.update_capabilities(user, new_tier)

        logger.info(
            f"HostingEnvironment capabilities updated for {user.email} "
            f"(Tier: {new_tier}, Capabilities: {hosting_env.capabilities})"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'hosting_env_id': str(hosting_env.id),
            'new_tier': new_tier,
            'capabilities': hosting_env.capabilities
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        raise

    except Exception as exc:
        logger.error(
            f"Failed to update HostingEnvironment capabilities for {user_id}: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc)
