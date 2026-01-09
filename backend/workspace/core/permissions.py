from functools import wraps
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Workspace, Membership


# ============================================================================
# CORE VALIDATION LOGIC (Shared by all permission systems)
# ============================================================================

def _validate_workspace_access(request, workspace_id, required_permissions=[]):
    """
    Core validation logic for workspace access and permissions

    Args:
        request: Django request object
        workspace_id: UUID of workspace
        required_permissions: List of required permissions

    Returns:
        tuple: (workspace, membership, error_dict)
            error_dict is None if validation passes

    Security checks:
        1. JWT has workspace claims
        2. JWT workspace_id matches URL workspace_id
        3. Workspace exists and is active
        4. User is owner OR has active membership
        5. User has required permissions (owner bypasses)
    """
    # 1. Check JWT has workspace claims
    jwt_workspace_id = getattr(request, 'workspace_id', None)
    workspace_role = getattr(request, 'workspace_role', None)
    workspace_permissions = getattr(request, 'workspace_permissions', [])

    if not jwt_workspace_id:
        return None, None, {
            'error': 'Workspace context required',
            'detail': 'Please switch to a workspace first using /api/auth/workspace-switch/',
            'status_code': status.HTTP_403_FORBIDDEN
        }

    # 2. Validate JWT workspace_id matches URL workspace_id
    if str(jwt_workspace_id) != str(workspace_id):
        return None, None, {
            'error': 'Workspace mismatch',
            'detail': f'JWT workspace ({jwt_workspace_id}) does not match requested workspace ({workspace_id})',
            'status_code': status.HTTP_403_FORBIDDEN
        }

    # 3. Get workspace and validate it's active
    try:
        workspace = Workspace.objects.get(id=workspace_id, status='active')
    except Workspace.DoesNotExist:
        return None, None, {
            'error': 'Workspace not found or inactive',
            'status_code': status.HTTP_404_NOT_FOUND
        }

    # 4. Owner bypasses all permission checks
    if workspace.owner == request.user:
        return workspace, None, None

    # 5. Validate user has active membership
    try:
        membership = Membership.objects.prefetch_related('roles').get(
            user=request.user,
            workspace=workspace,
            is_active=True
        )
    except Membership.DoesNotExist:
        return None, None, {
            'error': 'Access denied',
            'detail': 'You are not a member of this workspace',
            'status_code': status.HTTP_403_FORBIDDEN
        }

    # 6. Check required permissions
    if required_permissions:
        user_permissions = set(workspace_permissions)
        required_perms_set = set(required_permissions)

        if not required_perms_set.issubset(user_permissions):
            missing_perms = required_perms_set - user_permissions
            return None, None, {
                'error': 'Insufficient permissions',
                'detail': f'Missing permissions: {list(missing_perms)}',
                'required': list(required_perms_set),
                'current_role': workspace_role,
                'current_permissions': list(user_permissions),
                'status_code': status.HTTP_403_FORBIDDEN
            }

    # All checks passed
    return workspace, membership, None


# ============================================================================
# DECORATOR-BASED PERMISSIONS (Recommended for function-based views)
# ============================================================================

def requires_workspace_permission(required_permissions):
    """
    Decorator to validate workspace access and permissions from JWT claims

    Usage:
        @requires_workspace_permission(['edit_content'])
        def my_view(request, workspace_id):
            # request.workspace is now available (validated)
            pass

    Args:
        required_permissions (list): Permissions required
            ['view_content'], ['edit_content', 'delete_content'], or []
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, workspace_id, *args, **kwargs):
            workspace, membership, error = _validate_workspace_access(
                request, workspace_id, required_permissions
            )

            if error:
                return Response(
                    {k: v for k, v in error.items() if k != 'status_code'},
                    status=error['status_code']
                )

            # Attach workspace and membership to request
            request.workspace = workspace
            request.workspace_membership = membership

            return view_func(request, workspace_id, *args, **kwargs)

        return wrapper
    return decorator


# Permission constants for consistency
class WorkspacePermissions:
    """Standard workspace permissions - aligned with Role model"""

    # Workspace management
    MANAGE_WORKSPACE = 'manage_workspace'
    MANAGE_MEMBERS = 'manage_members'
    MANAGE_SETTINGS = 'manage_settings'
    MANAGE_BILLING = 'manage_billing'

    # Analytics
    VIEW_ANALYTICS = 'view_analytics'

    # Content operations (products, categories, orders, etc.)
    CREATE_CONTENT = 'create_content'
    EDIT_CONTENT = 'edit_content'
    DELETE_CONTENT = 'delete_content'
    VIEW_CONTENT = 'view_content'

    # Common permission sets
    @classmethod
    def read_only(cls):
        return [cls.VIEW_CONTENT]

    @classmethod
    def read_write(cls):
        return [cls.VIEW_CONTENT, cls.CREATE_CONTENT, cls.EDIT_CONTENT]

    @classmethod
    def full_content_access(cls):
        return [cls.VIEW_CONTENT, cls.CREATE_CONTENT, cls.EDIT_CONTENT, cls.DELETE_CONTENT]


# ============================================================================
# CLASS-BASED PERMISSIONS (For DRF permission_classes - Uses same logic)
# ============================================================================

class HasWorkspacePermission(BasePermission):
    """
    Base class for workspace permissions - uses shared validation logic

    Subclass and set required_permissions list
    """
    required_permissions = []  # Override in subclasses

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace_id = view.kwargs.get('workspace_id')
        if not workspace_id:
            return False

        workspace, membership, error = _validate_workspace_access(
            request, workspace_id, self.required_permissions
        )

        if error:
            # Attach error for debugging
            request._permission_error = error
            return False

        # Attach workspace and membership to request
        request.workspace = workspace
        request.workspace_membership = membership
        return True


class IsWorkspaceMember(HasWorkspacePermission):
    """Access for any workspace member (viewer+)"""
    required_permissions = []  # Any member can access


class CanViewContent(HasWorkspacePermission):
    """Read-only access to workspace content"""
    required_permissions = [WorkspacePermissions.VIEW_CONTENT]


class CanEditContent(HasWorkspacePermission):
    """Can create and edit content"""
    required_permissions = [
        WorkspacePermissions.VIEW_CONTENT,
        WorkspacePermissions.CREATE_CONTENT,
        WorkspacePermissions.EDIT_CONTENT
    ]


class CanDeleteContent(HasWorkspacePermission):
    """Full content access including delete"""
    required_permissions = [
        WorkspacePermissions.VIEW_CONTENT,
        WorkspacePermissions.CREATE_CONTENT,
        WorkspacePermissions.EDIT_CONTENT,
        WorkspacePermissions.DELETE_CONTENT
    ]


class CanManageWorkspace(HasWorkspacePermission):
    """Admin-level workspace management"""
    required_permissions = [
        WorkspacePermissions.MANAGE_SETTINGS,
        WorkspacePermissions.MANAGE_MEMBERS
    ]