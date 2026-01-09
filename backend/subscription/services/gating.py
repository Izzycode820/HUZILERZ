"""
Capability Gating Service
Centralized utility for feature gating across all modules

Pattern: workspace.capabilities (denormalized) -> validation at creation time
Follows Shopify/Stripe industry standard for subscription-based feature gating

Usage:
    from subscription.services.gating import check_product_limit, check_storage_limit
    
    allowed, error_msg = check_product_limit(workspace)
    if not allowed:
        return {'success': False, 'error': error_msg}
"""
from typing import Tuple, Optional, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class GatingError(Exception):
    """
    Raised when capability check fails
    Contains structured data for frontend upgrade prompts
    """
    def __init__(
        self,
        capability: str,
        limit: int,
        current: int,
        message: str,
        upgrade_required: bool = True
    ):
        self.capability = capability
        self.limit = limit
        self.current = current
        self.message = message
        self.upgrade_required = upgrade_required
        super().__init__(message)


class RestrictedModeError(Exception):
    """
    Raised when workspace is in restricted mode (subscription payment issue)
    Contains structured data for frontend reactivation prompts
    """
    def __init__(
        self,
        workspace_id: str,
        workspace_name: str,
        reason: str,
        message: str
    ):
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name
        self.reason = reason
        self.message = message
        self.error_code = 'WORKSPACE_RESTRICTED'
        self.reactivation_required = True
        super().__init__(message)


