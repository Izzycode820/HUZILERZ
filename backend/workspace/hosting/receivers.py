"""
Hosting event receivers - Handle hosting capability provisioning
Listens to subscription events and provisions hosting entitlements
Also handles storefront auto-provisioning (password protection, etc.)
"""
from django.dispatch import receiver
from django.db.models.signals import post_save
from subscription.events import (
    subscription_activated,
    plan_change_applied,  # Used for upgrades/tier changes
    subscription_downgraded,
    subscription_expired,
    subscription_cancelled,
    trial_converted
)
import logging

logger = logging.getLogger(__name__)


@receiver(subscription_activated)
def provision_hosting_environment_on_activation(sender, subscription, **kwargs):
    """
    Create HostingEnvironment when subscription activates (CRITICAL FIRST STEP)

    This runs for:
    - Free tier (signup) - creates HostingEnvironment with free capabilities
    - Paid tier (first payment or upgrade) - creates/updates HostingEnvironment
    - Trial activation - creates with trial tier capabilities

    Uses Celery chain to ensure workspace capabilities are updated AFTER HostingEnvironment exists.
    """
    logger.info(
        f"HostingEnvironment provisioning triggered: subscription activated "
        f"for {subscription.user.email} (Tier: {subscription.plan.tier})"
    )

    from workspace.hosting.tasks.hosting_environment_tasks import provision_hosting_environment
    from workspace.core.tasks.workspace_capabilities_provisioning import update_user_workspace_capabilities
    from celery import chain

    # CRITICAL: Use Celery chain to ensure proper ordering
    # Step 1: Create HostingEnvironment (blocks until complete)
    # Step 2: Update workspace capabilities (runs AFTER step 1 completes)
    chain(
        provision_hosting_environment.si(
            user_id=str(subscription.user.id),
            subscription_id=str(subscription.id)
        ),
        update_user_workspace_capabilities.si(
            user_id=str(subscription.user.id),
            new_tier=subscription.plan.tier,
            event_type='activated'
        )
    ).apply_async()


@receiver(plan_change_applied)
def update_hosting_on_plan_change(sender, subscription, old_plan, new_plan, **kwargs):
    """Update HostingEnvironment capabilities when plan changes (upgrade/downgrade)"""
    logger.info(
        f"HostingEnvironment update triggered: plan change "
        f"{old_plan.tier} → {new_plan.tier} for {subscription.user.email}"
    )

    from workspace.hosting.tasks.hosting_environment_tasks import update_hosting_environment_capabilities

    update_hosting_environment_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=new_plan.tier,
        event_type='plan_changed'
    )


@receiver(subscription_downgraded)
def update_hosting_on_downgrade(sender, subscription, old_plan, new_plan, **kwargs):
    """Update HostingEnvironment capabilities when subscription downgrades"""
    logger.info(
        f"HostingEnvironment update triggered: downgrade "
        f"{old_plan.tier} → {new_plan.tier} for {subscription.user.email}"
    )

    from workspace.hosting.tasks.hosting_environment_tasks import update_hosting_environment_capabilities

    update_hosting_environment_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=new_plan.tier,
        event_type='downgraded'
    )


@receiver(subscription_expired)
def update_hosting_on_expiry(sender, subscription, **kwargs):
    """Update HostingEnvironment capabilities when subscription expires (downgrade to free)"""
    logger.info(
        f"HostingEnvironment update triggered: subscription expired "
        f"for {subscription.user.email} (downgrade to free)"
    )

    from workspace.hosting.tasks.hosting_environment_tasks import update_hosting_environment_capabilities

    update_hosting_environment_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier='free',
        event_type='expired'
    )


@receiver(subscription_cancelled)
def update_hosting_on_cancellation(sender, subscription, **kwargs):
    """Update HostingEnvironment capabilities when subscription cancelled (downgrade to free)"""
    logger.info(
        f"HostingEnvironment update triggered: subscription cancelled "
        f"for {subscription.user.email} (downgrade to free)"
    )

    from workspace.hosting.tasks.hosting_environment_tasks import update_hosting_environment_capabilities

    update_hosting_environment_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier='free',
        event_type='cancelled'
    )


@receiver(trial_converted)
def update_hosting_on_trial_conversion(sender, trial, subscription, **kwargs):
    """Update HostingEnvironment capabilities when trial converts to paid"""
    logger.info(
        f"HostingEnvironment update triggered: trial converted to "
        f"{subscription.plan.tier} for {subscription.user.email}"
    )

    from workspace.hosting.tasks.hosting_environment_tasks import update_hosting_environment_capabilities

    update_hosting_environment_capabilities.delay(
        user_id=str(subscription.user.id),
        new_tier=subscription.plan.tier,
        event_type='trial_converted'
    )


# Storefront Auto-Provisioning (Concern #2)

@receiver(post_save, sender='workspace_hosting.DeployedSite')
def auto_provision_storefront_password(sender, instance, created, **kwargs):
    """
    Auto-enable password protection on new DeployedSite creation

    Shopify pattern: "Infrastructure live, business not live"
    - Prevents Google from indexing incomplete stores
    - Protects Cameroon market users who may not understand SEO/passwords
    - Default password shown in dashboard notification

    This runs when:
    - User creates workspace → DeployedSite auto-created
    - DeployedSite is created programmatically

    Security:
    - Password is hashed using Django's PBKDF2 SHA256
    - Simple format: "huzilerz-{year}-{random}"
    - User can change or disable via GraphQL mutation

    Implementation:
    - Queues async Celery task (non-blocking, retryable)
    - Uses transaction.on_commit() to run after DB transaction completes
    - Prevents blocking DeployedSite creation if provisioning fails
    """
    if not created:
        # Only run on creation, not updates
        return

    if instance.password_protection_enabled:
        # Already has password (manual creation), skip
        return

    # Queue async task AFTER transaction commits
    # This prevents blocking DeployedSite creation if provisioning fails
    from django.db import transaction

    def queue_password_provisioning():
        from workspace.hosting.tasks import provision_storefront_password_async
        provision_storefront_password_async.delay(str(instance.id))

    transaction.on_commit(queue_password_provisioning)

    logger.info(
        f"Queued storefront password provisioning for DeployedSite {instance.id} "
        f"(workspace: {instance.workspace.name})"
    )
