"""
Hosting Capability Provisioning Tasks
Handles hosting entitlement provisioning when subscription changes
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from subscription.services.capability_engine import CapabilityEngine
from subscription.models import SubscriptionEventLog
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

# Hosting-specific capability keys from YAML
HOSTING_CAPABILITY_KEYS = [
    'storage_gb',
    'custom_domain',
    'deployment_allowed',
]


def extract_hosting_capabilities(all_capabilities):
    """
    Extract only hosting-related capabilities from full capability set

    Args:
        all_capabilities: Full capability dict from CapabilityEngine

    Returns:
        Dict containing only hosting-related capabilities
    """
    return {
        key: all_capabilities.get(key)
        for key in HOSTING_CAPABILITY_KEYS
        if key in all_capabilities
    }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='workspace_hosting.update_hosting_capabilities'
)
def update_hosting_capabilities(self, user_id, new_tier, event_type, metadata=None):
    """
    Update hosting capabilities for a user when subscription changes
    Triggered by subscription lifecycle events

    Args:
        user_id: UUID string of user
        new_tier: New tier slug (free, beginner, pro, enterprise)
        event_type: Event that triggered this (activated, upgraded, downgraded, etc.)
        metadata: Optional additional context
    """
    try:
        # Get user
        user = User.objects.get(id=user_id)
        logger.info(f"Provisioning hosting capabilities for user {user.email} with tier {new_tier}")

        # Generate full capabilities from YAML
        all_capabilities = CapabilityEngine.get_plan_capabilities(new_tier)

        # Extract only hosting-related capabilities
        hosting_capabilities = extract_hosting_capabilities(all_capabilities)

        # Get user's hosting environment
        from workspace.hosting.models import HostingEnvironment
        try:
            hosting_env = HostingEnvironment.objects.get(user=user)

            # Update capabilities
            old_capabilities = hosting_env.capabilities.copy() if hosting_env.capabilities else {}
            hosting_env.capabilities = hosting_capabilities
            hosting_env.save(update_fields=['capabilities', 'updated_at'])

            logger.info(
                f"Updated hosting capabilities for user {user.email}: "
                f"{old_capabilities} → {hosting_capabilities}"
            )

            # Log provisioning success
            try:
                subscription = user.subscription
                SubscriptionEventLog.objects.create(
                    subscription=subscription,
                    user=user,
                    event_type='hosting_provisioning_success',
                    description=f'Provisioned hosting with {new_tier} capabilities',
                    metadata={
                        'event_type': event_type,
                        'new_tier': new_tier,
                        'old_capabilities': old_capabilities,
                        'new_capabilities': hosting_capabilities,
                        'additional_metadata': metadata or {}
                    }
                )
            except Exception as log_error:
                logger.warning(f"Failed to log hosting provisioning event: {log_error}")

            return {
                'success': True,
                'user_id': str(user_id),
                'tier': new_tier,
                'hosting_capabilities': hosting_capabilities
            }

        except HostingEnvironment.DoesNotExist:
            logger.warning(
                f"No hosting environment found for user {user.email}. "
                f"Will be provisioned when hosting is initialized."
            )
            return {
                'success': True,
                'user_id': str(user_id),
                'tier': new_tier,
                'message': 'No hosting environment yet - will provision on initialization'
            }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for hosting provisioning")
        raise

    except Exception as exc:
        logger.error(
            f"Error provisioning hosting capabilities for user {user_id}: {exc}",
            exc_info=True
        )

        # Log provisioning failure
        try:
            user = User.objects.get(id=user_id)
            subscription = user.subscription
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='hosting_provisioning_failed',
                description=f'Failed to provision hosting: {str(exc)}',
                metadata={
                    'event_type': event_type,
                    'new_tier': new_tier,
                    'error': str(exc),
                    'additional_metadata': metadata or {}
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log hosting provisioning failure: {log_error}")

        # Retry task
        raise self.retry(exc=exc)


@shared_task(name='workspace_hosting.provision_new_hosting_capabilities')
def provision_new_hosting_capabilities(user_id):
    """
    Provision hosting capabilities for a newly created hosting environment
    Called during hosting environment initialization

    Args:
        user_id: UUID string of user
    """
    try:
        user = User.objects.get(id=user_id)
        logger.info(f"Provisioning new hosting capabilities for user {user.email}")

        # Get user's current tier
        try:
            subscription = user.subscription
            tier = subscription.plan.tier
        except:
            # No subscription = free tier
            tier = 'free'

        # Generate full capabilities
        all_capabilities = CapabilityEngine.get_plan_capabilities(tier)

        # Extract only hosting-related capabilities
        hosting_capabilities = extract_hosting_capabilities(all_capabilities)

        # Get hosting environment
        from workspace.hosting.models import HostingEnvironment
        hosting_env = HostingEnvironment.objects.get(user=user)

        # Set hosting capabilities
        hosting_env.capabilities = hosting_capabilities
        hosting_env.save(update_fields=['capabilities', 'updated_at'])

        logger.info(
            f"Successfully provisioned new hosting with {tier} capabilities: "
            f"{hosting_capabilities}"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'tier': tier,
            'hosting_capabilities': hosting_capabilities
        }

    except Exception as exc:
        logger.error(
            f"Error provisioning new hosting capabilities for user {user_id}: {exc}",
            exc_info=True
        )
        raise
