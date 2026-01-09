"""
Membership & Roles GraphQL Queries
Provides workspace staff management queries following Shopify pattern

Security: All queries automatically scoped to authenticated workspace
Performance: Uses select_related and prefetch_related for N+1 prevention
"""

import graphene
import django_filters
from graphql import GraphQLError
from graphene_django.filter import DjangoFilterConnectionField

from ..types.membership_types import (
    WorkspaceMemberType,
    RoleType,
    PermissionType,
    WorkspaceInviteType,
    PermissionSummaryType,
    MyPermissionsType
)
from workspace.core.models import Membership, Role, Permission, WorkspaceInvite
from workspace.core.services import PermissionService, MembershipService


class MembershipFilterSet(django_filters.FilterSet):
    """
    FilterSet for Membership with explicit field definitions

    Security: Explicitly defines filterable fields
    Best Practice: Required by django-filter 2.0+
    """
    # Custom filter for role name (now supports M2M relationship)
    role_name = django_filters.CharFilter(method='filter_by_role_name')

    class Meta:
        model = Membership
        fields = {
            'status': ['exact'],
            'user__email': ['icontains'],
        }

    def filter_by_role_name(self, queryset, name, value):
        """Filter memberships by role name (supports M2M)"""
        return queryset.filter(roles__name=value).distinct()


class RoleFilterSet(django_filters.FilterSet):
    """
    FilterSet for Role with explicit field definitions

    Security: Explicitly defines filterable fields
    Best Practice: Required by django-filter 2.0+
    """
    class Meta:
        model = Role
        fields = {
            'name': ['exact', 'icontains'],
            'is_system': ['exact'],
        }


