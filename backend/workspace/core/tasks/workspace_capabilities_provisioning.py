"""
Workspace Provisioning Tasks
Handles workspace capability provisioning when subscription changes
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from subscription.services.capability_engine import CapabilityEngine
from subscription.models import SubscriptionEventLog
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='workspace.update_user_workspace_capabilities'
)
def update_user_workspace_capabilities(self, user_id, new_tier, event_type, metadata=None):
    """
    Update all workspaces for a user with new capabilities
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
        logger.info(f"Provisioning workspaces for user {user.email} with tier {new_tier}")

        # Generate new capabilities from YAML
        new_capabilities = CapabilityEngine.get_plan_capabilities(new_tier)

        # Get all active workspaces for this user
        from workspace.core.models import Workspace
        workspaces = Workspace.objects.filter(owner=user, status='active')

        updated_count = 0
        for workspace in workspaces:
            old_capabilities = workspace.capabilities.copy() if workspace.capabilities else {}

            # Update workspace capabilities
            workspace.capabilities = new_capabilities
            workspace.save(update_fields=['capabilities', 'updated_at'])

            updated_count += 1
            logger.info(
                f"Updated workspace {workspace.name} ({workspace.id}) "
                f"capabilities: {new_tier}"
            )

        # Log provisioning success
        try:
            subscription = user.subscription
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='provisioning_success',
                description=f'Provisioned {updated_count} workspace(s) with {new_tier} capabilities',
                metadata={
                    'event_type': event_type,
                    'new_tier': new_tier,
                    'workspaces_updated': updated_count,
                    'additional_metadata': metadata or {}
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log provisioning event: {log_error}")

        logger.info(
            f" Successfully provisioned {updated_count} workspace(s) "
            f"for user {user.email} with {new_tier} capabilities"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'tier': new_tier,
            'workspaces_updated': updated_count
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for provisioning")
        raise

    except Exception as exc:
        logger.error(
            f"Error provisioning workspaces for user {user_id}: {exc}",
            exc_info=True
        )

        # Log provisioning failure
        try:
            user = User.objects.get(id=user_id)
            subscription = user.subscription
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='provisioning_failed',
                description=f'Failed to provision workspaces: {str(exc)}',
                metadata={
                    'event_type': event_type,
                    'new_tier': new_tier,
                    'error': str(exc),
                    'additional_metadata': metadata or {}
                }
            )
        except Exception as log_error:
            logger.warning(f"Failed to log provisioning failure: {log_error}")

        # Retry task
        raise self.retry(exc=exc)


@shared_task(name='workspace.provision_new_workspace')
def provision_new_workspace(workspace_id):
    """
    Provision capabilities for a newly created workspace
    Called during workspace creation

    Args:
        workspace_id: UUID string of workspace
    """
    try:
        from workspace.core.models import Workspace

        workspace = Workspace.objects.get(id=workspace_id)
        user = workspace.owner

        logger.info(f"Provisioning new workspace {workspace.name} for user {user.email}")

        # Get user's current tier
        try:
            subscription = user.subscription
            tier = subscription.plan.tier
        except:
            # No subscription = free tier
            tier = 'free'

        # Generate capabilities
        capabilities = CapabilityEngine.get_plan_capabilities(tier)

        # Set workspace capabilities
        workspace.capabilities = capabilities
        workspace.save(update_fields=['capabilities', 'updated_at'])

        logger.info(
            f" Successfully provisioned workspace {workspace.name} "
            f"with {tier} capabilities"
        )

        return {
            'success': True,
            'workspace_id': str(workspace_id),
            'tier': tier
        }

    except Exception as exc:
        logger.error(
            f"Error provisioning new workspace {workspace_id}: {exc}",
            exc_info=True
        )
        raise
