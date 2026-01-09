"""
Workspace Permissions Utility

Production-ready permission validation with performance optimizations
Follows industry standards for security, scalability, and reliability

Performance: Cached permission checks, optimized queries
Security: Defense-in-depth with proper error handling
Scalability: Bulk operations support, connection pooling compatible
Reliability: Comprehensive logging, graceful degradation
"""

from typing import List, Set
from django.core.cache import cache
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger('workspace.store.permissions')


def validate_workspace_access(workspace, user) -> bool:
    """
    Validate user has basic access to workspace (owner or active member)

    Performance: Cached results, optimized single query
    Security: Proper error handling, no information leakage
    Reliability: Graceful degradation on cache/db failures

    Args:
        workspace: Workspace instance
        user: User instance

    Returns:
        bool: True if user has access, False otherwise
    """
    if not user or not user.is_authenticated:
        logger.warning(f"Unauthenticated user attempted workspace access")
        return False

    if not workspace:
        logger.error("Workspace validation called with None workspace")
        return False

    # Cache key for performance
    cache_key = f"workspace_access:{workspace.id}:{user.id}"

    try:
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Single optimized query for both owner and membership checks
        has_access = (
            workspace.owner_id == user.id or
            workspace.members.filter(
                user=user,
                is_active=True
            ).exists()
        )

        # Cache result for 5 minutes (adjust based on your needs)
        cache.set(cache_key, has_access, timeout=300)

        if not has_access:
            logger.warning(
                f"User {user.id} denied access to workspace {workspace.id}"
            )

        return has_access

    except Exception as e:
        # Graceful degradation - log error but don't crash
        logger.error(
            f"Workspace access validation failed for user {user.id}, "
            f"workspace {workspace.id}: {str(e)}",
            exc_info=True
        )
        return False


def validate_permission(workspace, user, permission_key: str) -> bool:
    """
    Check if user has specific permission in workspace using role system

    Uses the core PermissionService for role-based permission checking

    Args:
        workspace: Workspace instance
        user: User instance
        permission_key: Permission key (e.g., 'product:create', 'category:view')

    Returns:
        bool: True if user has permission

    Examples:
        >>> validate_permission(workspace, user, 'category:create')
        >>> validate_permission(workspace, user, 'product:view')
    """
    from workspace.core.services import PermissionService
    return PermissionService.has_permission(user, workspace, permission_key)


def assert_permission(workspace, user, permission_key: str, error_message=None):
    """
    Assert user has permission or raise PermissionDenied
    Use this in service layer for clean code

    Args:
        workspace: Workspace instance
        user: User instance
        permission_key: Permission key (e.g., 'category:create')
        error_message: Optional custom error message

    Raises:
        PermissionDenied: If user lacks permission

    Examples:
        >>> assert_permission(workspace, user, 'category:create')
        >>> assert_permission(workspace, user, 'product:delete', 'Cannot delete product')
    """
    from workspace.core.services import PermissionService
    PermissionService.assert_permission(user, workspace, permission_key, error_message)




def bulk_validate_workspace_access(workspace_ids: List[str], user) -> Set[str]:
    """
    Bulk validate workspace access for multiple workspaces

    Performance: Optimized for bulk operations
    Scalability: Handles large numbers of workspace IDs

    Args:
        workspace_ids: List of workspace IDs to check
        user: User instance

    Returns:
        Set[str]: Set of workspace IDs user has access to
    """
    if not user or not user.is_authenticated:
        return set()

    if not workspace_ids:
        return set()

    try:
        from workspace.core.models import Workspace

        # Single query to get all accessible workspaces
        accessible_workspaces = Workspace.objects.filter(
            models.Q(id__in=workspace_ids) &
            (
                models.Q(owner=user) |
                models.Q(members__user=user, members__is_active=True)
            )
        ).values_list('id', flat=True)

        return set(str(wid) for wid in accessible_workspaces)

    except Exception as e:
        logger.error(
            f"Bulk workspace access validation failed for user {user.id}: {str(e)}",
            exc_info=True
        )
        return set()


def invalidate_workspace_cache(workspace_id: str, user_id: str = None):
    """
    Invalidate cached workspace permissions

    Call this when workspace membership changes

    Args:
        workspace_id: Workspace ID
        user_id: Optional specific user ID, otherwise invalidates all users
    """
    try:
        if user_id:
            # Invalidate specific user
            cache_key = f"workspace_access:{workspace_id}:{user_id}"
            cache.delete(cache_key)
        else:
            # Invalidate all users for this workspace
            # This is a simplified approach - in production you might want
            # to track cache keys more precisely
            cache.delete_many([
                f"workspace_access:{workspace_id}:{uid}"
                for uid in get_user_model().objects.values_list('id', flat=True)
            ])

    except Exception as e:
        logger.error(
            f"Failed to invalidate workspace cache for {workspace_id}: {str(e)}"
        )