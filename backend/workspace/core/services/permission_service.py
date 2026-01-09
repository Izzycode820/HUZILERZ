# Permission Service - Authorization context and permission checking

from django.core.exceptions import PermissionDenied
from django.core.cache import cache
import logging

logger = logging.getLogger('workspace.core.services')


class PermissionService:
    """
    Central authorization service following industry standard pattern

    Key principles (from guide):
    - Authorization is evaluated per request
    - Context resolved: user -> workspace -> membership -> permissions
    - Never read permissions from JWT
    - Never check role names - always check permissions
    - Deny by default
    - Cache permissions per request (NOT globally)
    """

    @staticmethod
    def build_request_context(user, workspace):
        """
        Build authorization context for a request
        Following guide pattern:

        context = {
            user,
            workspace,
            membership,
            permissions: Set<string>
        }

        Args:
            user: User instance (from JWT authentication)
            workspace: Workspace instance (from X-Workspace-Id header or resolver)

        Returns:
            Dict with context including permissions set

        Note: This should be called once per request and cached in request context
        """
        from workspace.core.models import Membership

        context = {
            'user': user,
            'workspace': workspace,
            'membership': None,
            'permissions': set()
        }

        # Get active membership
        membership = Membership.get_user_active_membership(user, workspace)

        if membership:
            context['membership'] = membership
            # Get permissions from role
            context['permissions'] = membership.permissions  # Returns set from role

        return context

    @staticmethod
    def has_permission(user, workspace, permission_key):
        """
        Check if user has specific permission in workspace
        Core authorization method - used throughout the system

        Args:
            user: User instance
            workspace: Workspace instance
            permission_key: Permission key string (e.g., 'product:create')

        Returns:
            bool: True if user has permission

        CRITICAL: Deny by default. Missing permission = reject.
        """
        from workspace.core.models import Membership

        # Get active membership
        membership = Membership.get_user_active_membership(user, workspace)

        if not membership:
            logger.warning(
                f"Permission denied: {user.email} has no active membership in {workspace.name}"
            )
            return False

        # Check permission via membership -> role -> permissions
        has_perm = membership.has_permission(permission_key)

        if not has_perm:
            logger.debug(
                f"Permission denied: {user.email} lacks '{permission_key}' in {workspace.name}"
            )

        return has_perm

    @staticmethod
    def assert_permission(user, workspace, permission_key, error_message=None):
        """
        Assert user has permission or raise PermissionDenied
        Use this in service methods for cleaner code

        Args:
            user: User instance
            workspace: Workspace instance
            permission_key: Permission key string
            error_message: Optional custom error message

        Raises:
            PermissionDenied: If user lacks permission
        """
        if not PermissionService.has_permission(user, workspace, permission_key):
            message = error_message or f"Insufficient permissions: '{permission_key}' required"
            logger.warning(
                f"Permission assertion failed: {user.email} in {workspace.name} - {permission_key}"
            )
            raise PermissionDenied(message)

    @staticmethod
    def get_user_permissions(user, workspace):
        """
        Get all permissions for user in workspace
        Returns as list for serialization

        Args:
            user: User instance
            workspace: Workspace instance

        Returns:
            List of permission key strings
        """
        from workspace.core.models import Membership

        membership = Membership.get_user_active_membership(user, workspace)

        if not membership:
            return []

        # Return as list for JSON serialization
        return list(membership.permissions)

    @staticmethod
    def check_multiple_permissions(user, workspace, permission_keys, require_all=True):
        """
        Check multiple permissions at once
        Useful for complex authorization logic

        Args:
            user: User instance
            workspace: Workspace instance
            permission_keys: List of permission key strings
            require_all: If True, requires ALL permissions. If False, requires ANY permission.

        Returns:
            bool: True if check passes
        """
        from workspace.core.models import Membership

        membership = Membership.get_user_active_membership(user, workspace)

        if not membership:
            return False

        user_permissions = membership.permissions

        if require_all:
            # User must have ALL specified permissions
            return all(perm in user_permissions for perm in permission_keys)
        else:
            # User must have AT LEAST ONE permission
            return any(perm in user_permissions for perm in permission_keys)

    @staticmethod
    def can_user_access_workspace(user, workspace):
        """
        Check if user has ANY access to workspace
        Returns True if user has active membership

        Args:
            user: User instance
            workspace: Workspace instance

        Returns:
            bool: True if user has active membership
        """
        from workspace.core.models import Membership

        membership = Membership.get_user_active_membership(user, workspace)
        return membership is not None

    @staticmethod
    def get_workspace_role(user, workspace):
        """
        Get user's role in workspace
        Returns None if no active membership

        Args:
            user: User instance
            workspace: Workspace instance

        Returns:
            Role instance or None
        """
        from workspace.core.models import Membership

        membership = Membership.get_user_active_membership(user, workspace)
        return membership.role if membership else None

    @staticmethod
    def invalidate_permission_cache(user, workspace):
        """
        Invalidate permission cache for user in workspace
        Call this when:
        - User role changes
        - Role permissions change
        - Membership status changes

        Args:
            user: User instance
            workspace: Workspace instance

        Note: Currently no caching implemented at service level.
        Request-level caching handled by GraphQL context.
        This is a placeholder for future Redis caching.
        """
        # Placeholder for future Redis-based permission caching
        # cache_key = f"permissions:{user.id}:{workspace.id}"
        # cache.delete(cache_key)
        logger.debug(f"Permission cache invalidated for {user.email} in {workspace.name}")

    @staticmethod
    def get_permission_context_for_logging(user, workspace):
        """
        Get permission context for logging/debugging
        Useful for audit trails and debugging authorization issues

        Args:
            user: User instance
            workspace: Workspace instance

        Returns:
            Dict with detailed permission context
        """
        from workspace.core.models import Membership

        membership = Membership.get_user_active_membership(user, workspace)

        if not membership:
            return {
                'user_id': str(user.id),
                'user_email': user.email,
                'workspace_id': str(workspace.id),
                'workspace_name': workspace.name,
                'has_membership': False,
                'role': None,
                'permissions': []
            }

        return {
            'user_id': str(user.id),
            'user_email': user.email,
            'workspace_id': str(workspace.id),
            'workspace_name': workspace.name,
            'has_membership': True,
            'membership_id': str(membership.id),
            'membership_status': membership.status,
            'role_id': str(membership.role.id),
            'role_name': membership.role.name,
            'permissions': list(membership.permissions)
        }
