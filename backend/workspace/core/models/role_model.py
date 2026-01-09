# Role Model - Workspace-scoped roles with permission-based access control

import uuid
from django.db import models
from django.core.exceptions import ValidationError


class Role(models.Model):
    """
    Workspace-scoped roles following Shopify/GitHub/Linear architecture

    Key principles:
    - Roles are DATA, not hardcoded logic
    - Each workspace has its own roles (except system roles)
    - System roles (null workspace) are auto-created on workspace creation
    - Permissions are stored in RolePermission junction table
    - Never check role names in authorization - always check permissions
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Workspace scoping (null = system role, used as template)
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='roles',
        null=True,
        blank=True,
        help_text="Workspace this role belongs to. NULL for system/default roles."
    )

    # Role identity
    name = models.CharField(
        max_length=100,
        help_text="Role name (e.g., 'Owner', 'Admin', 'Staff', 'ReadOnly')"
    )

    description = models.TextField(
        blank=True,
        default='',
        help_text="Description of role responsibilities and permissions"
    )

    # System role flag
    is_system = models.BooleanField(
        default=False,
        db_index=True,
        help_text="System roles are auto-provisioned and cannot be deleted"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_roles'
        ordering = ['workspace', 'name']
        unique_together = [
            ['workspace', 'name'],  # Unique role names per workspace
        ]
        indexes = [
            models.Index(fields=['workspace', 'name']),
            models.Index(fields=['is_system']),
            models.Index(fields=['workspace', 'is_system']),
        ]

    def __str__(self):
        scope = "System" if self.is_system else self.workspace.name if self.workspace else "Unscoped"
        return f"{self.name} ({scope})"

    def clean(self):
        """Validate role constraints"""
        super().clean()

        # CRITICAL: System roles must have workspace=None
        if self.is_system and self.workspace is not None:
            raise ValidationError({
                'workspace': 'System roles must have workspace=None'
            })

        # CRITICAL: Non-system roles must have workspace
        if not self.is_system and self.workspace is None:
            raise ValidationError({
                'workspace': 'Non-system roles must belong to a workspace'
            })

    def save(self, *args, **kwargs):
        """Enforce validation before save"""
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of system roles"""
        if self.is_system:
            raise ValidationError('Cannot delete system roles')
        super().delete(*args, **kwargs)

    @property
    def permissions(self):
        """
        Get permissions for this role (compatibility property)
        Returns list of permission keys from RolePermission table

        Note: This is a read-only property for backward compatibility.
        Use RolePermission model to modify permissions.
        """
        from .role_permission_model import RolePermission
        return list(RolePermission.get_permissions_for_role(self))

    def has_permission(self, permission_key):
        """
        Check if role has specific permission

        Args:
            permission_key: Permission key string (e.g., 'product:create')

        Returns:
            bool: True if role has permission
        """
        from .role_permission_model import RolePermission
        return RolePermission.objects.filter(
            role=self,
            permission_key=permission_key
        ).exists()

    def get_permission_keys(self):
        """
        Get all permission keys for this role as a set (optimized for checking)

        Returns:
            Set of permission key strings
        """
        from .role_permission_model import RolePermission
        return RolePermission.get_permissions_for_role(self)

    @classmethod
    def get_default_role_descriptions(cls):
        """
        Get user-friendly descriptions for system roles
        Used in UI to help users understand role capabilities

        Returns:
            Dict mapping role names to description strings
        """
        return {
            'Owner': 'Full control of the workspace including billing, settings, and staff management. Can perform all actions.',
            'Admin': 'Manage all workspace content, products, orders, and staff. Cannot access billing or delete the workspace.',
            'Staff': 'Create and manage products, orders, and customers. Cannot manage other staff members or workspace settings.',
            'ReadOnly': 'View-only access to all workspace data. Cannot create, edit, or delete anything.',
        }

    @classmethod
    def get_default_role_permissions(cls):
        """
        Get default permission sets for system roles
        Following Shopify/GitHub pattern

        Returns:
            Dict mapping role names to permission key lists
        """
        return {
            'Owner': [
                # Full workspace control
                'workspace:manage',
                'workspace:settings',
                'workspace:billing',

                # Staff management
                'staff:invite',
                'staff:remove',
                'staff:role_change',
                'staff:view',

                # Content
                'content:create',
                'content:update',
                'content:delete',
                'content:view',

                # Products
                'product:create',
                'product:update',
                'product:delete',
                'product:view',

                # Categories
                'category:create',
                'category:update',
                'category:delete',
                'category:view',

                # Discounts
                'discount:create',
                'discount:update',
                'discount:delete',
                'discount:view',

                # Orders
                'order:create',
                'order:view',
                'order:update',
                'order:refund',
                'order:cancel',

                # Customers
                'customer:create',
                'customer:view',
                'customer:update',
                'customer:delete',

                # Analytics & Settings
                'analytics:view',
                'settings:view',
                'settings:update',
            ],
            'Admin': [
                # Staff management (cannot modify owner)
                'staff:invite',
                'staff:remove',
                'staff:role_change',
                'staff:view',

                # Content
                'content:create',
                'content:update',
                'content:delete',
                'content:view',

                # Products
                'product:create',
                'product:update',
                'product:delete',
                'product:view',

                # Categories
                'category:create',
                'category:update',
                'category:delete',
                'category:view',

                # Discounts
                'discount:create',
                'discount:update',
                'discount:delete',
                'discount:view',

                # Orders
                'order:create',
                'order:view',
                'order:update',
                'order:refund',
                'order:cancel',

                # Customers
                'customer:create',
                'customer:view',
                'customer:update',
                'customer:delete',

                # Analytics & Settings
                'analytics:view',
                'settings:view',
                'settings:update',
            ],
            'Staff': [
                # Content management
                'content:create',
                'content:update',
                'content:view',

                # Products
                'product:create',
                'product:update',
                'product:view',

                # Categories
                'category:create',
                'category:update',
                'category:view',

                # Discounts
                'discount:create',
                'discount:update',
                'discount:view',

                # Orders
                'order:create',
                'order:view',
                'order:update',

                # Customers
                'customer:create',
                'customer:view',
                'customer:update',

                # Settings (view only)
                'settings:view',
            ],
            'ReadOnly': [
                # View only access
                'content:view',
                'product:view',
                'category:view',
                'discount:view',
                'order:view',
                'customer:view',
                'analytics:view',
                'settings:view',
                'staff:view',
            ],
        }

    @classmethod
    def create_system_roles(cls):
        """
        Create system roles (templates for workspace role provisioning)
        Idempotent - safe to run multiple times

        Returns:
            List of created Role instances
        """
        from .role_permission_model import RolePermission

        role_permissions_map = cls.get_default_role_permissions()
        role_descriptions = cls.get_default_role_descriptions()
        created_roles = []

        for role_name, permission_keys in role_permissions_map.items():
            # Create or get system role with description
            role, created = cls.objects.get_or_create(
                workspace=None,
                name=role_name,
                defaults={
                    'is_system': True,
                    'description': role_descriptions.get(role_name, '')
                }
            )

            # Update description if role already exists
            if not created and role.description != role_descriptions.get(role_name, ''):
                role.description = role_descriptions.get(role_name, '')
                role.save(skip_validation=True)

            if created:
                created_roles.append(role)

            # Assign permissions (replaces existing)
            RolePermission.assign_permissions_to_role(
                role=role,
                permission_keys=permission_keys,
                allow_system=True
            )

        return created_roles

    @classmethod
    def provision_workspace_roles(cls, workspace):
        """
        Auto-provision default roles for a new workspace
        Copies system roles to workspace-specific roles

        Args:
            workspace: Workspace instance

        Returns:
            Dict mapping role names to Role instances
        """
        from django.db import transaction
        from .role_permission_model import RolePermission

        # Get system roles (templates)
        system_roles = cls.objects.filter(workspace=None, is_system=True)

        if not system_roles.exists():
            raise ValidationError(
                "System roles not found. Run Role.create_system_roles() first."
            )

        workspace_roles = {}

        with transaction.atomic():
            for system_role in system_roles:
                # Create workspace-specific role (copy description from system role)
                workspace_role, created = cls.objects.get_or_create(
                    workspace=workspace,
                    name=system_role.name,
                    defaults={
                        'is_system': False,
                        'description': system_role.description
                    }
                )

                if created:
                    # Copy permissions from system role
                    system_permissions = RolePermission.get_permissions_for_role(system_role)
                    RolePermission.assign_permissions_to_role(
                        role=workspace_role,
                        permission_keys=list(system_permissions),
                        allow_system=False
                    )

                workspace_roles[system_role.name] = workspace_role

        return workspace_roles