"""
Compliance Service - Downgrade Flow Engine
Detects violations and orchestrates enforcement when subscription downgrades

Architecture per downgrade guide:
    - SubscriptionService: decides entitlements (what user CAN have)
    - ComplianceService: decides compliance (does user EXCEED limits?)
    - Feature modules: enforce locally (block actions if not compliant)

Key principles:
    - Entitlements != Data Ownership: Downgrades never delete data automatically
    - Workspace-level subscription is authoritative
    - Compliance is explicit: No silent auto-fixes except final fallback
"""
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@dataclass
class ViolationRecord:
    """
    Represents a single capability violation after downgrade.
    Immutable record for audit trail.
    """
    violation_type: str      # e.g., 'products', 'staff', 'workspaces'
    capability_key: str      # e.g., 'product_limit', 'staff_limit'
    current_count: int       # What user currently has
    new_limit: int           # What new plan allows (0 = unlimited)
    excess_count: int        # How many over the limit
    requires_grace: bool     # False for domains (immediate), True for others


class ComplianceService:
    """
    Compliance Engine - Detects violations and orchestrates enforcement

    Separation of concerns:
        - SubscriptionService: decides entitlements (what user CAN have)
        - ComplianceService: decides compliance (does user EXCEED limits?)
        - Feature modules: enforce locally (block actions if not compliant)

    Thread-safety: All database operations use select_for_update where needed
    """

    # Violation types and their grace period behavior
    # Per downgrade guide: domains unbind immediately, others get grace period
    VIOLATION_CONFIG = {
        'workspaces': {'capability_key': 'workspace_limit', 'grace_required': True},
        'products': {'capability_key': 'product_limit', 'grace_required': True},
        'staff': {'capability_key': 'staff_limit', 'grace_required': True},
        'themes': {'capability_key': 'theme_library_limit', 'grace_required': True},
        'domains': {'capability_key': 'custom_domain', 'grace_required': False},
        'payment': {'capability_key': 'payment_processing', 'grace_required': False},
    }

    @classmethod
    def get_grace_period_days(cls) -> int:
        """
        Get grace period from Django settings with fallback.
        Configure via: COMPLIANCE_GRACE_PERIOD_DAYS = 7
        """
        from django.conf import settings
        return getattr(settings, 'COMPLIANCE_GRACE_PERIOD_DAYS', 7)

    # For backward compat - use get_grace_period_days() instead
    DEFAULT_GRACE_DAYS = 7

    @classmethod
    def detect_violations(
        cls,
        user,
        old_capabilities: Dict[str, Any],
        new_capabilities: Dict[str, Any]
    ) -> List[ViolationRecord]:
        """
        Compare old vs new capabilities, detect which resources exceed new limits.
        Called when subscription downgrades.

        Args:
            user: User instance
            old_capabilities: Capabilities before downgrade
            new_capabilities: Capabilities after downgrade

        Returns:
            List of ViolationRecord for each exceeded limit
        """
        violations = []

        # Check workspace count
        workspace_violation = cls._check_workspace_violation(user, new_capabilities)
        if workspace_violation:
            violations.append(workspace_violation)

        # Check product count (across all workspaces)
        product_violation = cls._check_product_violation(user, new_capabilities)
        if product_violation:
            violations.append(product_violation)

        # Check staff count (across all workspaces)
        staff_violation = cls._check_staff_violation(user, new_capabilities)
        if staff_violation:
            violations.append(staff_violation)

        # Check theme library count
        theme_violation = cls._check_theme_violation(user, new_capabilities)
        if theme_violation:
            violations.append(theme_violation)

        # Check custom domain (boolean capability)
        domain_violation = cls._check_domain_violation(user, old_capabilities, new_capabilities)
        if domain_violation:
            violations.append(domain_violation)

        # Check payment processing (boolean capability)
        payment_violation = cls._check_payment_violation(user, old_capabilities, new_capabilities)
        if payment_violation:
            violations.append(payment_violation)

        logger.info(
            f"Detected {len(violations)} violations for user {user.email}: "
            f"{[v.violation_type for v in violations]}"
        )

        return violations

    @classmethod
    def _check_workspace_violation(cls, user, new_capabilities: Dict) -> Optional[ViolationRecord]:
        """Check if user's workspace count exceeds new limit"""
        from workspace.core.models import Workspace

        new_limit = new_capabilities.get('workspace_limit', 1)

        # 0 means unlimited
        if new_limit == 0:
            return None

        current_count = Workspace.objects.filter(
            owner=user,
            status__in=['active', 'provisioning']
        ).count()

        if current_count > new_limit:
            return ViolationRecord(
                violation_type='workspaces',
                capability_key='workspace_limit',
                current_count=current_count,
                new_limit=new_limit,
                excess_count=current_count - new_limit,
                requires_grace=True
            )
        return None

    @classmethod
    def _check_product_violation(cls, user, new_capabilities: Dict) -> Optional[ViolationRecord]:
        """Check if user's total product count exceeds new limit"""
        from workspace.store.models import Product
        from workspace.core.models import Workspace

        new_limit = new_capabilities.get('product_limit', 20)

        # 0 means unlimited
        if new_limit == 0:
            return None

        # Count products across all user's active workspaces
        # Only count products that are both user-active AND plan-active
        user_workspaces = Workspace.objects.filter(
            owner=user,
            status='active'
        ).values_list('id', flat=True)

        current_count = Product.objects.filter(
            workspace_id__in=user_workspaces,
            is_active=True,
            active_by_plan=True  # Only count plan-active products
        ).count()

        if current_count > new_limit:
            return ViolationRecord(
                violation_type='products',
                capability_key='product_limit',
                current_count=current_count,
                new_limit=new_limit,
                excess_count=current_count - new_limit,
                requires_grace=True
            )
        return None

    @classmethod
    def _check_staff_violation(cls, user, new_capabilities: Dict) -> Optional[ViolationRecord]:
        """Check if user's total staff count exceeds new limit"""
        from workspace.core.models import Workspace, Membership

        new_limit = new_capabilities.get('staff_limit', 1)

        # 0 means unlimited
        if new_limit == 0:
            return None

        # Count active staff across all user's workspaces (excluding owner)
        user_workspaces = Workspace.objects.filter(
            owner=user,
            status='active'
        )

        current_count = 0
        for workspace in user_workspaces:
            # Count active members excluding owner
            staff_count = Membership.objects.filter(
                workspace=workspace,
                status=Membership.Status.ACTIVE
            ).exclude(user=user).count()
            current_count += staff_count

        if current_count > new_limit:
            return ViolationRecord(
                violation_type='staff',
                capability_key='staff_limit',
                current_count=current_count,
                new_limit=new_limit,
                excess_count=current_count - new_limit,
                requires_grace=True
            )
        return None

    @classmethod
    def _check_theme_violation(cls, user, new_capabilities: Dict) -> Optional[ViolationRecord]:
        """Check if user's theme library count exceeds new limit"""
        try:
            from theme.models import ThemeInstance
            from workspace.core.models import Workspace

            new_limit = new_capabilities.get('theme_library_limit', 1)

            # 0 means unlimited
            if new_limit == 0:
                return None

            # Count themes across all user's workspaces
            user_workspaces = Workspace.objects.filter(
                owner=user,
                status='active'
            ).values_list('id', flat=True)

            current_count = ThemeInstance.objects.filter(
                workspace_id__in=user_workspaces,
                status__in=['active', 'draft']
            ).count()

            if current_count > new_limit:
                return ViolationRecord(
                    violation_type='themes',
                    capability_key='theme_library_limit',
                    current_count=current_count,
                    new_limit=new_limit,
                    excess_count=current_count - new_limit,
                    requires_grace=True
                )
        except ImportError:
            # Theme module not installed
            pass
        return None

    @classmethod
    def _check_domain_violation(
        cls,
        user,
        old_capabilities: Dict,
        new_capabilities: Dict
    ) -> Optional[ViolationRecord]:
        """
        Check domain violations - handles TWO cases:
        1. Boolean: Pro/Enterprise -> Free/Beginner (has domain -> no domain)
        2. Count: Enterprise -> Pro (5 domains -> 2 domains)

        IMMEDIATE enforcement - no grace period per downgrade guide.
        """
        old_allowed = old_capabilities.get('custom_domain', False)
        new_allowed = new_capabilities.get('custom_domain', False)

        try:
            from workspace.hosting.models import CustomDomain
            from workspace.core.models import Workspace

            user_workspaces = Workspace.objects.filter(
                owner=user,
                status='active'
            ).values_list('id', flat=True)

            active_domains = CustomDomain.objects.filter(
                workspace_id__in=user_workspaces,
                status__in=['verified', 'pending']
            ).count()

            if active_domains == 0:
                return None  # No domains, no violation

            # Case 1: Boolean violation (allowed -> not allowed)
            if old_allowed and not new_allowed:
                return ViolationRecord(
                    violation_type='domains',
                    capability_key='custom_domain',
                    current_count=active_domains,
                    new_limit=0,
                    excess_count=active_domains,
                    requires_grace=False
                )

            # Case 2: Count violation (both allowed, but limit decreased)
            # custom_domain can be: True (unlimited), False, or int (limit)
            old_limit = old_allowed if isinstance(old_allowed, int) else (0 if old_allowed else 0)
            new_limit = new_allowed if isinstance(new_allowed, int) else (0 if new_allowed else 0)

            # 0 means unlimited, so only check if new_limit is a positive number
            if isinstance(new_allowed, int) and new_allowed > 0:
                if active_domains > new_allowed:
                    return ViolationRecord(
                        violation_type='domains',
                        capability_key='custom_domain',
                        current_count=active_domains,
                        new_limit=new_allowed,
                        excess_count=active_domains - new_allowed,
                        requires_grace=False  # Domains always immediate
                    )

        except ImportError:
                pass
        return None

    @classmethod
    def _check_payment_violation(
        cls,
        user,
        old_capabilities: Dict,
        new_capabilities: Dict
    ) -> Optional[ViolationRecord]:
        """
        Check if user has payment methods but new plan doesn't allow them.
        IMMEDIATE enforcement - payment is a premium feature.
        """
        old_allowed = old_capabilities.get('payment_processing', False)
        new_allowed = new_capabilities.get('payment_processing', False)

        # Only a violation if going from allowed to not allowed
        if old_allowed and not new_allowed:
            try:
                from payments.models import MerchantPaymentMethod
                from workspace.core.models import Workspace

                user_workspaces = Workspace.objects.filter(
                    owner=user,
                    status='active'
                ).values_list('id', flat=True)

                active_methods = MerchantPaymentMethod.objects.filter(
                    workspace_id__in=user_workspaces,
                    enabled=True
                ).count()

                if active_methods > 0:
                    return ViolationRecord(
                        violation_type='payment',
                        capability_key='payment_processing',
                        current_count=active_methods,
                        new_limit=0,
                        excess_count=active_methods,
                        requires_grace=False  # Immediate enforcement
                    )
            except ImportError:
                pass
        return None

    @classmethod
    @transaction.atomic
    def handle_downgrade_violations(
        cls,
        user,
        old_capabilities: Dict[str, Any],
        new_capabilities: Dict[str, Any],
        grace_days: int = DEFAULT_GRACE_DAYS
    ) -> Tuple[List[ViolationRecord], Dict[str, Any]]:
        """
        Main entry point: Detect violations and handle them appropriately.
        Called by receiver when subscription_downgraded signal is emitted.

        Process:
            1. Detect all violations
            2. Immediately enforce non-grace violations (domains, payment)
            3. Mark grace-period violations on workspaces

        Args:
            user: User instance
            old_capabilities: Pre-downgrade capabilities
            new_capabilities: Post-downgrade capabilities
            grace_days: Days before auto-enforcement (default 7)

        Returns:
            Tuple of (all_violations, immediate_enforcement_results)
        """
        from workspace.core.models import Workspace

        violations = cls.detect_violations(user, old_capabilities, new_capabilities)

        if not violations:
            logger.info(f"No violations detected for user {user.email} downgrade")
            return [], {}

        # Separate immediate vs grace period violations
        immediate_violations = [v for v in violations if not v.requires_grace]
        grace_violations = [v for v in violations if v.requires_grace]

        immediate_results = {}

        # Process immediate violations (domains, payment)
        for violation in immediate_violations:
            if violation.violation_type == 'domains':
                result = cls._enforce_domain_violation(user)
                immediate_results['domains'] = result
            elif violation.violation_type == 'payment':
                result = cls._enforce_payment_violation(user)
                immediate_results['payment'] = result

        # Mark grace period violations on user's workspaces
        if grace_violations:
            grace_violation_types = [v.violation_type for v in grace_violations]
            user_workspaces = Workspace.objects.filter(
                owner=user,
                status='active'
            ).select_for_update()

            for workspace in user_workspaces:
                workspace.mark_plan_violation(
                    violation_types=grace_violation_types,
                    grace_days=grace_days
                )

            logger.info(
                f"Marked {len(list(user_workspaces))} workspaces with violations "
                f"{grace_violation_types} for user {user.email}, "
                f"grace period: {grace_days} days"
            )

        # Log event
        cls._log_violation_event(user, violations, immediate_results)

        return violations, immediate_results

    @classmethod
    def _enforce_domain_violation(cls, user) -> Dict[str, Any]:
        """
        Immediately unbind all custom domains for user.
        No grace period per downgrade guide.
        """
        try:
            from workspace.hosting.models import CustomDomain
            from workspace.core.models import Workspace

            user_workspaces = Workspace.objects.filter(
                owner=user,
                status='active'
            ).values_list('id', flat=True)

            domains = CustomDomain.objects.filter(
                workspace_id__in=user_workspaces,
                status__in=['verified', 'pending']
            ).select_for_update()

            unbound_domains = []
            for domain in domains:
                domain.status = 'inactive'
                domain.save(update_fields=['status', 'updated_at'])
                unbound_domains.append(str(domain.domain_name))

            logger.info(
                f"Immediately unbound {len(unbound_domains)} domains for user {user.email}: "
                f"{unbound_domains}"
            )

            return {
                'enforced': True,
                'domains_unbound': unbound_domains,
                'count': len(unbound_domains)
            }

        except ImportError:
            logger.warning("CustomDomain model not available for enforcement")
            return {'enforced': False, 'error': 'CustomDomain model not available'}
        except Exception as e:
            logger.error(f"Error enforcing domain violation for user {user.email}: {e}")
            return {'enforced': False, 'error': str(e)}

    @classmethod
    def _enforce_payment_violation(cls, user) -> Dict[str, Any]:
        """
        Immediately disable all payment methods for user.
        No grace period - payment is a premium feature.
        """
        try:
            from payments.models import MerchantPaymentMethod
            from workspace.core.models import Workspace

            user_workspaces = Workspace.objects.filter(
                owner=user,
                status='active'
            ).values_list('id', flat=True)

            methods = MerchantPaymentMethod.objects.filter(
                workspace_id__in=user_workspaces,
                enabled=True
            ).select_for_update()

            disabled_methods = []
            for method in methods:
                method.enabled = False
                method.save(update_fields=['enabled', 'updated_at'])
                disabled_methods.append({
                    'provider': method.provider_name,
                    'workspace_id': str(method.workspace_id)
                })

            logger.info(
                f"Immediately disabled {len(disabled_methods)} payment methods "
                f"for user {user.email}"
            )

            return {
                'enforced': True,
                'methods_disabled': disabled_methods,
                'count': len(disabled_methods)
            }

        except ImportError:
            logger.warning("MerchantPaymentMethod model not available for enforcement")
            return {'enforced': False, 'error': 'MerchantPaymentMethod model not available'}
        except Exception as e:
            logger.error(f"Error enforcing payment violation for user {user.email}: {e}")
            return {'enforced': False, 'error': str(e)}

    @classmethod
    def _log_violation_event(cls, user, violations: List[ViolationRecord], immediate_results: Dict):
        """Log violation detection for audit trail"""
        try:
            from subscription.models import SubscriptionEventLog

            subscription = user.subscription
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='compliance_violation_detected',
                description=f"Detected {len(violations)} violations on downgrade",
                metadata={
                    'violations': [
                        {
                            'type': v.violation_type,
                            'current': v.current_count,
                            'limit': v.new_limit,
                            'excess': v.excess_count,
                            'requires_grace': v.requires_grace
                        }
                        for v in violations
                    ],
                    'immediate_enforcement': immediate_results
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log violation event: {e}")

    @classmethod
    @transaction.atomic
    def enforce_grace_period_violations(cls, workspace) -> Dict[str, Any]:
        """
        Auto-enforce all pending violations after grace period expires.
        Called by Celery task when workspace.compliance_deadline passes.

        Uses smart selection logic per downgrade guide:
            - Workspaces: Keep primary/oldest/highest-revenue
            - Products: Keep highest revenue, then oldest
            - Staff: Deactivate least recently active

        Args:
            workspace: Workspace instance with plan_violation status

        Returns:
            Dict with enforcement results per violation type
        """
        if not workspace.is_enforcement_due:
            logger.warning(
                f"Enforcement called for workspace {workspace.id} but deadline not due"
            )
            return {'enforced': False, 'reason': 'deadline_not_due'}

        enforcement_results = {}
        violation_types = workspace.violation_types.copy()

        for violation_type in violation_types:
            if violation_type == 'workspaces':
                result = cls._auto_enforce_workspace_violation(workspace)
                enforcement_results['workspaces'] = result

            elif violation_type == 'products':
                result = cls._auto_enforce_product_violation(workspace)
                enforcement_results['products'] = result

            elif violation_type == 'staff':
                result = cls._auto_enforce_staff_violation(workspace)
                enforcement_results['staff'] = result

            elif violation_type == 'themes':
                result = cls._auto_enforce_theme_violation(workspace)
                enforcement_results['themes'] = result

        # Mark workspace as auto-enforced
        workspace.mark_auto_enforced(enforcement_results)

        logger.info(
            f"Auto-enforced violations for workspace {workspace.id}: "
            f"{enforcement_results}"
        )

        return enforcement_results

    @classmethod
    def _auto_enforce_workspace_violation(cls, workspace) -> Dict[str, Any]:
        """
        Suspend excess workspaces using smart selection.
        Keep: primary (oldest) or highest revenue.
        """
        from workspace.core.models import Workspace

        user = workspace.owner
        new_limit = workspace.capabilities.get('workspace_limit', 1)

        if new_limit == 0:
            return {'enforced': False, 'reason': 'unlimited'}

        # Get all active workspaces, ordered by creation date (oldest first)
        workspaces = list(Workspace.objects.filter(
            owner=user,
            status='active'
        ).order_by('created_at').select_for_update())

        if len(workspaces) <= new_limit:
            return {'enforced': False, 'reason': 'within_limit'}

        # Keep the oldest N workspaces (primary), suspend the rest
        to_keep = workspaces[:new_limit]
        to_suspend = workspaces[new_limit:]

        suspended_ids = []
        for ws in to_suspend:
            ws.suspend_by_plan(reason='workspace_limit_exceeded')
            suspended_ids.append(str(ws.id))

        return {
            'enforced': True,
            'kept': [str(ws.id) for ws in to_keep],
            'suspended': suspended_ids,
            'count': len(suspended_ids)
        }

    @classmethod
    def _auto_enforce_product_violation(cls, workspace) -> Dict[str, Any]:
        """
        Mark excess products as inactive by plan.
        Keep: highest revenue products, then oldest.
        """
        from workspace.store.models import Product

        new_limit = workspace.capabilities.get('product_limit', 20)

        if new_limit == 0:
            return {'enforced': False, 'reason': 'unlimited'}

        # Get products that are both user-active AND plan-active for this workspace
        # Order by: created_at (oldest first = primary products)
        products = list(Product.objects.filter(
            workspace=workspace,
            is_active=True,
            active_by_plan=True
        ).order_by('created_at').select_for_update())

        if len(products) <= new_limit:
            return {'enforced': False, 'reason': 'within_limit'}

        # Keep oldest N products (primary products), mark rest as plan-inactive
        to_keep = products[:new_limit]
        to_deactivate = products[new_limit:]

        deactivated_ids = []
        for product in to_deactivate:
            # Use active_by_plan instead of is_active (preserve user's publish state)
            product.active_by_plan = False
            product.save(update_fields=['active_by_plan', 'updated_at'])
            deactivated_ids.append(str(product.id))

        return {
            'enforced': True,
            'kept': [str(p.id) for p in to_keep],
            'deactivated': deactivated_ids,
            'count': len(deactivated_ids)
        }

    @classmethod
    def _auto_enforce_staff_violation(cls, workspace) -> Dict[str, Any]:
        """
        Suspend excess staff members.
        Keep: most recently active (by updated_at).
        """
        from workspace.core.models import Membership

        new_limit = workspace.capabilities.get('staff_limit', 1)

        if new_limit == 0:
            return {'enforced': False, 'reason': 'unlimited'}

        # Get active staff excluding owner, ordered by last activity
        staff = list(Membership.objects.filter(
            workspace=workspace,
            status=Membership.Status.ACTIVE
        ).exclude(
            user=workspace.owner
        ).order_by('-updated_at').select_for_update())

        if len(staff) <= new_limit:
            return {'enforced': False, 'reason': 'within_limit'}

        # Keep most recently active N staff
        to_keep = staff[:new_limit]
        to_suspend = staff[new_limit:]

        suspended_ids = []
        for member in to_suspend:
            member.suspend(reason='Staff limit exceeded due to plan downgrade')
            suspended_ids.append(str(member.id))

        return {
            'enforced': True,
            'kept': [str(m.id) for m in to_keep],
            'suspended': suspended_ids,
            'count': len(suspended_ids)
        }

    @classmethod
    def _auto_enforce_theme_violation(cls, workspace) -> Dict[str, Any]:
        """
        Deactivate excess themes.
        Keep: most recently used.
        """
        try:
            from theme.models import ThemeInstance

            new_limit = workspace.capabilities.get('theme_library_limit', 1)

            if new_limit == 0:
                return {'enforced': False, 'reason': 'unlimited'}

            themes = list(ThemeInstance.objects.filter(
                workspace=workspace,
                status__in=['active', 'draft']
            ).order_by('-updated_at').select_for_update())

            if len(themes) <= new_limit:
                return {'enforced': False, 'reason': 'within_limit'}

            to_keep = themes[:new_limit]
            to_deactivate = themes[new_limit:]

            deactivated_ids = []
            for theme in to_deactivate:
                theme.status = 'archived'
                theme.save(update_fields=['status', 'updated_at'])
                deactivated_ids.append(str(theme.id))

            return {
                'enforced': True,
                'kept': [str(t.id) for t in to_keep],
                'deactivated': deactivated_ids,
                'count': len(deactivated_ids)
            }

        except ImportError:
            return {'enforced': False, 'reason': 'theme_module_not_available'}

    @classmethod
    def check_and_resolve_violation(cls, workspace, violation_type: str) -> bool:
        """
        Check if a specific violation is now resolved (user action).
        Called when user deletes/deactivates resources.

        Returns:
            True if violation is resolved (usage within limits)
        """
        user = workspace.owner
        capabilities = workspace.capabilities

        is_resolved = False

        if violation_type == 'workspaces':
            limit = capabilities.get('workspace_limit', 1)
            if limit == 0:
                is_resolved = True
            else:
                from workspace.core.models import Workspace
                count = Workspace.objects.filter(
                    owner=user,
                    status__in=['active', 'provisioning']
                ).count()
                is_resolved = count <= limit

        elif violation_type == 'products':
            limit = capabilities.get('product_limit', 20)
            if limit == 0:
                is_resolved = True
            else:
                from workspace.store.models import Product
                count = Product.objects.filter(
                    workspace=workspace,
                    is_active=True,
                    active_by_plan=True
                ).count()
                is_resolved = count <= limit

        elif violation_type == 'staff':
            limit = capabilities.get('staff_limit', 1)
            if limit == 0:
                is_resolved = True
            else:
                from workspace.core.models import Membership
                count = Membership.objects.filter(
                    workspace=workspace,
                    status=Membership.Status.ACTIVE
                ).exclude(user=user).count()
                is_resolved = count <= limit

        elif violation_type == 'themes':
            limit = capabilities.get('theme_library_limit', 1)
            if limit == 0:
                is_resolved = True
            else:
                try:
                    from theme.models import ThemeInstance
                    count = ThemeInstance.objects.filter(
                        workspace=workspace,
                        status__in=['active', 'draft']
                    ).count()
                    is_resolved = count <= limit
                except ImportError:
                    is_resolved = True

        if is_resolved:
            all_resolved = workspace.resolve_violation(violation_type)
            logger.info(
                f"Violation {violation_type} resolved for workspace {workspace.id}, "
                f"all resolved: {all_resolved}"
            )

        return is_resolved
