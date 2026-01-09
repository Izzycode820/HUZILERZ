"""
Hosting Environment Provisioning Service
Business logic for creating and managing HostingEnvironment per user
"""
import logging
from django.db import transaction
from workspace.hosting.models import HostingEnvironment
from subscription.services.capability_engine import CapabilityEngine

logger = logging.getLogger(__name__)


class HostingEnvironmentService:
    """
    Manage HostingEnvironment lifecycle

    HostingEnvironment = User-level hosting account (like Shopify's hosting environment)
    - ONE per user (OneToOne with User and Subscription)
    - Tracks resource quotas (storage, bandwidth, sites)
    - Stores hosting capabilities from subscription tier
    - Created when subscription activates (including free tier)

    This is pure business logic - no Celery, no signals, just the logic.
    Can be called from:
    - Async task (normal flow)
    - Admin panel (manual creation)
    - Management command (data migration)
    """

    # Hosting-specific capability keys from YAML
    HOSTING_CAPABILITY_KEYS = [
        'storage_gb',
        'custom_domain',
        'deployment_allowed',
    ]

    @classmethod
    def extract_hosting_capabilities(cls, all_capabilities):
        """
        Extract only hosting-related capabilities from full capability set

        Args:
            all_capabilities: Full capability dict from CapabilityEngine

        Returns:
            Dict containing only hosting-related capabilities
        """
        return {
            key: all_capabilities.get(key)
            for key in cls.HOSTING_CAPABILITY_KEYS
            if key in all_capabilities
        }

    @classmethod
    @transaction.atomic
    def create_for_user(cls, user, subscription):
        """
        Provision HostingEnvironment for user when subscription activates or changes

        Fully idempotent - handles ALL scenarios:
        - First activation (free tier signup) → Creates env with free capabilities
        - Paid activation (first payment) → Creates env with paid capabilities
        - Upgrade (free → pro) → Updates existing env with pro capabilities
        - Reactivation (cancelled → active) → Reactivates and updates capabilities
        - Concurrent calls → Django atomic transaction ensures last write wins

        Args:
            user: User instance
            subscription: Subscription instance

        Returns:
            tuple: (HostingEnvironment, created)
                - created=True if new environment was created
                - created=False if environment already existed and was updated
        """
        # Get EFFECTIVE tier based on subscription status
        # Only 'active' subscriptions get their plan tier - others get free tier
        # This prevents granting pro capabilities before payment completes
        if subscription.status == 'active':
            effective_tier = subscription.plan.tier
        else:
            # pending_payment, restricted, expired, cancelled, etc. = free tier
            effective_tier = 'free'
            logger.info(
                f"Subscription {subscription.id} is {subscription.status}, "
                f"using 'free' tier instead of '{subscription.plan.tier}'"
            )

        all_capabilities = CapabilityEngine.get_plan_capabilities(effective_tier)
        hosting_capabilities = cls.extract_hosting_capabilities(all_capabilities)

        # Idempotent - check if already exists
        try:
            hosting_env = HostingEnvironment.objects.select_for_update().get(user=user)
            logger.info(
                f"HostingEnvironment already exists for {user.email} "
                f"(ID: {hosting_env.id}, Status: {hosting_env.status})"
            )

            # Track what needs updating
            fields_to_update = []
            changes_made = []

            # Update capabilities if tier changed (handles upgrades/downgrades)
            old_capabilities = hosting_env.capabilities.copy() if hosting_env.capabilities else {}
            if old_capabilities != hosting_capabilities:
                hosting_env.capabilities = hosting_capabilities
                fields_to_update.append('capabilities')
                changes_made.append(
                    f"capabilities: {old_capabilities} → {hosting_capabilities}"
                )

            # Update subscription reference if changed
            if hosting_env.subscription_id != subscription.id:
                old_sub_id = hosting_env.subscription_id
                hosting_env.subscription = subscription
                fields_to_update.append('subscription')
                changes_made.append(
                    f"subscription: {old_sub_id} → {subscription.id}"
                )

            # Ensure status is active (handles reactivation)
            if hosting_env.status != 'active':
                old_status = hosting_env.status
                hosting_env.status = 'active'
                fields_to_update.append('status')
                changes_made.append(
                    f"status: {old_status} → active"
                )

            # Save if any changes were made
            if fields_to_update:
                fields_to_update.append('updated_at')
                hosting_env.save(update_fields=fields_to_update)
                logger.info(
                    f"Updated HostingEnvironment for {user.email} "
                    f"(Tier: {effective_tier}): {', '.join(changes_made)}"
                )
            else:
                logger.info(
                    f"HostingEnvironment for {user.email} already up-to-date "
                    f"(Tier: {effective_tier})"
                )

            return hosting_env, False

        except HostingEnvironment.DoesNotExist:
            pass

        # Create new HostingEnvironment
        logger.info(
            f"Creating HostingEnvironment for {user.email} "
            f"(Tier: {effective_tier}, Capabilities: {hosting_capabilities})"
        )

        hosting_env = HostingEnvironment.objects.create(
            subscription=subscription,
            user=user,
            status='active',
            capabilities=hosting_capabilities,
            storage_used_gb=0,
            bandwidth_used_gb=0,
            active_sites_count=0
        )

        logger.info(
            f" Created HostingEnvironment for {user.email} "
            f"(Tier: {effective_tier}, ID: {hosting_env.id})"
        )

        return hosting_env, True

    @classmethod
    @transaction.atomic
    def update_capabilities(cls, user, new_tier):
        """
        Update HostingEnvironment capabilities when subscription tier changes

        Defensive - creates environment if missing (shouldn't happen, but handles edge case)

        Called when:
        - User upgrades/downgrades subscription
        - Subscription expires (downgrade to free)
        - Reconciliation detects drift

        Args:
            user: User instance
            new_tier: New tier slug (free, beginner, pro, enterprise)

        Returns:
            HostingEnvironment with updated capabilities
        """
        # Get new capabilities from YAML
        all_capabilities = CapabilityEngine.get_plan_capabilities(new_tier)
        new_hosting_capabilities = cls.extract_hosting_capabilities(all_capabilities)

        try:
            hosting_env = HostingEnvironment.objects.select_for_update().get(user=user)

            # Update capabilities
            old_capabilities = hosting_env.capabilities.copy() if hosting_env.capabilities else {}
            if old_capabilities != new_hosting_capabilities:
                hosting_env.capabilities = new_hosting_capabilities
                hosting_env.save(update_fields=['capabilities', 'updated_at'])

                logger.info(
                    f"Updated HostingEnvironment capabilities for {user.email}: "
                    f"{old_capabilities} → {new_hosting_capabilities} (Tier: {new_tier})"
                )
            else:
                logger.info(
                    f"HostingEnvironment capabilities already match tier {new_tier} "
                    f"for {user.email}"
                )

            return hosting_env

        except HostingEnvironment.DoesNotExist:
            # Edge case: Environment was deleted or never created
            # This should NEVER happen in normal flow, but we handle it defensively
            logger.warning(
                f"HostingEnvironment missing for user {user.email} during capability update. "
                f"Creating with tier {new_tier} (THIS SHOULD NOT HAPPEN - investigate!)"
            )

            # Get user's subscription to create environment
            try:
                subscription = user.subscription
            except Exception as e:
                logger.error(
                    f"Cannot create HostingEnvironment for {user.email}: "
                    f"No subscription found. Error: {e}"
                )
                raise

            # Create environment using main creation method
            hosting_env, created = cls.create_for_user(user, subscription)

            if created:
                logger.warning(
                    f" Emergency-created HostingEnvironment for {user.email} "
                    f"(Tier: {new_tier}, ID: {hosting_env.id})"
                )

            return hosting_env

    @classmethod
    def get_or_create_for_user(cls, user):
        """
        Get existing HostingEnvironment or create if missing
        Fallback method for cases where environment should exist but doesn't

        Args:
            user: User instance

        Returns:
            tuple: (HostingEnvironment, created)
        """
        try:
            hosting_env = HostingEnvironment.objects.get(user=user)
            return hosting_env, False
        except HostingEnvironment.DoesNotExist:
            logger.warning(
                f"HostingEnvironment missing for user {user.email}. "
                f"Creating with subscription data."
            )

            # Get user's subscription
            try:
                subscription = user.subscription
            except Exception:
                logger.error(
                    f"No subscription found for user {user.email}. "
                    f"Cannot create HostingEnvironment."
                )
                raise

            return cls.create_for_user(user, subscription)
