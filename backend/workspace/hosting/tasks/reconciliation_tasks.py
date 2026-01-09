"""
Capability Reconciliation Tasks
Periodic background jobs that detect and fix capability drift

Reconciliation Pattern (Stripe/Shopify best practice):
- Primary: Event-driven updates handle 99% of cases (immediate)
- Secondary: Reconciliation catches 1% edge cases (eventual consistency)
- Handles: Failed tasks, lost signals, manual DB edits, race conditions

Safety Features:
- Read-only detection mode (audit without changes)
- Auto-correction mode (fixes drift automatically)
- Comprehensive logging for audit trail
- Rate-limited to prevent DB overload
"""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from subscription.services.capability_engine import CapabilityEngine
from subscription.models import SubscriptionEventLog
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(name='workspace_hosting.reconcile_hosting_capabilities')
def reconcile_hosting_capabilities(auto_fix=True, batch_size=100):
    """
    Detect and fix hosting capability drift between subscription tier and HostingEnvironment

    CRITICAL: Uses EFFECTIVE tier based on subscription status, not just plan tier.
    - Only 'active' subscriptions get their plan tier capabilities
    - pending_payment, restricted, expired, cancelled = FREE tier capabilities

    Runs every 5-10 minutes to catch edge cases:
    - Celery task failures
    - Lost signals (message broker issues)
    - Manual DB edits
    - Race conditions
    - User tampering (security)
    - PREMATURE PROVISIONING (subscription not active yet)

    Args:
        auto_fix: If True, automatically corrects drift. If False, only logs issues.
        batch_size: Number of users to process per run (rate limiting)

    Returns:
        dict: Reconciliation results
    """
    try:
        from workspace.hosting.models import HostingEnvironment
        from workspace.hosting.services.hosting_environment_service import HostingEnvironmentService

        logger.info(f"Starting hosting capability reconciliation (auto_fix={auto_fix}, batch_size={batch_size})")

        drift_detected = []
        drift_fixed = []
        errors = []

        # CRITICAL FIX: Check ALL hosting environments, not just those with active subscriptions
        # This catches users with pending_payment/restricted/etc. who might have wrong capabilities
        hosting_envs = HostingEnvironment.objects.select_related(
            'user',
            'subscription',
            'subscription__plan'
        ).filter(
            status='active'  # Only check active hosting environments
        )[:batch_size]

        for hosting_env in hosting_envs:
            try:
                user = hosting_env.user
                subscription = hosting_env.subscription

                if not subscription:
                    # No subscription - should have free tier
                    effective_tier = 'free'
                    plan_tier = None
                    subscription_status = 'missing'
                elif subscription.status == 'active':
                    # Active subscription - use plan tier
                    effective_tier = subscription.plan.tier
                    plan_tier = subscription.plan.tier
                    subscription_status = 'active'
                else:
                    # Non-active subscription - MUST have free tier
                    # This catches pending_payment, restricted, expired, cancelled, failed
                    effective_tier = 'free'
                    plan_tier = subscription.plan.tier if subscription.plan else None
                    subscription_status = subscription.status
                    logger.info(
                        f"[EFFECTIVE TIER CHECK] User {user.email}: "
                        f"plan={plan_tier}, status={subscription_status} -> effective_tier=free"
                    )

                # Get expected capabilities for EFFECTIVE tier (not plan tier)
                expected_capabilities = CapabilityEngine.get_plan_capabilities(effective_tier)
                expected_hosting_caps = HostingEnvironmentService.extract_hosting_capabilities(expected_capabilities)

                # Get current capabilities from DB
                current_caps = hosting_env.capabilities or {}

                # Detect drift
                if current_caps != expected_hosting_caps:
                    drift_info = {
                        'user_id': str(user.id),
                        'user_email': user.email,
                        'plan_tier': plan_tier,
                        'subscription_status': subscription_status,
                        'effective_tier': effective_tier,
                        'current_capabilities': current_caps,
                        'expected_capabilities': expected_hosting_caps,
                        'hosting_env_id': str(hosting_env.id),
                        'severity': 'HIGH' if effective_tier == 'free' and current_caps.get('custom_domain', False) else 'MEDIUM',
                    }
                    drift_detected.append(drift_info)

                    logger.warning(
                        f"[DRIFT DETECTED] HostingEnvironment capability mismatch for {user.email}: "
                        f"Current: {current_caps}, Expected (effective_tier={effective_tier}): {expected_hosting_caps} "
                        f"[plan={plan_tier}, status={subscription_status}]"
                    )

                    # Auto-fix if enabled
                    if auto_fix:
                        try:
                            # Update capabilities using service method (atomic, logged)
                            HostingEnvironmentService.update_capabilities(user, effective_tier)

                            drift_fixed.append(drift_info)

                            # Log to subscription event log for audit (if subscription exists)
                            if subscription:
                                SubscriptionEventLog.objects.create(
                                    subscription=subscription,
                                    user=user,
                                    event_type='capability_drift_fixed',
                                    description=f'Reconciliation auto-fixed capability drift: {plan_tier}/{subscription_status} -> {effective_tier}',
                                    metadata={
                                        'old_capabilities': current_caps,
                                        'new_capabilities': expected_hosting_caps,
                                        'plan_tier': plan_tier,
                                        'subscription_status': subscription_status,
                                        'effective_tier': effective_tier,
                                        'fixed_by': 'reconciliation_task',
                                        'fixed_at': timezone.now().isoformat(),
                                    }
                                )

                            logger.info(
                                f"[DRIFT FIXED] Updated HostingEnvironment capabilities for {user.email} "
                                f"to match effective_tier={effective_tier} (plan={plan_tier}, status={subscription_status})"
                            )
                        except Exception as fix_error:
                            errors.append({
                                'user_email': user.email,
                                'error': str(fix_error),
                                'drift_info': drift_info,
                            })
                            logger.error(
                                f"[FIX FAILED] Failed to fix drift for {user.email}: {fix_error}",
                                exc_info=True
                            )

            except Exception as e:
                errors.append({
                    'hosting_env_id': str(hosting_env.id),
                    'error': str(e),
                })
                logger.error(
                    f"[RECONCILIATION ERROR] Error processing HostingEnvironment {hosting_env.id}: {e}",
                    exc_info=True
                )

        # Summary
        result = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'processed_count': len(hosting_envs),
            'drift_detected_count': len(drift_detected),
            'drift_fixed_count': len(drift_fixed),
            'error_count': len(errors),
            'auto_fix_enabled': auto_fix,
            'drift_detected': drift_detected,
            'errors': errors,
        }

        logger.info(
            f" Hosting capability reconciliation complete: "
            f"{len(hosting_envs)} processed, {len(drift_detected)} drift detected, "
            f"{len(drift_fixed)} fixed, {len(errors)} errors"
        )

        return result

    except Exception as e:
        logger.error(f"[RECONCILIATION FAILED] Fatal error in reconciliation task: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='workspace_core.reconcile_workspace_capabilities')
def reconcile_workspace_capabilities(auto_fix=True, batch_size=100):
    """
    Detect and fix workspace capability drift between subscription tier and Workspace

    CRITICAL: Uses EFFECTIVE tier based on subscription status, not just plan tier.
    - Only 'active' subscriptions get their plan tier capabilities
    - pending_payment, restricted, expired, cancelled = FREE tier capabilities

    Companion task to reconcile_hosting_capabilities - handles workspace_core module

    Args:
        auto_fix: If True, automatically corrects drift. If False, only logs issues.
        batch_size: Number of workspaces to process per run (rate limiting)

    Returns:
        dict: Reconciliation results
    """
    try:
        from workspace.core.models import Workspace

        logger.info(f"Starting workspace capability reconciliation (auto_fix={auto_fix}, batch_size={batch_size})")

        drift_detected = []
        drift_fixed = []
        errors = []

        # CRITICAL FIX: Check ALL active workspaces, not just those with active subscriptions
        # This catches users with pending_payment/restricted/etc. who might have wrong capabilities
        workspaces = Workspace.objects.select_related(
            'owner',
            'owner__subscription',
            'owner__subscription__plan'
        ).filter(
            status='active'  # Only check active workspaces
        )[:batch_size]

        for workspace in workspaces:
            try:
                user = workspace.owner
                subscription = getattr(user, 'subscription', None)

                if not subscription:
                    # No subscription - should have free tier
                    effective_tier = 'free'
                    plan_tier = None
                    subscription_status = 'missing'
                elif subscription.status == 'active':
                    # Active subscription - use plan tier
                    effective_tier = subscription.plan.tier
                    plan_tier = subscription.plan.tier
                    subscription_status = 'active'
                else:
                    # Non-active subscription - MUST have free tier
                    # This catches pending_payment, restricted, expired, cancelled, failed
                    effective_tier = 'free'
                    plan_tier = subscription.plan.tier if subscription.plan else None
                    subscription_status = subscription.status
                    logger.info(
                        f"[EFFECTIVE TIER CHECK] Workspace {workspace.name} ({user.email}): "
                        f"plan={plan_tier}, status={subscription_status} -> effective_tier=free"
                    )

                # Get expected capabilities for EFFECTIVE tier (not plan tier)
                expected_capabilities = CapabilityEngine.get_plan_capabilities(effective_tier)

                # Get current capabilities from DB
                current_caps = workspace.capabilities or {}

                # Detect drift
                if current_caps != expected_capabilities:
                    drift_info = {
                        'user_id': str(user.id),
                        'user_email': user.email,
                        'workspace_id': str(workspace.id),
                        'workspace_name': workspace.name,
                        'plan_tier': plan_tier,
                        'subscription_status': subscription_status,
                        'effective_tier': effective_tier,
                        'current_capabilities': current_caps,
                        'expected_capabilities': expected_capabilities,
                        'severity': 'HIGH' if effective_tier == 'free' and current_caps.get('max_products', 0) > 15 else 'MEDIUM',
                    }
                    drift_detected.append(drift_info)

                    logger.warning(
                        f"[DRIFT DETECTED] Workspace capability mismatch for {workspace.name} ({user.email}): "
                        f"Current: {current_caps}, Expected (effective_tier={effective_tier}): {expected_capabilities} "
                        f"[plan={plan_tier}, status={subscription_status}]"
                    )

                    # Auto-fix if enabled
                    if auto_fix:
                        try:
                            # Update workspace capabilities directly (atomic)
                            old_caps = workspace.capabilities.copy() if workspace.capabilities else {}
                            workspace.capabilities = expected_capabilities
                            workspace.save(update_fields=['capabilities', 'updated_at'])

                            drift_fixed.append(drift_info)

                            # Log to subscription event log for audit (if subscription exists)
                            if subscription:
                                SubscriptionEventLog.objects.create(
                                    subscription=subscription,
                                    user=user,
                                    event_type='workspace_capability_drift_fixed',
                                    description=f'Reconciliation auto-fixed workspace capability drift: {plan_tier}/{subscription_status} -> {effective_tier}',
                                    metadata={
                                        'workspace_id': str(workspace.id),
                                        'workspace_name': workspace.name,
                                        'old_capabilities': old_caps,
                                        'new_capabilities': expected_capabilities,
                                        'plan_tier': plan_tier,
                                        'subscription_status': subscription_status,
                                        'effective_tier': effective_tier,
                                        'fixed_by': 'reconciliation_task',
                                        'fixed_at': timezone.now().isoformat(),
                                    }
                                )

                            logger.info(
                                f"[DRIFT FIXED] Updated Workspace capabilities for {workspace.name} "
                                f"({user.email}) to match effective_tier={effective_tier} (plan={plan_tier}, status={subscription_status})"
                            )
                        except Exception as fix_error:
                            errors.append({
                                'workspace_name': workspace.name,
                                'user_email': user.email,
                                'error': str(fix_error),
                                'drift_info': drift_info,
                            })
                            logger.error(
                                f"[FIX FAILED] Failed to fix drift for workspace {workspace.name}: {fix_error}",
                                exc_info=True
                            )

            except Exception as e:
                errors.append({
                    'workspace_id': str(workspace.id),
                    'error': str(e),
                })
                logger.error(
                    f"[RECONCILIATION ERROR] Error processing Workspace {workspace.id}: {e}",
                    exc_info=True
                )

        # Summary
        result = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'processed_count': len(workspaces),
            'drift_detected_count': len(drift_detected),
            'drift_fixed_count': len(drift_fixed),
            'error_count': len(errors),
            'auto_fix_enabled': auto_fix,
            'drift_detected': drift_detected,
            'errors': errors,
        }

        logger.info(
            f" Workspace capability reconciliation complete: "
            f"{len(workspaces)} processed, {len(drift_detected)} drift detected, "
            f"{len(drift_fixed)} fixed, {len(errors)} errors"
        )

        return result

    except Exception as e:
        logger.error(f"[RECONCILIATION FAILED] Fatal error in workspace reconciliation task: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='workspace.reconcile_all_capabilities')
def reconcile_all_capabilities(auto_fix=True, batch_size=100):
    """
    Master reconciliation task - runs both hosting and workspace reconciliation

    Schedule this task to run periodically (every 5-10 minutes) via Celery Beat

    Args:
        auto_fix: If True, automatically corrects drift. If False, only audits.
        batch_size: Number of records to process per module

    Returns:
        dict: Combined reconciliation results
    """
    logger.info(f"Starting full capability reconciliation (auto_fix={auto_fix})")

    # Run both reconciliation tasks
    hosting_result = reconcile_hosting_capabilities(auto_fix=auto_fix, batch_size=batch_size)
    workspace_result = reconcile_workspace_capabilities(auto_fix=auto_fix, batch_size=batch_size)

    # Combine results
    total_drift_detected = hosting_result.get('drift_detected_count', 0) + workspace_result.get('drift_detected_count', 0)
    total_drift_fixed = hosting_result.get('drift_fixed_count', 0) + workspace_result.get('drift_fixed_count', 0)
    total_errors = hosting_result.get('error_count', 0) + workspace_result.get('error_count', 0)

    result = {
        'success': True,
        'timestamp': timezone.now().isoformat(),
        'auto_fix_enabled': auto_fix,
        'total_drift_detected': total_drift_detected,
        'total_drift_fixed': total_drift_fixed,
        'total_errors': total_errors,
        'hosting_reconciliation': hosting_result,
        'workspace_reconciliation': workspace_result,
    }

    logger.info(
        f" Full reconciliation complete: "
        f"{total_drift_detected} total drift detected, "
        f"{total_drift_fixed} total fixed, {total_errors} total errors"
    )

    return result
