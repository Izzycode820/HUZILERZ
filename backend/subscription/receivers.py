"""
Subscription event receivers - Handle provisioning when subscription changes
Listens to subscription lifecycle events and updates workspace capabilities
"""
from django.dispatch import receiver
from subscription.events import (
    subscription_activated,
    subscription_upgraded,
    subscription_downgraded,
    subscription_expired,
    subscription_cancelled,
    subscription_suspended,
    subscription_reactivated,
    trial_converted
)
from workspace.core.tasks.workspace_capabilities_provisioning import update_user_workspace_capabilities
import logging

logger = logging.getLogger(__name__)


@receiver(subscription_activated)
def handle_subscription_activated(sender, subscription, **kwargs):
    """
    Handle subscription activation
    Triggered when: New subscription activated or payment successful
    """
    logger.info(f"Subscription activated for user {subscription.user.email} - {subscription.plan.tier}")

    # Queue async task to update workspace capabilities
    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=subscription.plan.tier,
        event_type='activated'
    )


@receiver(subscription_upgraded)
def handle_subscription_upgraded(sender, subscription, old_plan, new_plan, **kwargs):
    """
    Handle subscription upgrade
    Triggered when: User upgrades to higher tier
    """
    logger.info(
        f"Subscription upgraded for user {subscription.user.email}: "
        f"{old_plan.tier} -> {new_plan.tier}"
    )

    # Queue async task to update workspace capabilities
    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=new_plan.tier,
        event_type='upgraded',
        metadata={'old_tier': old_plan.tier}
    )


@receiver(subscription_downgraded)
def handle_subscription_downgraded(sender, subscription, old_plan, new_plan, **kwargs):
    """
    Handle subscription downgrade
    Triggered when: User downgrades to lower tier or expires to free

    Flow:
        1. Update workspace capabilities (immediate)
        2. Detect and handle violations (async - may trigger grace period)
    """
    logger.info(
        f"Subscription downgraded for user {subscription.user.email}: "
        f"{old_plan.tier} -> {new_plan.tier}"
    )

    # Queue async task to update workspace capabilities
    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=new_plan.tier,
        event_type='downgraded',
        metadata={'old_tier': old_plan.tier}
    )

    # Queue compliance violation detection and handling
    # This detects if user exceeds new tier limits and handles accordingly:
    # - Immediate enforcement for domains/payments (no grace period)
    # - Grace period (configurable) for workspaces/products/staff/themes
    from subscription.tasks.compliance_tasks import detect_and_handle_violations
    from subscription.services.compliance_service import ComplianceService
    detect_and_handle_violations.delay(
        user_id=str(subscription.user.id),
        old_tier=old_plan.tier,
        new_tier=new_plan.tier,
        grace_days=ComplianceService.get_grace_period_days()
    )


@receiver(subscription_expired)
def handle_subscription_expired(sender, subscription, **kwargs):
    """
    Handle subscription expiration
    Triggered when: Grace period ends, auto-downgrade to free
    """
    logger.info(f"Subscription expired for user {subscription.user.email}")

    # Queue async task to downgrade to free tier capabilities
    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier='free',
        event_type='expired'
    )


@receiver(subscription_cancelled)
def handle_subscription_cancelled(sender, subscription, **kwargs):
    """
    Handle subscription cancellation
    Triggered when: User manually cancels subscription
    """
    logger.info(f"Subscription cancelled for user {subscription.user.email}")

    # Queue async task to downgrade to free tier capabilities
    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier='free',
        event_type='cancelled'
    )


@receiver(trial_converted)
def handle_trial_converted(sender, trial, subscription, **kwargs):
    """
    Handle trial conversion to paid subscription
    Triggered when: User converts trial to paid plan
    """
    logger.info(
        f"Trial converted for user {subscription.user.email}: "
        f"trial -> {subscription.plan.tier}"
    )

    # Queue async task to update workspace capabilities
    update_user_workspace_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=subscription.plan.tier,
        event_type='trial_converted'
    )


@receiver(subscription_suspended)
def handle_subscription_suspended(sender, subscription, reason, **kwargs):
    """
    Handle subscription suspension/restriction
    Triggered when: Grace period expires OR admin suspension

    This is CRITICAL for the restricted_mode flow:
        1. Set restricted_mode=True on ALL user's workspaces
        2. Apply Smart Selection: Keep oldest workspace(s) accessible,
           mark excess as suspended_by_plan

    Thread-safe: Uses Celery task for async processing
    """
    logger.info(
        f"Subscription suspended for user {subscription.user.email} - "
        f"reason: {reason}, plan: {subscription.plan.tier}"
    )

    # Queue async task to enforce workspace restrictions
    from subscription.tasks.compliance_tasks import enforce_workspace_restriction
    enforce_workspace_restriction.delay(
        user_id=str(subscription.user.id),
        reason=reason
    )


@receiver(subscription_reactivated)
def handle_subscription_reactivated(sender, subscription, **kwargs):
    """
    Handle subscription reactivation
    Triggered when: User renews subscription after restricted state

    Clears restricted_mode and restores excess workspaces
    """
    logger.info(
        f"Subscription reactivated for user {subscription.user.email} - "
        f"plan: {subscription.plan.tier}"
    )

    # Queue async task to clear workspace restrictions
    from subscription.tasks.compliance_tasks import clear_workspace_restriction
    clear_workspace_restriction.delay(
        user_id=str(subscription.user.id),
        new_tier=subscription.plan.tier
    )
