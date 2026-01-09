# RolePermission Model - Many-to-many relationship between Roles and Permissions

import uuid
import logging
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class RolePermission(models.Model):
    """
    Junction table linking Roles to Permissions
    Defines which permissions each role has

    This is the source of truth for role capabilities.
    Never check role names in code - always check permissions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        'workspace_core.Role',
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    permission_key = models.CharField(
        max_length=100,
        help_text="Permission key from Permission model"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_role_permissions'
        unique_together = ['role', 'permission_key']
        ordering = ['permission_key']
        indexes = [
            models.Index(fields=['role', 'permission_key']),
            models.Index(fields=['permission_key']),
        ]

    def __str__(self):
        return f"{self.role.name} -> {self.permission_key}"

    def clean(self):
        """Validate permission exists and prevent system role modification"""
        super().clean()

        # Ensure permission exists
        from .permission_model import Permission
        if not Permission.objects.filter(key=self.permission_key).exists():
            raise ValidationError({
                'permission_key': f'Permission "{self.permission_key}" does not exist'
            })

        # CRITICAL: Prevent modification of system role permissions via direct model save
        # System roles should only be modified through RoleService with proper authorization
        if self.role.is_system and not getattr(self, '_allow_system_role_modification', False):
            raise ValidationError({
                'role': 'Cannot directly modify system role permissions. Use RoleService.'
            })

    def save(self, *args, **kwargs):
        """Enforce validation before save"""
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_permissions_for_role(cls, role):
        """
        Get all permission keys for a given role
        Optimized for performance with caching in mind

        Args:
            role: Role instance

        Returns:
            Set of permission key strings
        """
        return set(
            cls.objects.filter(role=role)
            .values_list('permission_key', flat=True)
        )

    @classmethod
    def assign_permissions_to_role(cls, role, permission_keys, allow_system=False):
        """
        Assign multiple permissions to a role (bulk operation)
        Replaces existing permissions completely

        Args:
            role: Role instance
            permission_keys: List of permission key strings
            allow_system: Allow modification of system roles (internal use only)

        Returns:
            Number of permissions assigned

        Raises:
            ValidationError: If inputs are invalid or permissions don't exist
            TypeError: If inputs are wrong type
        """
        from django.db import transaction
        from .permission_model import Permission

        # Input validation - fail fast
        if role is None:
            raise ValidationError("Role cannot be None")

        if not hasattr(permission_keys, '__iter__') or isinstance(permission_keys, (str, bytes)):
            raise TypeError("permission_keys must be an iterable (list, set, tuple)")

        # Convert to list and deduplicate
        permission_keys = list(set(permission_keys))

        # Validate all permissions exist
        existing_permissions = set(
            Permission.objects.filter(key__in=permission_keys)
            .values_list('key', flat=True)
        )

        invalid_permissions = set(permission_keys) - existing_permissions
        if invalid_permissions:
            raise ValidationError(
                f"Invalid permissions: {', '.join(sorted(invalid_permissions))}"
            )

        # Prevent system role modification unless explicitly allowed
        if role.is_system and not allow_system:
            raise ValidationError(
                "Cannot modify system role permissions. Use RoleService with proper authorization."
            )

        # Log security-critical operation
        if role.is_system:
            logger.warning(
                f"System role modification: Assigning {len(permission_keys)} permissions to role '{role.name}' (ID: {role.id})",
                extra={
                    'role_id': str(role.id),
                    'role_name': role.name,
                    'permission_count': len(permission_keys),
                    'allow_system': allow_system
                }
            )

        with transaction.atomic():
            # CRITICAL: Create new permissions FIRST, then delete old ones
            # This prevents permission loss if bulk_create fails
            # Old permissions remain until new ones are successfully created

            role_permissions = [
                cls(role=role, permission_key=key)
                for key in permission_keys
            ]

            # Bulk create for performance (bypasses save() and clean())
            # Use ignore_conflicts to handle race conditions gracefully
            cls.objects.bulk_create(role_permissions, ignore_conflicts=True)

            # Now safely delete old permissions that are not in new set
            # Keep only the permissions we just created
            cls.objects.filter(role=role).exclude(permission_key__in=permission_keys).delete()

        return len(permission_keys)

    @classmethod
    def add_permission_to_role(cls, role, permission_key, allow_system=False):
        """
        Add a single permission to a role (idempotent)
        Thread-safe using database-level uniqueness constraint

        Args:
            role: Role instance
            permission_key: Permission key string
            allow_system: Allow modification of system roles (internal use only)

        Returns:
            RolePermission instance (either existing or newly created)

        Raises:
            ValidationError: If inputs invalid or permission doesn't exist
        """
        from .permission_model import Permission

        # Input validation - fail fast
        if role is None:
            raise ValidationError("Role cannot be None")

        if not permission_key or not isinstance(permission_key, str):
            raise ValidationError("permission_key must be a non-empty string")

        # Validate permission exists
        if not Permission.objects.filter(key=permission_key).exists():
            raise ValidationError(f'Permission "{permission_key}" does not exist')

        # Prevent system role modification unless explicitly allowed
        if role.is_system and not allow_system:
            raise ValidationError(
                "Cannot modify system role permissions. Use RoleService with proper authorization."
            )

        # Log security-critical operation
        if role.is_system and allow_system:
            logger.warning(
                f"System role modification: Adding permission '{permission_key}' to role '{role.name}' (ID: {role.id})",
                extra={
                    'role_id': str(role.id),
                    'role_name': role.name,
                    'permission_key': permission_key,
                    'allow_system': allow_system
                }
            )

        # Race condition safe: Try to create, handle duplicate gracefully
        try:
            role_permission = cls(role=role, permission_key=permission_key)
            if role.is_system and allow_system:
                role_permission.save(skip_validation=True)
            else:
                role_permission.save()
            return role_permission

        except IntegrityError:
            # Another thread created it between our check and create
            # Return the existing record (idempotent behavior)
            return cls.objects.get(role=role, permission_key=permission_key)

    @classmethod
    def remove_permission_from_role(cls, role, permission_key, allow_system=False):
        """
        Remove a permission from a role (idempotent)

        Args:
            role: Role instance
            permission_key: Permission key string
            allow_system: Allow modification of system roles (internal use only)

        Returns:
            int: Number of permissions removed (0 or 1)

        Raises:
            ValidationError: If inputs invalid or system role without authorization
        """
        # Input validation - fail fast
        if role is None:
            raise ValidationError("Role cannot be None")

        if not permission_key or not isinstance(permission_key, str):
            raise ValidationError("permission_key must be a non-empty string")

        # Prevent system role modification unless explicitly allowed
        if role.is_system and not allow_system:
            raise ValidationError(
                "Cannot modify system role permissions. Use RoleService with proper authorization."
            )

        # Log security-critical operation
        if role.is_system and allow_system:
            logger.warning(
                f"System role modification: Removing permission '{permission_key}' from role '{role.name}' (ID: {role.id})",
                extra={
                    'role_id': str(role.id),
                    'role_name': role.name,
                    'permission_key': permission_key,
                    'allow_system': allow_system
                }
            )

        deleted_count, _ = cls.objects.filter(role=role, permission_key=permission_key).delete()
        return deleted_count