class MembershipQueries(graphene.ObjectType):
    """
    Membership queries with workspace auto-scoping
    Following Shopify Users page pattern

    Security: All queries automatically scoped to authenticated workspace
    Authorization: Permission checks via PermissionService
    """

    # Main workspace members list (Shopify Users page)
    workspace_members = DjangoFilterConnectionField(
        WorkspaceMemberType,
        filterset_class=MembershipFilterSet,
        description="List all workspace members with status and roles (requires staff:view permission)"
    )

    # Single member details (Shopify member details page)
    workspace_member = graphene.Field(
        WorkspaceMemberType,
        id=graphene.ID(required=True),
        description="Get single workspace member details (requires staff:view permission)"
    )

    # Workspace roles dropdown (for "Assign roles" in add user modal)
    workspace_roles = DjangoFilterConnectionField(
        RoleType,
        filterset_class=RoleFilterSet,
        description="List all workspace roles for assignment (requires staff:view permission)"
    )

    # Single role details
    workspace_role = graphene.Field(
        RoleType,
        id=graphene.ID(required=True),
        description="Get single role with permissions"
    )

    # All available permissions in system
    available_permissions = graphene.List(
        PermissionType,
        description="List all available permissions in the system"
    )

    # Pending invitations
    pending_invites = graphene.List(
        WorkspaceInviteType,
        description="List pending workspace invitations (requires staff:view permission)"
    )

    # Current user's permissions (for frontend UI state)
    my_permissions = graphene.Field(
        MyPermissionsType,
        description="Get current user's permissions in workspace"
    )

    # Permission summary for member (used in member details page)
    member_permission_summary = graphene.List(
        PermissionSummaryType,
        member_id=graphene.ID(required=True),
        description="Get permission summary grouped by resource"
    )

    def resolve_workspace_members(self, info, **kwargs):
        """
        Resolve workspace members list
        Following Shopify Users page pattern: User | Status | Role

        Security: Requires 'staff:view' permission
        Performance: Uses select_related for user and role
        """
        workspace = info.context.workspace
        user = info.context.user

        # Check permission
        if not PermissionService.has_permission(user, workspace, 'staff:view'):
            raise GraphQLError("Insufficient permissions to view workspace members")

        return Membership.objects.filter(
            workspace=workspace
        ).select_related('user').prefetch_related(
            'roles',
            'roles__role_permissions'
        ).order_by('-joined_at')

    def resolve_workspace_member(self, info, id):
        """
        Resolve single workspace member
        For member details page

        Security: Requires 'staff:view' permission
        """
        workspace = info.context.workspace
        user = info.context.user

        # Check permission
        if not PermissionService.has_permission(user, workspace, 'staff:view'):
            raise GraphQLError("Insufficient permissions to view member details")

        try:
            return Membership.objects.select_related(
                'user', 'workspace'
            ).prefetch_related(
                'roles',
                'roles__role_permissions'
            ).get(
                id=id,
                workspace=workspace
            )
        except Membership.DoesNotExist:
            raise GraphQLError("Member not found")

    def resolve_workspace_roles(self, info, **kwargs):
        """
        Resolve workspace roles for dropdown
        Used in "Add users" modal role selection

        Security: Requires 'staff:view' permission
        Performance: Prefetches permissions for each role
        """
        workspace = info.context.workspace
        user = info.context.user

        # Check permission
        if not PermissionService.has_permission(user, workspace, 'staff:view'):
            raise GraphQLError("Insufficient permissions to view roles")

        return Role.objects.filter(
            workspace=workspace,
            is_system=False
        ).prefetch_related('role_permissions').order_by('name')

    def resolve_workspace_role(self, info, id):
        """
        Resolve single role with permissions

        Security: Requires 'staff:view' permission
        """
        workspace = info.context.workspace
        user = info.context.user

        # Check permission
        if not PermissionService.has_permission(user, workspace, 'staff:view'):
            raise GraphQLError("Insufficient permissions to view role details")

        try:
            return Role.objects.prefetch_related('role_permissions').get(
                id=id,
                workspace=workspace
            )
        except Role.DoesNotExist:
            raise GraphQLError("Role not found")

    def resolve_available_permissions(self, info):
        """
        Resolve all available permissions
        For permission display and role management

        Security: Requires 'staff:view' permission
        """
        workspace = info.context.workspace
        user = info.context.user

        # Check permission
        if not PermissionService.has_permission(user, workspace, 'staff:view'):
            raise GraphQLError("Insufficient permissions to view permissions")

        return Permission.objects.all().order_by('key')

    def resolve_pending_invites(self, info):
        """
        Resolve pending workspace invitations
        Shows invites with status "Pending" in users list

        Security: Requires 'staff:view' permission
        """
        workspace = info.context.workspace
        user = info.context.user

        # Check permission
        if not PermissionService.has_permission(user, workspace, 'staff:view'):
            raise GraphQLError("Insufficient permissions to view pending invites")

        return WorkspaceInvite.get_pending_invites(workspace)

    def resolve_my_permissions(self, info):
        """
        Resolve current user's permissions in workspace
        Used for frontend UI state management (show/hide buttons, features)

        This is cosmetic only - backend always enforces real permissions
        """
        workspace = info.context.workspace
        user = info.context.user

        # Get user's permissions
        permissions = PermissionService.get_user_permissions(user, workspace)
        role = PermissionService.get_workspace_role(user, workspace)

        return MyPermissionsType(
            permissions=permissions,
            role_name=role.name if role else None,
            can_invite_staff='staff:invite' in permissions,
            can_manage_roles='staff:role_change' in permissions,
            can_remove_staff='staff:remove' in permissions
        )

    def resolve_member_permission_summary(self, info, member_id):
        """
        Resolve permission summary grouped by resource
        Used in member details page "Permission summary" section

        Security: Requires 'staff:view' permission
        """
        workspace = info.context.workspace
        user = info.context.user

        # Check permission
        if not PermissionService.has_permission(user, workspace, 'staff:view'):
            raise GraphQLError("Insufficient permissions to view permission summary")

        # Get member
        try:
            membership = Membership.objects.prefetch_related('roles').get(
                id=member_id,
                workspace=workspace
            )
        except Membership.DoesNotExist:
            raise GraphQLError("Member not found")

        # Get member's permissions
        from workspace.core.models import RolePermission
        permission_keys = RolePermission.get_permissions_for_role(membership.role)
        member_permissions = Permission.objects.filter(key__in=permission_keys)

        # Group by resource
        resource_groups = {}
        for perm in member_permissions:
            try:
                resource, action = perm.key.split(':')
                if resource not in resource_groups:
                    resource_groups[resource] = []
                resource_groups[resource].append(perm)
            except:
                continue

        # Get all permissions by resource for comparison
        all_permissions = Permission.objects.all()
        all_resource_counts = {}
        for perm in all_permissions:
            try:
                resource, action = perm.key.split(':')
                all_resource_counts[resource] = all_resource_counts.get(resource, 0) + 1
            except:
                continue

        # Build summary
        summary = []
        resource_name_map = {
            'product': 'Products',
            'order': 'Orders',
            'customer': 'Customers',
            'staff': 'Staff',
            'workspace': 'Workspace',
            'content': 'Content',
            'analytics': 'Analytics',
            'settings': 'Settings'
        }

        for resource, perms in resource_groups.items():
            summary.append(PermissionSummaryType(
                resource=resource_name_map.get(resource, resource.capitalize()),
                total_permissions=all_resource_counts.get(resource, 0),
                granted_permissions=len(perms),
                permissions=perms
            ))

        return summary
