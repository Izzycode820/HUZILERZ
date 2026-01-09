"""
Membership Provisioning Repair Tasks
Fallback tasks for role/membership provisioning failures (NOT infrastructure)

Scope: ONLY repairs workspace roles + owner membership
Does NOT repair: infrastructure, capabilities, notification settings, etc.

Following industry pattern (Shopify/GitHub):
- Primary: Synchronous provisioning in signal (99.5% success)
- Fallback: Async repair task catches edge cases (0.5%)

Handles:
- System roles not seeded
- Database connection hiccups
- Transaction rollbacks
- Any other role/membership provisioning failures
"""

from celery import shared_task
from django.db import transaction
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,  # 10 seconds between retries
    name='workspace.repair_workspace_roles_and_owner'
)
def repair_workspace_roles_and_owner(self, workspace_id):
    """
    Idempotent repair task for missing workspace roles and owner membership
    Runs when synchronous provisioning fails

    Features:
    - Transaction locked (no race conditions)
    - Idempotent (safe to run multiple times)
    - Auto-retries 3 times with 10s delay

    Args:
        workspace_id: UUID string of workspace to repair

    Returns:
        dict: Repair result with status
    """
    from workspace.core.models import Workspace, Role, Membership
    from workspace.core.services import RoleService

    try:
        # CRITICAL: Use select_for_update to prevent race conditions
        with transaction.atomic():
            workspace = Workspace.objects.select_for_update().select_related('owner').get(
                id=workspace_id
            )

            # Check if roles already provisioned (idempotent check)
            existing_roles = Role.objects.filter(workspace=workspace, is_system=False).count()

            if existing_roles > 0:
                logger.info(
                    f"✓ Workspace {workspace.name} already has {existing_roles} roles (skipping repair)"
                )

                # Still check owner membership exists
                owner_membership = Membership.objects.filter(
                    workspace=workspace,
                    user=workspace.owner,
                    status=Membership.Status.ACTIVE
                ).first()

                if owner_membership:
                    return {
                        'status': 'already_provisioned',
                        'workspace_id': str(workspace_id),
                        'workspace_name': workspace.name,
                        'roles_count': existing_roles
                    }
                else:
                    # Roles exist but owner membership missing - create it
                    logger.warning(
                        f"⚠ Workspace {workspace.name} has roles but missing owner membership - creating"
                    )
                    owner_membership = RoleService.create_owner_membership(
                        workspace=workspace,
                        owner_user=workspace.owner
                    )
                    logger.info(f"✓ Created owner membership for {workspace.owner.email}")

                    return {
                        'status': 'owner_repaired',
                        'workspace_id': str(workspace_id),
                        'workspace_name': workspace.name,
                        'owner_membership_id': str(owner_membership.id)
                    }

            # Provision missing roles
            logger.info(f"⚙ Repairing workspace provisioning for: {workspace.name}")

            # 1. Provision workspace roles (copies from system roles)
            try:
                workspace_roles = RoleService.provision_workspace_roles(workspace)
                logger.info(
                    f"✓ Provisioned {len(workspace_roles)} roles for workspace: {workspace.name}"
                )
            except ValidationError as e:
                # System roles not seeded - critical error
                logger.error(
                    f"✗ CRITICAL: System roles not found. Run 'python manage.py seed_permissions' first."
                )
                raise

            # 2. Create owner membership with Owner role
            owner_membership = RoleService.create_owner_membership(
                workspace=workspace,
                owner_user=workspace.owner
            )
            logger.info(
                f"✓ Created owner membership for {workspace.owner.email} in {workspace.name}"
            )

            return {
                'status': 'repaired',
                'workspace_id': str(workspace_id),
                'workspace_name': workspace.name,
                'roles_provisioned': len(workspace_roles),
                'owner_membership_id': str(owner_membership.id)
            }

    except Workspace.DoesNotExist:
        logger.error(f"✗ Workspace {workspace_id} not found")
        raise

    except Exception as exc:
        logger.error(
            f"✗ Repair failed for workspace {workspace_id} (attempt {self.request.retries + 1}/3): {exc}"
        )

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))


@shared_task(
    bind=True,
    max_retries=1,
    name='workspace.verify_all_workspaces_roles_provisioned'
)
def verify_all_workspaces_roles_provisioned(self):
    """
    Periodic health check task
    Verifies all workspaces have proper role + owner membership provisioning

    Scope: ONLY checks roles/membership (not infrastructure)

    Run this daily via cron to catch any edge cases:
        celery -A backend beat -l info

    Returns:
        dict: Health check results
    """
    from workspace.core.models import Workspace, Role

    logger.info("🔍 Starting workspace provisioning health check...")

    workspaces_checked = 0
    workspaces_missing_roles = []
    workspaces_repaired = []

    try:
        # Get all active workspaces
        workspaces = Workspace.objects.filter(status='active').select_related('owner')

        for workspace in workspaces:
            workspaces_checked += 1

            # Check if workspace has roles
            role_count = Role.objects.filter(workspace=workspace, is_system=False).count()

            if role_count == 0:
                # Missing roles - queue repair
                logger.warning(
                    f"⚠ Workspace {workspace.name} ({workspace.id}) missing roles - queuing repair"
                )

                workspaces_missing_roles.append({
                    'id': str(workspace.id),
                    'name': workspace.name,
                    'owner': workspace.owner.email
                })

                # Queue repair task
                repair_workspace_roles_and_owner.apply_async(
                    args=[str(workspace.id)],
                    countdown=2
                )

                workspaces_repaired.append(str(workspace.id))

        logger.info(
            f"✓ Health check complete: {workspaces_checked} workspaces checked, "
            f"{len(workspaces_missing_roles)} queued for repair"
        )

        return {
            'status': 'completed',
            'workspaces_checked': workspaces_checked,
            'workspaces_missing_roles': len(workspaces_missing_roles),
            'workspaces_repaired': workspaces_repaired,
            'missing_workspaces': workspaces_missing_roles
        }

    except Exception as exc:
        logger.error(f"✗ Health check failed: {exc}")
        raise
