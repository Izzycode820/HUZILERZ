"""
Domain Management Authentication Middleware (v3.0)

ALL operations require authentication (no public endpoints)
Industry Standard: JWT for identity, X-Workspace-Id header for context
"""

from graphql import GraphQLError
from authentication.services.token_service import TokenService
from workspace.core.models import Workspace, Membership
from workspace.store.utils.workspace_permissions import validate_workspace_access
import logging

logger = logging.getLogger(__name__)


class DomainAuthMiddleware:
    """
    Strict authentication for domain management GraphQL

    Security: All operations require JWT + workspace
    Pattern: Same as Store GraphQL - workspace injection via middleware
    """

    def resolve(self, next, root, info, **kwargs):
        request = info.context

        # Extract JWT from Authorization header
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
