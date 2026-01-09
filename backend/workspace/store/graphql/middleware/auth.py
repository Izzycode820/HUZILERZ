"""
Authentication Middleware for GraphQL API (Industry Standard: Shopify/Stripe/Linear)

JWT validates user identity
X-Workspace-Id header provides workspace context per-request
Eliminates context drift, race conditions, and stale workspace bugs
"""

from graphql import GraphQLError
from authentication.services.token_service import TokenService
from workspace.core.models import Workspace, Membership
from workspace.store.utils.workspace_permissions import validate_workspace_access
import logging

logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    """
    Industry-Standard Multi-Tenant Authentication (Shopify Pattern)

    Flow:
    1. Verify JWT (user identity + global roles)
    2. Extract workspace from X-Workspace-Id header
    3. Validate user has access to workspace
    4. Fetch workspace-specific role and permissions
    5. Inject into GraphQL context

    Security:
    - Zero trust: validate access on EVERY request
    - Workspace sent per-request (no stale context)
    - Comprehensive authorization checks
    """

    def resolve(self, next, root, info, **kwargs):
        request = info.context

        # ===== STEP 1: Verify JWT (User Identity) =====
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            raise GraphQLError("Authentication required - missing or invalid Authorization header")

        token = auth_header.split(' ')[1]

        try:
            payload = TokenService.verify_access_token(token)

            # Get user from payload
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.select_related().get(id=payload['user_id'])

        except Exception as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise GraphQLError(f"Authentication failed: {str(e)}")

        # ===== STEP 2: Extract Workspace from Header (Industry Standard) =====
        workspace_id = request.META.get('HTTP_X_WORKSPACE_ID')

        if not workspace_id:
            raise GraphQLError(
                "No workspace context - send X-Workspace-Id header with your request"
            )

        # ===== STEP 3: Validate Workspace Exists and Is Active =====
        try:
            workspace = Workspace.objects.select_related('owner').get(
                id=workspace_id,
                status='active'
            )
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace {workspace_id} not found or inactive (user: {user.id})")
            raise GraphQLError("Workspace not found or inactive")

        # ===== STEP 4: Validate User Has Access + Get Role =====
        # Check if user is workspace owner
        if workspace.owner == user:
            workspace_role = 'owner'
            workspace_permissions = ['read', 'write', 'delete', 'invite', 'admin']
            membership = None
        else:
            # Check membership
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

        # Superuser override (god mode)
        if user.is_superuser:
            workspace_role = 'superuser'
            workspace_permissions = ['read', 'write', 'delete', 'invite', 'admin', 'superuser']

        # ===== STEP 5: Inject into GraphQL Context =====
        # All resolvers access these via info.context
        info.context.user = user
        info.context.user_id = str(user.id)
        info.context.workspace = workspace
        info.context.workspace_id = str(workspace.id)
        info.context.workspace_role = workspace_role
        info.context.workspace_permissions = workspace_permissions
        info.context.is_authenticated = True
        info.context.jwt_payload = payload  # Full JWT payload (subscription, etc.)

        # Auth successful - no logging to avoid spam
        # (This middleware runs on EVERY GraphQL request - queries, mutations, subscriptions)
        return next(root, info, **kwargs)