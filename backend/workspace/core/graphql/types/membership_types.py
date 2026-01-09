"""
Membership & Roles GraphQL Types
Production-ready types for workspace staff management following Shopify pattern
"""

import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from workspace.core.models import Membership, Role, Permission, WorkspaceInvite, Workspace
from workspace.store.graphql.types.common_types import BaseConnection

User = get_user_model()


class UserType(DjangoObjectType):
    """
    GraphQL type for User model
    Minimal user information for staff management
    """
    id = graphene.ID(required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')

    def resolve_id(self, info):
        """Return user ID as string"""
        return str(self.id)


class WorkspaceType(DjangoObjectType):
    """
    GraphQL type for Workspace model
    Minimal workspace information
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Workspace
        fields = ('id', 'name')

    def resolve_id(self, info):
        """Return workspace ID as string"""
        return str(self.id)


class PermissionType(DjangoObjectType):
    """
    GraphQL type for Permission model
    Represents individual permissions like 'product:create', 'order:refund'
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Permission
        fields = ('key', 'description', 'created_at', 'updated_at')

    # Display name for UI (e.g., "product:create" -> "Create Products")
    display_name = graphene.String()

    def resolve_display_name(self, info):
        """Generate human-readable permission name"""
        # Convert "product:create" to "Create Products"
        try:
            resource, action = self.key.split(':')
            action_map = {
                'create': 'Create',
                'update': 'Update',
                'delete': 'Delete',
                'view': 'View',
                'manage': 'Manage'
            }
            resource_map = {
                'product': 'Products',
                'order': 'Orders',
                'customer': 'Customers',
                'staff': 'Staff',
                'workspace': 'Workspace',
                'content': 'Content',
                'analytics': 'Analytics',
                'settings': 'Settings'
            }
            action_text = action_map.get(action, action.capitalize())
            resource_text = resource_map.get(resource, resource.capitalize())
            return f"{action_text} {resource_text}"
        except:
            return self.key


class RoleType(DjangoObjectType):
    """
    GraphQL type for Role model
    Represents workspace roles (Owner, Admin, Staff, ReadOnly)
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'is_system', 'created_at', 'updated_at')
        interfaces = (graphene.relay.Node,)

    # Related permissions for this role
    permissions = graphene.List(PermissionType)
    permission_count = graphene.Int()
    member_count = graphene.Int()

    def resolve_permissions(self, info):
        """Get all permissions for this role"""
        from workspace.core.models import RolePermission
        permission_keys = RolePermission.get_permissions_for_role(self)
        return Permission.objects.filter(key__in=permission_keys).order_by('key')

    def resolve_permission_count(self, info):
        """Count of permissions for this role"""
        from workspace.core.models import RolePermission
        return RolePermission.objects.filter(role=self).count()

    def resolve_member_count(self, info):
        """Count of members with this role"""
        return self.memberships.filter(status=Membership.Status.ACTIVE).count()


class WorkspaceMemberType(DjangoObjectType):
    """
    GraphQL type for Membership model
    Represents workspace members with their roles and status
    Following Shopify pattern (supports multiple roles): User | Status | Roles
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Membership
        fields = (
            'id', 'user', 'workspace', 'roles', 'status',
            'invited_by', 'suspended_at', 'suspended_by', 'suspension_reason',
            'removed_at', 'removed_by',
            'joined_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    # User details
    user_email = graphene.String()
    user_name = graphene.String()

    # Role details (compatibility - returns first role)
    role = graphene.Field(RoleType)
    role_names = graphene.List(graphene.String)
    all_permissions = graphene.List(PermissionType)

    # Status helpers
    is_active = graphene.Boolean()
    is_pending = graphene.Boolean()
    is_suspended = graphene.Boolean()
    is_removed = graphene.Boolean()

    def resolve_user_email(self, info):
        """User's email"""
        return self.user.email

    def resolve_user_name(self, info):
        """User's display name"""
        return self.user.get_full_name() or self.user.email

    def resolve_role(self, info):
        """Primary role (first role) for backward compatibility"""
        return self.roles.first()

    def resolve_role_names(self, info):
        """All role names"""
        return [role.name for role in self.roles.all()]

    def resolve_all_permissions(self, info):
        """Get union of permissions from all assigned roles"""
        permission_keys = self.permissions  # Uses membership.permissions property
        return Permission.objects.filter(key__in=permission_keys).order_by('key')

    def resolve_is_active(self, info):
        """Check if membership is active"""
        return self.status == Membership.Status.ACTIVE

    def resolve_is_pending(self, info):
        """Check if membership is pending (invited but not accepted)"""
        return self.status == Membership.Status.INVITED

    def resolve_is_suspended(self, info):
        """Check if membership is suspended"""
        return self.status == Membership.Status.SUSPENDED

    def resolve_is_removed(self, info):
        """Check if membership is removed"""
        return self.status == Membership.Status.REMOVED


class WorkspaceInviteType(DjangoObjectType):
    """
    GraphQL type for WorkspaceInvite model
    Represents pending invitations (supports multiple roles like Shopify)
    """
    id = graphene.ID(required=True)

    class Meta:
        model = WorkspaceInvite
        fields = (
            'id', 'email', 'roles', 'invited_by', 'status',
            'expires_at', 'created_at', 'accepted_at'
        )
        interfaces = (graphene.relay.Node,)

    # Inviter details (helper field for convenience)
    invited_by_email = graphene.String()

    # Role details (helper fields)
    role = graphene.Field(RoleType)  # Backward compatibility
    role_names = graphene.List(graphene.String)

    # Status helpers
    is_valid = graphene.Boolean()
    is_expired = graphene.Boolean()

    def resolve_invited_by_email(self, info):
        """Email of person who sent invite"""
        return self.invited_by.email if self.invited_by else None

    def resolve_role(self, info):
        """Primary role (first role) for backward compatibility"""
        return self.roles.first()

    def resolve_role_names(self, info):
        """All role names for this invite"""
        return [role.name for role in self.roles.all()]

    def resolve_is_valid(self, info):
        """Check if invite is still valid"""
        return self.is_valid

    def resolve_is_expired(self, info):
        """Check if invite has expired"""
        return self.is_expired


class WorkspaceMemberConnection(graphene.relay.Connection):
    """
    Connection for workspace members with pagination
    """
    class Meta:
        node = WorkspaceMemberType

    total_count = graphene.Int()
    active_count = graphene.Int()
    pending_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        """Total members count"""
        return self.iterable.count()

    def resolve_active_count(self, info, **kwargs):
        """Active members count"""
        return self.iterable.filter(status=Membership.Status.ACTIVE).count()

    def resolve_pending_count(self, info, **kwargs):
        """Pending invites count"""
        return self.iterable.filter(status=Membership.Status.INVITED).count()


class RoleConnection(graphene.relay.Connection):
    """
    Connection for roles with pagination
    """
    class Meta:
        node = RoleType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        """Total roles count"""
        return self.iterable.count()


class PermissionSummaryType(graphene.ObjectType):
    """
    Type for permission summary (used in member details page)
    Groups permissions by resource for display
    """
    resource = graphene.String()  # e.g., "Orders", "Products"
    total_permissions = graphene.Int()
    granted_permissions = graphene.Int()
    permissions = graphene.List(PermissionType)


class MyPermissionsType(graphene.ObjectType):
    """
    Type for current user's permissions in workspace
    Used for frontend UI state management
    """
    permissions = graphene.List(graphene.String)
    role_name = graphene.String()
    can_invite_staff = graphene.Boolean()
    can_manage_roles = graphene.Boolean()
    can_remove_staff = graphene.Boolean()