def check_restricted_mode(workspace, user=None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if workspace is in restricted mode (subscription payment issue).
    MUST be called FIRST by all gating functions.

    When restricted_mode=True, ALL new actions are blocked:
    - Create product
    - Invite staff
    - Add domain
    - Deploy site
    etc.

    Args:
        workspace: Workspace instance
        user: Optional User instance for context-aware error messages

    Returns:
        Tuple of (allowed: bool, error_dict: Optional[Dict])
        error_dict contains structured data for frontend toast/modal

    Usage:
        allowed, error = check_restricted_mode(workspace, user)
        if not allowed:
            return {'success': False, **error}
    """
    if not workspace:
        return True, None

    # Check restricted_mode flag
    if getattr(workspace, 'restricted_mode', False):
        reason = getattr(workspace, 'restricted_reason', 'subscription_issue')
        restricted_at = getattr(workspace, 'restricted_at', None)
        
        # Determine if user is owner or staff for context-aware messaging
        is_owner = user and workspace.owner == user if user else True
        
        # Build user-friendly message based on reason and role
        if is_owner:
            # Owner sees messages about THEIR subscription
            reason_messages = {
                'grace_period_expired': (
                    "Your subscription payment is overdue. "
                    "Please renew to continue creating new content."
                ),
                'payment_failed': (
                    "Your last payment failed. "
                    "Please update your payment method to continue."
                ),
                'admin_action': (
                    "Your workspace has been restricted by an administrator. "
                    "Please contact support for assistance."
                ),
            }
            message = reason_messages.get(reason, (
                "Your workspace is currently restricted. "
                "Please renew your subscription to continue."
            ))
            suggestion = 'Go to Settings > Subscription to renew your plan.'
        else:
            # Staff sees messages about OWNER's subscription
            owner_email = workspace.owner.email if hasattr(workspace, 'owner') else 'the workspace owner'
            reason_messages = {
                'grace_period_expired': (
                    f"This workspace's subscription payment is overdue. "
                    f"Contact {owner_email} to resolve this issue."
                ),
                'payment_failed': (
                    f"This workspace's payment failed. "
                    f"Contact {owner_email} to update the payment method."
                ),
                'admin_action': (
                    f"This workspace has been restricted by an administrator. "
                    f"Contact {owner_email} for more information."
                ),
            }
            message = reason_messages.get(reason, (
                f"This workspace is currently restricted due to a subscription issue. "
                f"Contact {owner_email} to resolve this."
            ))
            suggestion = f'Ask {owner_email} to renew the subscription.'

        return False, {
            'error': message,
            'error_code': 'WORKSPACE_RESTRICTED',
            'workspace_id': str(workspace.id),
            'workspace_name': workspace.name,
            'restricted_reason': reason,
            'restricted_at': restricted_at.isoformat() if restricted_at else None,
            'reactivation_required': True,
            'suggestion': suggestion,
            'is_owner': is_owner
        }

    return True, None


def check_capability(
    capabilities: Dict[str, Any],
    capability: str,
    current_count: int = None
) -> Tuple[bool, Optional[str]]:
    """
    Generic capability check against a capabilities dict
    
    Args:
        capabilities: Dict from workspace.capabilities or hosting_env.capabilities
        capability: Capability key from plans.yaml (e.g., 'product_limit', 'custom_domain')
        current_count: Current usage count (for limit-based capabilities)
        
    Returns:
        Tuple of (allowed: bool, error_message: Optional[str])
        
    Conventions:
        - 0 = unlimited (no restriction)
        - False = feature not available
        - True = feature available
        - Integer > 0 = limit
    """
    if not capabilities:
        capabilities = {}
    
    limit = capabilities.get(capability)
    
    # Capability not defined - default deny for safety
    if limit is None:
        logger.warning(f"Capability '{capability}' not found in capabilities dict")
        return False, f"Feature '{capability}' is not available on your current plan."
    
    # Boolean capabilities (custom_domain, deployment_allowed, etc.)
    if isinstance(limit, bool):
        if not limit:
            return False, (
                f"Feature '{capability.replace('_', ' ')}' requires an upgraded plan."
            )
        return True, None
    
    # Numeric limits (0 = unlimited)
    if limit == 0:
        return True, None
    
    # Limit check
    if current_count is not None and current_count >= limit:
        return False, (
            f"Your plan allows {limit} {capability.replace('_limit', 's').replace('_', ' ')}. "
            f"Current: {current_count}. Upgrade to add more."
        )
    
    return True, None


def check_product_limit(workspace) -> Tuple[bool, Optional[str]]:
    """
    Check if workspace can create more products

    Performance: Single COUNT query with index on workspace_id

    Args:
        workspace: Workspace instance with capabilities JSONField

    Returns:
        Tuple of (allowed: bool, error_message: Optional[str])
    """
    # RESTRICTION CHECK FIRST: Block all actions if workspace is restricted
    allowed, error = check_restricted_mode(workspace)
    if not allowed:
        return False, error.get('error')

    # Lazy import to avoid circular dependencies
    from workspace.store.models import Product

    capabilities = workspace.capabilities or {}
    product_limit = capabilities.get('product_limit', 0)

    # 0 = unlimited, skip counting
    if product_limit == 0:
        return True, None

    # Count existing products that are both user-active AND plan-active
    current_count = Product.objects.filter(
        workspace=workspace,
        deleted_at__isnull=True,
        active_by_plan=True  # Only count plan-active products toward limit
    ).count()

    return check_capability(capabilities, 'product_limit', current_count)


def check_product_plan_compliance(product) -> Tuple[bool, Optional[str]]:
    """
    Check if a specific product is active by plan (not restricted by downgrade).

    Use this before checkout, order creation, or product publish operations.
    Products marked active_by_plan=False cannot be sold or published.

    Args:
        product: Product instance

    Returns:
        Tuple of (allowed: bool, error_message: Optional[str])
    """
    if product.active_by_plan:
        return True, None

    return False, (
        f"Product '{product.name}' is restricted due to plan limits. "
        f"Upgrade your plan or contact support to restore access to this product."
    )


def check_product_limit_for_batch(
    workspace,
    batch_size: int
) -> Tuple[bool, Optional[str], Dict[str, int]]:
    """
    Check if workspace can create a batch of products
    
    Used for bulk import operations
    
    Args:
        workspace: Workspace instance
        batch_size: Number of products to create
        
    Returns:
        Tuple of (allowed, error_message, info_dict)
        info_dict contains: current_count, limit, remaining
    """
    from workspace.store.models import Product
    
    capabilities = workspace.capabilities or {}
    product_limit = capabilities.get('product_limit', 0)
    
    current_count = Product.objects.filter(
        workspace=workspace,
        deleted_at__isnull=True
    ).count()
    
    info = {
        'current_count': current_count,
        'limit': product_limit,
        'remaining': (product_limit - current_count) if product_limit > 0 else -1,
        'batch_size': batch_size
    }
    
    # 0 = unlimited
    if product_limit == 0:
        return True, None, info
    
    # Check if batch would exceed limit
    if (current_count + batch_size) > product_limit:
        remaining = max(0, product_limit - current_count)
        return False, (
            f"Bulk import would exceed product limit. "
            f"Limit: {product_limit}, Current: {current_count}, "
            f"Trying to add: {batch_size}. You can add {remaining} more products."
        ), info
    
    return True, None, info


def check_storage_limit(
    user,
    additional_bytes: int = 0
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Check if user can upload more storage
    Uses HostingEnvironment for storage tracking (SOURCE OF TRUTH for usage)
    
    Args:
        user: User instance with hosting_environment relation
        additional_bytes: Bytes to be added (file size)
        
    Returns:
        Tuple of (allowed, error_message, usage_info)
        usage_info contains: used_gb, limit_gb, percentage, status
    """
    try:
        hosting_env = user.hosting_environment
    except AttributeError:
        logger.error(f"User {user.id} has no hosting_environment")
        return False, "Hosting environment not configured. Please contact support.", {}
    
    storage_limit_gb = hosting_env.capabilities.get('storage_gb', 0)
    storage_used_gb = float(hosting_env.storage_used_gb)
    additional_gb = additional_bytes / (1024 ** 3)
    
    # Build usage info
    if storage_limit_gb > 0:
        percentage = (storage_used_gb / storage_limit_gb) * 100
    else:
        percentage = 0
    
    usage_info = {
        'used_gb': round(storage_used_gb, 2),
        'limit_gb': storage_limit_gb,
        'percentage': round(percentage, 1),
        'additional_gb': round(additional_gb, 4),
        'status': 'ok'
    }
    
    # 0 = unlimited
    if storage_limit_gb == 0:
        return True, None, usage_info
    
    # Check thresholds
    new_total = storage_used_gb + additional_gb
    
    if new_total > storage_limit_gb:
        usage_info['status'] = 'exceeded'
        return False, (
            f"Upload would exceed {storage_limit_gb}GB storage limit. "
            f"Current usage: {storage_used_gb:.2f}GB. "
            f"File size: {additional_gb:.4f}GB. "
            f"Upgrade your plan for more storage."
        ), usage_info
    
    # Warning thresholds
    new_percentage = (new_total / storage_limit_gb) * 100
    if new_percentage >= 90:
        usage_info['status'] = 'critical'
    elif new_percentage >= 80:
        usage_info['status'] = 'warning'
    
    return True, None, usage_info


def check_boolean_capability(
    capabilities: Dict[str, Any],
    capability: str,
    feature_display_name: str = None
) -> Tuple[bool, Optional[str]]:
    """
    Check boolean feature flags (custom_domain, deployment_allowed, etc.)
    
    Args:
        capabilities: Dict from workspace.capabilities or hosting_env.capabilities
        capability: Capability key
        feature_display_name: Human-readable name for error message
        
    Returns:
        Tuple of (allowed, error_message)
    """
    if not capabilities:
        capabilities = {}
    
    display_name = feature_display_name or capability.replace('_', ' ').title()
    
    if not capabilities.get(capability, False):
        return False, (
            f"{display_name} is not available on your current plan. "
            f"Upgrade to Pro or Enterprise to access this feature."
        )
    
    return True, None


def check_staff_limit(workspace, include_pending: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Check if workspace can invite more staff members
    
    Counts BOTH active members AND pending invites to prevent over-inviting.
    Defense in depth: checked when sending invite AND when accepting invite.
    
    Performance: Two COUNT queries with indices on workspace_id
    
    Args:
        workspace: Workspace instance with capabilities JSONField
        include_pending: If True, counts pending invites in the total (default True)
        
    Returns:
        Tuple of (allowed: bool, error_message: Optional[str])
    """
    # RESTRICTION CHECK FIRST
    allowed, error = check_restricted_mode(workspace)
    if not allowed:
        return False, error.get('error')

    from workspace.core.models import Membership, WorkspaceInvite
    
    capabilities = workspace.capabilities or {}
    staff_limit = capabilities.get('staff_limit', 1)
    
    # 0 = unlimited, skip counting
    if staff_limit == 0:
        return True, None
    
    # Count active members (not suspended, not removed)
    active_count = Membership.objects.filter(
        workspace=workspace,
        status='active'
    ).count()
    
    # Count pending invites (not expired, not accepted)
    pending_count = 0
    if include_pending:
        pending_count = WorkspaceInvite.objects.filter(
            workspace=workspace,
            status='pending'
        ).count()
    
    current_count = active_count + pending_count
    
    logger.debug(
        f"Staff limit check: workspace={workspace.id}, limit={staff_limit}, "
        f"active={active_count}, pending={pending_count}, total={current_count}"
    )
    
    return check_capability(capabilities, 'staff_limit', current_count)


def check_theme_library_limit(workspace) -> Tuple[bool, Optional[str]]:
    """
    Check if workspace can clone/duplicate more themes
    
    Performance: Single COUNT query with index on workspace_id
    
    Args:
        workspace: Workspace instance with capabilities JSONField
        
    Returns:
        Tuple of (allowed: bool, error_message: Optional[str])
    """
    # RESTRICTION CHECK FIRST
    allowed, error = check_restricted_mode(workspace)
    if not allowed:
        return False, error.get('error')

    from theme.models import TemplateCustomization
    
    capabilities = workspace.capabilities or {}
    theme_limit = capabilities.get('theme_library_limit', 1)
    
    # 0 = unlimited, skip counting
    if theme_limit == 0:
        return True, None
    
    # Count themes in workspace library
    current_count = TemplateCustomization.objects.filter(
        workspace=workspace
    ).count()
    
    return check_capability(capabilities, 'theme_library_limit', current_count)


def check_payment_processing(workspace) -> Tuple[bool, Optional[str]]:
    """
    Check if workspace can add payment methods
    
    Args:
        workspace: Workspace instance with capabilities JSONField
        
    Returns:
        Tuple of (allowed: bool, error_message: Optional[str])
    """
    # RESTRICTION CHECK FIRST
    allowed, error = check_restricted_mode(workspace)
    if not allowed:
        return False, error.get('error')

    capabilities = workspace.capabilities or {}
    return check_boolean_capability(
        capabilities, 'payment_processing', 'Payment processing'
    )


# Analytics capability levels (matches plans.yaml)
ANALYTICS_LEVELS = {
    'none': 0,
    'basic': 1,
    'pro': 2,
    'advanced': 3,
}


def check_analytics_capability(
    workspace,
    required_level: str = 'basic'
) -> Tuple[bool, Optional[str]]:
    """
    Check if workspace has sufficient analytics capability level.
    
    Args:
        workspace: Workspace instance with capabilities JSONField
        required_level: Required analytics level (basic, pro, advanced)
        
    Returns:
        Tuple of (allowed, error_message)
    """
    capabilities = workspace.capabilities or {}
    workspace_analytics = capabilities.get('analytics')
    
    # analytics: none or missing means no analytics
    if not workspace_analytics or workspace_analytics == 'none':
        return False, (
            "Analytics is not available on your current plan. "
            "Please ensure you have an active subscription to access analytics."
        )
    
    workspace_level = ANALYTICS_LEVELS.get(workspace_analytics, 0)
    required = ANALYTICS_LEVELS.get(required_level, 1)
    
    if workspace_level < required:
        level_to_plan = {
            'basic': 'Free',
            'pro': 'Pro',
            'advanced': 'Enterprise'
        }
        required_plan = level_to_plan.get(required_level, 'Pro')
        return False, (
            f"This analytics feature requires {required_level} analytics capability. "
            f"Upgrade to {required_plan} plan to access this feature."
        )
    
    return True, None


def get_analytics_level(workspace) -> str:
    """
    Get the analytics capability level for a workspace.
    
    Args:
        workspace: Workspace instance
        
    Returns:
        Analytics level string (none, basic, pro, advanced)
    """
    capabilities = workspace.capabilities or {}
    return capabilities.get('analytics', 'none')


def can_access_analytics_event(workspace, event_type: str) -> bool:
    """
    Check if workspace can access a specific analytics event type.
    
    Event types map to analytics levels:
    - basic: order_completed, order_failed, store_page_view, add_to_cart
    - pro: product_view, checkout_started, customer_created, cart_abandoned
    - advanced: customer_returned, coupon_applied, order_refunded, delivery_completed
    
    Args:
        workspace: Workspace instance
        event_type: Event type to check
        
    Returns:
        True if workspace can access this event type
    """
    # Import here to avoid circular dependency
    from workspace.analytics.models import StoreEvent
    return StoreEvent.can_track_event(workspace, event_type)


def check_workspace_access(user, workspace) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if user can access a specific workspace for SWITCHING (read access).
    Used by switch_workspace in auth_service.py for workspace switching gating.

    IMPORTANT: This function checks READ access only (workspace switching).
    Write operations (create product, invite staff) are blocked by check_restricted_mode()
    in individual gating functions like check_product_limit(), check_staff_limit(), etc.

    Design Principle:
        - restricted_mode blocks WRITE operations (handled by check_restricted_mode)
        - workspace.status blocks READ+WRITE (handled here)
        - subscription.status limits workspace access (handled here)

    Checks (in order):
        1. Workspace status (suspended_by_plan = noncompliant excess workspace)
        2. Subscription status (restricted = allow only primary workspace)

    Args:
        user: User instance (workspace owner)
        workspace: Workspace instance to check access for

    Returns:
        Tuple of (allowed: bool, error_dict: Optional[Dict])
        error_dict contains structured data for frontend toast/modal

    Usage in switch_workspace:
        allowed, error = check_workspace_access(user, workspace)
        if not allowed:
            return {'success': False, **error}
    """
    # Check 1: Workspace status (suspended_by_plan = noncompliant excess workspace)
    # This workspace is an "excess" workspace beyond plan limit
    if workspace.status == 'suspended_by_plan':
        return False, {
            'error': (
                f"Workspace '{workspace.name}' is not accessible on your current plan. "
                f"Your plan allows fewer workspaces than you currently have."
            ),
            'error_code': 'WORKSPACE_NONCOMPLIANT',
            'workspace_id': str(workspace.id),
            'workspace_name': workspace.name,
            'noncompliant_reason': 'workspace_limit_exceeded',
            'upgrade_required': True,
            'suggestion': (
                'Upgrade your plan to access all workspaces, '
                'or delete excess workspaces to stay within your current limit.'
            )
        }

    # Check 2: Subscription status check (for owner only)
    # When subscription is restricted, only allow access to primary (oldest) workspace
    if workspace.owner == user:
        try:
            subscription = user.subscription
            if subscription.status == 'restricted':
                # User's subscription is restricted - check if this workspace is the primary (oldest)
                from workspace.core.models import Workspace
                oldest_workspace = Workspace.objects.filter(
                    owner=user,
                    status='active'
                ).order_by('created_at').first()

                if oldest_workspace and oldest_workspace.id != workspace.id:
                    # Not the primary workspace - block access
                    return False, {
                        'error': (
                            f"Your subscription is restricted. "
                            f"Only your primary workspace ('{oldest_workspace.name}') is accessible. "
                            f"Renew your subscription to access all workspaces."
                        ),
                        'error_code': 'SUBSCRIPTION_RESTRICTED',
                        'workspace_id': str(workspace.id),
                        'workspace_name': workspace.name,
                        'primary_workspace_id': str(oldest_workspace.id),
                        'primary_workspace_name': oldest_workspace.name,
                        'reactivation_required': True,
                        'suggestion': 'Go to Settings > Subscription to renew your plan.'
                    }
        except Exception:
            # No subscription = free tier, usually 1 workspace allowed
            pass

    # Allow access - user can VIEW this workspace
    # Note: restricted_mode will still block WRITE operations (create product, etc.)
    return True, None
