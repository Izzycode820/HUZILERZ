"""
Workspace event receivers - Handle workspace provisioning reactions
Listens to subscription events and provisions workspace capabilities
"""
from django.dispatch import receiver
from subscription.events import (
    subscription_activated,
    plan_change_applied,  # Used for upgrades/tier changes
    subscription_downgraded,
    subscription_expired,
    subscription_cancelled,
    trial_converted
)
from workspace.core.tasks.workspace_capabilities_provisioning import update_user_workspace_capabilities
import logging

logger = logging.getLogger(__name__)


# REMOVED: This receiver has been moved to hosting/receivers.py as part of a Celery chain
# to ensure proper ordering: HostingEnvironment creation BEFORE workspace capability updates.
# See: hosting/receivers.py:provision_hosting_environment_on_activation
#
# @receiver(subscription_activated)
# def provision_workspaces_on_activation(sender, subscription, **kwargs):
#     """Provision workspace capabilities when subscription activates"""
#     # This is now handled by Celery chain in hosting/receivers.py


@receiver(plan_change_applied)
def provision_workspaces_on_plan_change(sender, subscription, old_plan, new_plan, **kwargs):
    """Provision workspace capabilities when plan changes (upgrade/downgrade)"""
    logger.info(f"Workspace provisioning triggered: plan change {old_plan.tier} → {new_plan.tier}")

    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=new_plan.tier,
        event_type='plan_changed',
        metadata={'old_tier': old_plan.tier}
    )


@receiver(subscription_downgraded)
def provision_workspaces_on_downgrade(sender, subscription, old_plan, new_plan, **kwargs):
    """Provision workspace capabilities when subscription downgrades"""
    logger.info(f"Workspace provisioning triggered: downgrade {old_plan.tier} → {new_plan.tier}")

    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=new_plan.tier,
        event_type='downgraded',
        metadata={'old_tier': old_plan.tier}
    )


@receiver(subscription_expired)
def provision_workspaces_on_expiry(sender, subscription, **kwargs):
    """Provision workspace capabilities when subscription expires (downgrade to free)"""
    logger.info(f"Workspace provisioning triggered: subscription expired for {subscription.user.email}")

    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier='free',
        event_type='expired'
    )


@receiver(subscription_cancelled)
def provision_workspaces_on_cancellation(sender, subscription, **kwargs):
    """Provision workspace capabilities when subscription cancelled (downgrade to free)"""
    logger.info(f"Workspace provisioning triggered: subscription cancelled for {subscription.user.email}")

    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier='free',
        event_type='cancelled'
    )


@receiver(trial_converted)
def provision_workspaces_on_trial_conversion(sender, trial, subscription, **kwargs):
    """Provision workspace capabilities when trial converts to paid"""
    logger.info(f"Workspace provisioning triggered: trial converted to {subscription.plan.tier}")

    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=subscription.plan.tier,
        event_type='trial_converted'
    )
