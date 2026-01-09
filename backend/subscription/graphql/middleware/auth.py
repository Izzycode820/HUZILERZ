"""
Subscription Authentication Middleware - Hybrid Public/Private Access (v3.0)

Handles both public (plan browsing) and authenticated (subscription management) operations
Industry Standard: JWT for identity, X-Workspace-Id header for context
"""

from graphql import GraphQLError
from authentication.services.token_service import TokenService
from workspace.core.models import Workspace, Membership
from workspace.store.utils.workspace_permissions import validate_workspace_access
import logging

logger = logging.getLogger(__name__)


class SubscriptionAuthMiddleware:
    """
    Conditional authentication for subscription GraphQL

    Public operations (no auth required):
    - plans: Browse available subscription plans
    - planDetails: View plan details
    - trialPricing: Get trial pricing info

    User-level operations (require JWT but NOT workspace):
    - Subscriptions are tied to USERS, not workspaces
    - All subscription queries and mutations

    Workspace-scoped operations (require JWT + workspace):
    - None currently - subscriptions are user-level

    Security: Leverages existing JWT security service
    Performance: Uses existing token verification
    """

    # Public queries that don't require authentication
    PUBLIC_QUERIES = {'plans', 'planDetails', 'trialPricing', '__schema', '__type', 'IntrospectionQuery'}

    # User-level operations: require auth but NOT workspace context
    # Subscriptions are tied to users, not workspaces
    # Includes both queries AND mutations
    USER_LEVEL_OPERATIONS = {
        # Queries
        'currentPlan', 
        'mySubscription', 
        'isIntroPricingEligible',
        # Mutations - subscription checkout flow
        'prepareSubscriptionCheckout',
        'prepareRenewalCheckout',
        'prepareUpgradeCheckout',
        'prepareIntent',  # Key mutation for pricing page
    }

    def resolve(self, next, root, info, **kwargs):
        request = info.context

        # Check if we already determined this is a public operation
        if hasattr(info.context, '_is_public_operation') and info.context._is_public_operation:
            return next(root, info, **kwargs)

        # Check if we already determined this is a user-level operation (no workspace needed)
        if hasattr(info.context, '_is_user_level_operation') and info.context._is_user_level_operation:
            return next(root, info, **kwargs)

        # Check if this is a public query
        operation_name = self._get_operation_name(info)

        if operation_name in self.PUBLIC_QUERIES:
            # Public access - skip authentication for this entire operation tree
            info.context.is_authenticated = False
            info.context.user = None
            info.context.workspace = None
            info.context._is_public_operation = True
            return next(root, info, **kwargs)

        # Private operation - require authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            raise GraphQLError("Authentication required")

        token = auth_header.split(' ')[1]

        # Use existing token service for verification
        try:
            payload = TokenService.verify_access_token(token)

            # Get user from payload
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=payload['user_id'])

        except Exception as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise GraphQLError(f"Authentication failed: {str(e)}")

        # USER-LEVEL OPERATIONS: Auth required but NO workspace context needed
        # Subscriptions are user-level, not workspace-scoped
        if operation_name in self.USER_LEVEL_OPERATIONS:
            info.context.user = user
            info.context.user_id = str(user.id)
            info.context.workspace = None
            info.context.workspace_id = None
            info.context.is_authenticated = True
            info.context.jwt_payload = payload
            info.context._is_user_level_operation = True
            return next(root, info, **kwargs)

        # v3.0 - Extract workspace from X-Workspace-Id header (Industry Standard)
        workspace_id = request.META.get('HTTP_X_WORKSPACE_ID')

        if not workspace_id:
            raise GraphQLError(
                "No workspace context - send X-Workspace-Id header with your request"
            )

        # Validate workspace exists and is active
        try:
            workspace = Workspace.objects.select_related('owner').get(
                id=workspace_id,
                status='active'
            )
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace {workspace_id} not found or inactive (user: {user.id})")
            raise GraphQLError("Workspace not found or inactive")

        # Validate user has access + get role
        if workspace.owner == user:
            workspace_role = 'owner'
            workspace_permissions = ['read', 'write', 'delete', 'invite', 'admin']
        else:
            try:
                membership = Membership.objects.get(
                    workspace=workspace,
                    user=user,
                    is_active=True
                )
                workspace_role = membership.role
                workspace_permissions = membership.permissions or ['read']
            except Membership.DoesNotExist:
                logger.error(
                    f"SECURITY: User {user.id} attempted unauthorized access to workspace {workspace_id}"
                )
                raise GraphQLError(
                    "Access denied - you do not have permission to access this workspace"
                )

        # Superuser override
        if user.is_superuser:
            workspace_role = 'superuser'
            workspace_permissions = ['read', 'write', 'delete', 'invite', 'admin', 'superuser']

        # Inject into GraphQL context
        info.context.user = user
        info.context.user_id = str(user.id)
        info.context.workspace = workspace
        info.context.workspace_id = str(workspace.id)
        info.context.workspace_role = workspace_role
        info.context.workspace_permissions = workspace_permissions
        info.context.is_authenticated = True
        info.context.jwt_payload = payload

        return next(root, info, **kwargs)

    def _get_operation_name(self, info):
        """
        Extract operation name from GraphQL info

        Returns the field name being queried/mutated
        """
        # Get the field name from the GraphQL operation
        if info.field_name:
            return info.field_name

        # Fallback to operation name from query
        if hasattr(info.operation, 'name') and info.operation.name:
            return info.operation.name.value

        return None
