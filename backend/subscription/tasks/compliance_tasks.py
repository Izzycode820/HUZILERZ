"""
Compliance Enforcement Tasks
Celery tasks for handling subscription downgrade compliance

Key tasks:
    - check_compliance_deadlines: Periodic task (hourly) to enforce after grace period
    - detect_and_handle_violations: Called when subscription downgrades
    - enforce_workspace_compliance: Single workspace enforcement
"""
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='subscription.detect_and_handle_violations'
)
def detect_and_handle_violations(
    self,
    user_id: str,
    old_tier: str,
    new_tier: str,
    grace_days: int = 7
):
    """
    Detect and handle violations after subscription downgrade.
    Called by receiver when subscription_downgraded signal is emitted.

    Args:
        user_id: UUID string of the user
        old_tier: Previous tier slug
        new_tier: New (lower) tier slug
        grace_days: Days before auto-enforcement

    Returns:
        Dict with violation detection and immediate enforcement results
    """
    try:
        from subscription.services.capability_engine import CapabilityEngine
        from subscription.services.compliance_service import ComplianceService
        from subscription.events import compliance_violation_detected

        user = User.objects.get(id=user_id)

        logger.info(
            f"Detecting violations for user {user.email} "
            f"downgrade: {old_tier} -> {new_tier}"
        )

        # Get capabilities for both tiers
        old_capabilities = CapabilityEngine.get_plan_capabilities(old_tier)
        new_capabilities = CapabilityEngine.get_plan_capabilities(new_tier)

        # Detect and handle violations
        violations, immediate_results = ComplianceService.handle_downgrade_violations(
            user=user,
            old_capabilities=old_capabilities,
            new_capabilities=new_capabilities,
            grace_days=grace_days
        )

        if violations:
            # Emit signal for other modules to react
            grace_deadline = timezone.now() + timezone.timedelta(days=grace_days)

            # Get user's primary workspace for signal
            from workspace.core.models import Workspace
            workspace = Workspace.objects.filter(owner=user, status='active').first()

            if workspace:
                compliance_violation_detected.send(
                    sender=ComplianceService,
                    user=user,
                    workspace=workspace,
                    violations=[
                        {
                            'type': v.violation_type,
                            'current': v.current_count,
                            'limit': v.new_limit,
                            'excess': v.excess_count,
                            'requires_grace': v.requires_grace
                        }
                        for v in violations
                    ],
                    grace_deadline=grace_deadline
                )

        logger.info(
            f"Violation detection complete for user {user.email}: "
            f"{len(violations)} violations found, "
            f"immediate enforcement: {list(immediate_results.keys())}"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'violations_count': len(violations),
            'immediate_enforcement': immediate_results
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for violation detection")
        raise

    except Exception as exc:
        logger.error(
            f"Error detecting violations for user {user_id}: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc)


@shared_task(name='subscription.check_compliance_deadlines')
def check_compliance_deadlines():
    """
    Periodic task to enforce violations after grace period expires.
    Should be scheduled to run hourly via Celery Beat.

    Finds all workspaces with:
        - plan_status = 'plan_violation'
        - compliance_deadline <= now

    And triggers auto-enforcement for each.
    """
    from workspace.core.models import Workspace
    from subscription.events import compliance_grace_expired

    logger.info("Running compliance deadline check")

    # Find workspaces with expired grace period
    # Use select_for_update with skip_locked to prevent race conditions
    expired_workspaces = Workspace.objects.filter(
        plan_status='plan_violation',
        compliance_deadline__lte=timezone.now()
    ).select_for_update(skip_locked=True)

    enforced_count = 0
    error_count = 0

    for workspace in expired_workspaces:
        try:
            # Queue individual enforcement (for better error isolation)
            enforce_workspace_compliance.delay(str(workspace.id))
            enforced_count += 1

            # Emit grace expired signal
            compliance_grace_expired.send(
                sender=Workspace,
                workspace=workspace,
                violations=workspace.violation_types
            )

        except Exception as e:
            logger.error(
                f"Error queuing enforcement for workspace {workspace.id}: {e}"
            )
            error_count += 1

    logger.info(
        f"Compliance deadline check complete: "
        f"{enforced_count} workspaces queued for enforcement, "
        f"{error_count} errors"
    )

    return {
        'workspaces_queued': enforced_count,
        'errors': error_count
    }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,  # 2 minutes between retries
    name='subscription.enforce_workspace_compliance'
)
def enforce_workspace_compliance(self, workspace_id: str):
    """
    Enforce compliance for a single workspace.
    Called by check_compliance_deadlines or directly when needed.

    Uses select_for_update to prevent race conditions.

    Args:
        workspace_id: UUID string of workspace to enforce
    """
    try:
        from workspace.core.models import Workspace
        from subscription.services.compliance_service import ComplianceService
        from subscription.events import compliance_auto_enforced

        with transaction.atomic():
            workspace = Workspace.objects.select_for_update().get(id=workspace_id)

            # Double-check enforcement is still needed
            if not workspace.is_enforcement_due:
                logger.info(
                    f"Workspace {workspace_id} no longer needs enforcement "
                    f"(status: {workspace.plan_status})"
                )
                return {
                    'success': True,
                    'workspace_id': workspace_id,
                    'enforced': False,
                    'reason': 'not_needed'
                }

            # Perform enforcement
            results = ComplianceService.enforce_grace_period_violations(workspace)

            # Emit signal
            compliance_auto_enforced.send(
                sender=ComplianceService,
                workspace=workspace,
                enforcement_results=results
            )

            logger.info(
                f"Auto-enforcement complete for workspace {workspace_id}: "
                f"{results}"
            )

            return {
                'success': True,
                'workspace_id': workspace_id,
                'enforced': True,
                'results': results
            }

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found for enforcement")
        return {
            'success': False,
            'workspace_id': workspace_id,
            'error': 'workspace_not_found'
        }

    except Exception as exc:
        logger.error(
            f"Error enforcing compliance for workspace {workspace_id}: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc)


@shared_task(name='subscription.check_violation_resolved')
def check_violation_resolved(workspace_id: str, violation_type: str):
    """
    Check if a specific violation is now resolved after user action.
    Called when user deletes/deactivates resources.

    Args:
        workspace_id: UUID string
        violation_type: Type of violation to check

    Returns:
        Whether the violation is resolved
    """
    try:
        from workspace.core.models import Workspace
        from subscription.services.compliance_service import ComplianceService
        from subscription.events import compliance_resolved

        workspace = Workspace.objects.get(id=workspace_id)

        is_resolved = ComplianceService.check_and_resolve_violation(
            workspace=workspace,
            violation_type=violation_type
        )

        if is_resolved:
            compliance_resolved.send(
                sender=ComplianceService,
                workspace=workspace,
                violation_type=violation_type,
                resolution_method='manual'
            )

        return {
            'workspace_id': workspace_id,
            'violation_type': violation_type,
            'resolved': is_resolved
        }

    except Exception as e:
        logger.error(
            f"Error checking violation resolution for workspace {workspace_id}: {e}"
        )
        return {
            'workspace_id': workspace_id,
            'violation_type': violation_type,
            'resolved': False,
            'error': str(e)
        }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='subscription.enforce_workspace_restriction'
)
def enforce_workspace_restriction(self, user_id: str, reason: str):
    """
    Enforce workspace restrictions when subscription enters restricted status.
    Called by subscription_suspended signal receiver.

    Actions:
        1. Set restricted_mode=True on ALL user's workspaces
        2. Apply Smart Selection: Keep oldest N workspaces accessible (based on plan limit)
        3. Mark excess workspaces as suspended_by_plan

    Thread-safe: Uses select_for_update to prevent race conditions

    Args:
        user_id: UUID string of user
        reason: Reason for restriction (grace_period_expired, payment_failed, admin_action)
    """
    try:
        from workspace.core.models import Workspace
        from subscription.services.capability_engine import CapabilityEngine

        user = User.objects.get(id=user_id)
        subscription = user.subscription

        logger.info(
            f"Enforcing workspace restriction for user {user.email} - "
            f"reason: {reason}, tier: {subscription.plan.tier}"
        )

        # Get plan's workspace limit
        capabilities = CapabilityEngine.get_plan_capabilities(subscription.plan.tier)
        workspace_limit = capabilities.get('workspace_limit', 1)

        with transaction.atomic():
            # Get all active workspaces (ordered by creation date - oldest first)
            workspaces = Workspace.objects.filter(
                owner=user,
                status='active'
            ).select_for_update().order_by('created_at')

            total_workspaces = workspaces.count()
            restricted_count = 0
            suspended_count = 0

            for idx, workspace in enumerate(workspaces):
                # Set restricted_mode on ALL workspaces
                workspace.restricted_mode = True
                workspace.restricted_at = timezone.now()
                workspace.restricted_reason = reason

                # Smart Selection: Keep oldest N workspaces accessible
                if idx < workspace_limit:
                    # This workspace stays active (user can VIEW it but not create new resources)
                    workspace.save(update_fields=[
                        'restricted_mode', 'restricted_at', 'restricted_reason', 'updated_at'
                    ])
                    restricted_count += 1
                else:
                    # Excess workspace - suspend it (user cannot even VIEW it)
                    workspace.status = 'suspended_by_plan'
                    workspace.save(update_fields=[
                        'restricted_mode', 'restricted_at', 'restricted_reason',
                        'status', 'updated_at'
                    ])
                    suspended_count += 1

        logger.info(
            f"Workspace restriction complete for user {user.email}: "
            f"{total_workspaces} total, {restricted_count} restricted (accessible), "
            f"{suspended_count} suspended (inaccessible)"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'total_workspaces': total_workspaces,
            'restricted_accessible': restricted_count,
            'suspended_inaccessible': suspended_count
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for workspace restriction")
        raise

    except Exception as exc:
        logger.error(
            f"Error enforcing workspace restriction for user {user_id}: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='subscription.clear_workspace_restriction'
)
def clear_workspace_restriction(self, user_id: str, new_tier: str):
    """
    Clear workspace restrictions when subscription is reactivated.
    Called by subscription_reactivated signal receiver.

    Actions:
        1. Clear restricted_mode from ALL user's workspaces
        2. Restore suspended_by_plan workspaces to active (if within new tier limit)

    Thread-safe: Uses select_for_update to prevent race conditions

    Args:
        user_id: UUID string of user
        new_tier: New tier after reactivation
    """
    try:
        from workspace.core.models import Workspace
        from subscription.services.capability_engine import CapabilityEngine

        user = User.objects.get(id=user_id)

        logger.info(
            f"Clearing workspace restriction for user {user.email} - "
            f"new tier: {new_tier}"
        )

        # Get new plan's workspace limit
        capabilities = CapabilityEngine.get_plan_capabilities(new_tier)
        workspace_limit = capabilities.get('workspace_limit', 1)

        with transaction.atomic():
            # Get all workspaces (both active and suspended_by_plan)
            workspaces = Workspace.objects.filter(
                owner=user,
                status__in=['active', 'suspended_by_plan']
            ).select_for_update().order_by('created_at')

            total_workspaces = workspaces.count()
            cleared_count = 0
            restored_count = 0

            for idx, workspace in enumerate(workspaces):
                # Clear restricted_mode from ALL workspaces
                workspace.restricted_mode = False
                workspace.restricted_at = None
                workspace.restricted_reason = ''

                # Restore suspended workspaces if within new limit
                if workspace.status == 'suspended_by_plan':
                    if idx < workspace_limit or workspace_limit == 0:  # 0 = unlimited
                        workspace.status = 'active'
                        restored_count += 1

                workspace.save(update_fields=[
                    'restricted_mode', 'restricted_at', 'restricted_reason',
                    'status', 'updated_at'
                ])
                cleared_count += 1

        logger.info(
            f"Workspace restriction cleared for user {user.email}: "
            f"{total_workspaces} total, {cleared_count} cleared, "
            f"{restored_count} restored from suspended"
        )

        return {
            'success': True,
            'user_id': str(user_id),
            'total_workspaces': total_workspaces,
            'cleared_count': cleared_count,
            'restored_count': restored_count
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for clearing workspace restriction")
        raise

    except Exception as exc:
        logger.error(
            f"Error clearing workspace restriction for user {user_id}: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc)
