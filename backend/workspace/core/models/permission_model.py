# Permission Model - Action-based permissions for RBAC system

from django.db import models
from django.core.exceptions import ValidationError


class Permission(models.Model):
    """
    Global permissions catalog using action-based keys
    Following industry standard: resource:action pattern

    Examples:
        - product:create
        - product:update
        - order:refund
        - staff:invite
        - staff:remove
    """

    # Primary key is the permission key itself
    key = models.CharField(
        max_length=100,
        primary_key=True,
        help_text="Permission key in format 'resource:action' (e.g., 'product:create')"
    )
    description = models.TextField(
        help_text="Human-readable description of what this permission allows"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_permissions'
        ordering = ['key']
        indexes = [
            models.Index(fields=['key']),
        ]

    def __str__(self):
        return self.key

    def clean(self):
        """Validate permission key format"""
        super().clean()

        # Enforce resource:action format
        if ':' not in self.key:
            raise ValidationError({
                'key': 'Permission key must follow "resource:action" format (e.g., "product:create")'
            })

        parts = self.key.split(':')
        if len(parts) != 2:
            raise ValidationError({
                'key': 'Permission key must have exactly one colon separator'
            })

        resource, action = parts
        if not resource or not action:
            raise ValidationError({
                'key': 'Both resource and action must be non-empty'
            })

    def save(self, *args, **kwargs):
        """Enforce validation before save"""
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_default_permissions(cls):
        """
        Get default permissions to be created on system initialization
        These are the core permissions available in the system
        """
        return [
            # Workspace management
            ('workspace:manage', 'Full workspace management including deletion and settings'),
            ('workspace:settings', 'Manage workspace settings and preferences'),
            ('workspace:billing', 'Access and manage billing and subscription'),

            # Member management
            ('staff:invite', 'Invite new members to workspace'),
            ('staff:remove', 'Remove members from workspace'),
            ('staff:role_change', 'Change member roles'),
            ('staff:view', 'View workspace members and their roles'),

            # Content management (generic)
            ('content:create', 'Create new content'),
            ('content:update', 'Update existing content'),
            ('content:delete', 'Delete content'),
            ('content:view', 'View content'),

            # Product management (e-commerce)
            ('product:create', 'Create new products'),
            ('product:update', 'Update product information'),
            ('product:delete', 'Delete products'),
            ('product:view', 'View products'),

            # Category management
            ('category:create', 'Create new categories'),
            ('category:update', 'Update category information'),
            ('category:delete', 'Delete categories'),
            ('category:view', 'View categories'),

            # Discount management
            ('discount:create', 'Create new discounts'),
            ('discount:update', 'Update discount information'),
            ('discount:delete', 'Delete discounts'),
            ('discount:view', 'View discounts'),

            # Order management (e-commerce)
            ('order:create', 'Create new orders'),
            ('order:view', 'View orders'),
            ('order:update', 'Update order status'),
            ('order:refund', 'Process refunds'),
            ('order:cancel', 'Cancel orders'),

            # Customer management
            ('customer:create', 'Create new customers'),
            ('customer:view', 'View customer information'),
            ('customer:update', 'Update customer information'),
            ('customer:delete', 'Delete customers'),

            # Analytics
            ('analytics:view', 'View analytics and reports'),

            # Settings management
            ('settings:view', 'View workspace settings'),
            ('settings:update', 'Update workspace settings'),
        ]

    @classmethod
    def seed_default_permissions(cls):
        """
        Seed database with default permissions
        Safe to run multiple times (idempotent)
        """
        created_count = 0

        for key, description in cls.get_default_permissions():
            permission, created = cls.objects.get_or_create(
                key=key,
                defaults={'description': description}
            )
            if created:
                created_count += 1

        return created_count
