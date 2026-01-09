# Core Workspace Signals - Handle user registration and workspace setup

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.apps import apps
import logging

from .services.workspace_service import WorkspaceService

User = get_user_model()
logger = logging.getLogger('workspace.core.signals')


@receiver(post_save, sender=User)
def create_default_workspace(sender, instance, created, **kwargs):
    """DISABLED: Create default workspace when user registers
    
    Users should manually create their workspace after choosing the type:
    - store: E-commerce with products, orders, transactions
    - blog: Content management with posts, categories, comments
    - services: Service booking with clients, appointments, invoices
    """
    # DISABLED - Manual workspace creation required
    pass


@receiver(post_save, sender='workspace_core.Workspace')
def setup_workspace_extensions(sender, instance, created, **kwargs):
    """Set up workspace extensions when workspace is created"""
    if created:
        try:
            WorkspaceService.setup_workspace_extensions(instance)
            logger.info(f"Extensions set up for workspace: {instance.name}")
        except Exception as e:
            logger.warning(f"Failed to set up extensions for workspace {instance.name}: {str(e)}")


@receiver(post_save, sender='workspace_core.Workspace')
def provision_workspace_roles_and_owner(sender, instance, created, **kwargs):
    """
    Auto-provision roles and create owner membership (SYNCHRONOUS)

    Following industry standard (Shopify/GitHub/Linear):
    - Workspace roles are created immediately (NOT async)
    - Owner membership is created immediately
    - Authorization is synchronous, never delayed

    This runs BEFORE async infrastructure provisioning
    Ensures owner has permissions from moment of creation

    CRITICAL: This is synchronous - must complete before request returns
    """
    if created:
        from workspace.core.services import RoleService

        try:
            # 1. Provision workspace roles (copies from system roles)
            workspace_roles = RoleService.provision_workspace_roles(instance)
            logger.info(
                f" Provisioned {len(workspace_roles)} roles for workspace: {instance.name}"
            )

            # 2. Create owner membership with Owner role
            owner_membership = RoleService.create_owner_membership(
                workspace=instance,
                owner_user=instance.owner
            )
            logger.info(
                f" Created owner membership for {instance.owner.email} in {instance.name}"
            )

        except Exception as e:
            # CRITICAL: Sync provisioning failed - queue async repair
            logger.error(
                f"✗ CRITICAL: Sync provisioning failed for workspace {instance.name}: {str(e)}"
            )

            # FALLBACK: Queue async repair task (catches 0.5% edge cases)
            from workspace.core.tasks.membership_provisioning_repair import repair_workspace_roles_and_owner

            repair_workspace_roles_and_owner.apply_async(
                args=[str(instance.id)],
                countdown=5  # Retry in 5 seconds
            )

            logger.info(
                f"⚙ Queued async repair task for workspace {instance.name} (will retry in 5s)"
            )


@receiver(post_save, sender='workspace_core.Workspace')
def provision_workspace_infrastructure(sender, instance, created, **kwargs):
    """
    Trigger async infrastructure provisioning when workspace is created

    Creates ProvisioningRecord and queues background tasks:
    1. Assign infrastructure (pool/bridge/silo based on tier)
    2. Create admin area defaults
    3. Create Puck workspace
    4. Finalize and activate workspace

    Workspace is immediately usable for admin panel while provisioning runs
    """
    if created:
        from workspace.core.models import ProvisioningRecord
        from workspace.core.tasks.workspace_hosting_provisioning import provision_workspace
        from workspace.core.tasks.workspace_capabilities_provisioning import provision_new_workspace

        try:
            # Create provisioning record for tracking
            provisioning_record = ProvisioningRecord.objects.create(
                workspace=instance,
                status='queued'
            )

            logger.info(
                f"Provisioning queued for workspace: {instance.name} "
                f"(provisioning_id: {provisioning_record.id})"
            )

            # Queue async provisioning tasks
            # 1. Hosting infrastructure provisioning
            provision_workspace.apply_async(
                args=[str(instance.id)],
                countdown=2  # Small delay to ensure transaction commits
            )

            # 2. Capability provisioning (loads limits from YAML based on user's tier)
            provision_new_workspace.delay(str(instance.id))

        except Exception as e:
            logger.error(
                f"Failed to queue provisioning for workspace {instance.name}: {str(e)}"
            )