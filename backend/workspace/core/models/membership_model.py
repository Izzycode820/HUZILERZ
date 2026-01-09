# Membership Model - Many-to-Many relationship between Users and Workspaces

import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Membership(models.Model):
    """
    Many-to-many link between Users and Workspaces with roles
    Handles multi-tenancy user access control

    Key principles (from guide):
    - Users do NOT have roles. Memberships have roles.
    - Roles belong to memberships.
    - Authorization is evaluated per request via membership -> role -> permissions.
    - Never bypass permission checks with owner logic.
    """

    # Status choices following industry standard invitation flow
    class Status(models.TextChoices):
        INVITED = 'INVITED', 'Invited'
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        REMOVED = 'REMOVED', 'Removed'  # Permanent removal, cannot be reactivated

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    roles = models.ManyToManyField(
        'workspace_core.Role',
        related_name='memberships',
        help_text="Roles assigned to this membership (supports multiple roles per user)"
    )

    # Status (state machine: INVITED -> ACTIVE -> SUSPENDED or REMOVED)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="Membership status in invitation lifecycle"
    )

    # Suspension tracking
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suspended_memberships',
        help_text="User who suspended this membership"
    )
    suspension_reason = models.TextField(blank=True, default='')

    # Removal tracking (permanent)
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='removed_memberships',
        help_text="User who removed this membership"
    )

    # Invitation tracking
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_memberships',
        help_text="User who invited this member"
    )

    # Metadata
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_memberships'
        unique_together = ['user', 'workspace']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['workspace', 'user', 'status']),
        ]

    def __str__(self):
        role_names = ', '.join([role.name for role in self.roles.all()]) if self.pk else 'No roles'
        return f"{self.user.email} - {self.workspace.name} ({role_names}) [{self.status}]"

    def clean(self):
        """Validate membership constraints"""
        super().clean()

        # Note: ManyToMany validation happens after save, so we validate in add_role() method instead

    def save(self, *args, **kwargs):
        """Enforce validation before save"""
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Backward compatibility property for is_active checks"""
        return self.status == self.Status.ACTIVE

    @property
    def permissions(self):
        """
        Get user permissions in this workspace via all assigned roles
        Returns union of permission keys from all roles

        IMPORTANT: This is read-only. Never check role names in code.
        Always check permissions.
        """
        if not self.pk:
            return set()

        # Aggregate permissions from all roles (union)
        all_permissions = set()
        for role in self.roles.all():
            all_permissions.update(role.get_permission_keys())
        return all_permissions

    def has_permission(self, permission_key):
        """
        Check if membership has specific permission across any of its roles

        Args:
            permission_key: Permission key string (e.g., 'product:create')

        Returns:
            bool: True if ANY of membership's roles has permission AND membership is ACTIVE

        CRITICAL: Only ACTIVE memberships can use permissions
        """
        # Only active memberships can use permissions
        if self.status != self.Status.ACTIVE:
            return False

        if not self.pk:
            return False

        # Check if ANY role has the permission
        return permission_key in self.permissions

    def activate(self):
        """
        Activate membership (used when accepting invitation)
        State transition: INVITED -> ACTIVE
        """
        if self.status == self.Status.INVITED:
            self.status = self.Status.ACTIVE
            self.save(update_fields=['status', 'updated_at'])
        else:
            raise ValidationError(
                f'Cannot activate membership in {self.status} state'
            )

    def suspend(self, suspended_by=None, reason=''):
        """
        Suspend membership (revoke access without deletion)
        State transition: ACTIVE -> SUSPENDED

        Args:
            suspended_by: User performing the suspension
            reason: Reason for suspension (optional)

        Raises:
            ValidationError: If membership is not in ACTIVE state
        """
        from django.utils import timezone

        if self.status == self.Status.ACTIVE:
            self.status = self.Status.SUSPENDED
            self.suspended_at = timezone.now()
            self.suspended_by = suspended_by
            self.suspension_reason = reason
            self.save(update_fields=['status', 'suspended_at', 'suspended_by', 'suspension_reason', 'updated_at'])
        else:
            raise ValidationError(
                f'Cannot suspend membership in {self.status} state. Must be ACTIVE.'
            )

    def reactivate(self):
        """
        Reactivate suspended membership
        State transition: SUSPENDED -> ACTIVE
        Clears suspension tracking fields

        Raises:
            ValidationError: If membership is not in SUSPENDED state
        """
        if self.status == self.Status.SUSPENDED:
            self.status = self.Status.ACTIVE
            self.suspended_at = None
            self.suspended_by = None
            self.suspension_reason = ''
            self.save(update_fields=['status', 'suspended_at', 'suspended_by', 'suspension_reason', 'updated_at'])
        else:
            raise ValidationError(
                f'Cannot reactivate membership in {self.status} state. Must be SUSPENDED.'
            )

    def remove(self, removed_by=None):
        """
        Permanently remove membership (cannot be reactivated)
        State transition: ACTIVE or SUSPENDED -> REMOVED

        Args:
            removed_by: User performing the removal

        Raises:
            ValidationError: If membership is already REMOVED
        """
        from django.utils import timezone

        if self.status in [self.Status.ACTIVE, self.Status.SUSPENDED]:
            self.status = self.Status.REMOVED
            self.removed_at = timezone.now()
            self.removed_by = removed_by
            self.save(update_fields=['status', 'removed_at', 'removed_by', 'updated_at'])
        else:
            raise ValidationError(
                f'Cannot remove membership in {self.status} state.'
            )

    def add_role(self, role):
        """
        Add role to membership with validation
        Thread-safe via database constraints

        Args:
            role: Role instance to add

        Raises:
            ValidationError: If role is invalid (system role, wrong workspace)
        """
        if not self.pk:
            raise ValidationError("Cannot add role to unsaved membership")

        # CRITICAL: Validate role belongs to same workspace
        if role.workspace != self.workspace:
            raise ValidationError(
                f'Role must belong to workspace {self.workspace.name}'
            )

        # CRITICAL: Cannot use system roles in memberships
        if role.is_system:
            raise ValidationError(
                'Cannot assign system roles to memberships. Use workspace-specific roles.'
            )

        # Add role (idempotent - won't duplicate)
        self.roles.add(role)

    def remove_role(self, role):
        """
        Remove role from membership

        Args:
            role: Role instance to remove

        Raises:
            ValidationError: If removing would leave membership with no roles
        """
        if not self.pk:
            raise ValidationError("Cannot remove role from unsaved membership")

        # CRITICAL: Don't leave membership without any roles
        if self.roles.count() <= 1:
            raise ValidationError(
                "Cannot remove last role. Membership must have at least one role."
            )

        self.roles.remove(role)

    def set_roles(self, role_ids):
        """
        Replace all roles atomically
        Used when changing multiple roles at once

        Args:
            role_ids: List of role IDs to assign

        Raises:
            ValidationError: If any role is invalid
        """
        from django.db import transaction
        from .role_model import Role

        if not self.pk:
            raise ValidationError("Cannot set roles on unsaved membership")

        if not role_ids:
            raise ValidationError("Must provide at least one role")

        # Get and validate all roles
        roles = Role.objects.filter(id__in=role_ids)

        if roles.count() != len(role_ids):
            raise ValidationError("One or more roles not found")

        # Validate all roles
        for role in roles:
            if role.workspace != self.workspace:
                raise ValidationError(
                    f'Role {role.name} does not belong to workspace {self.workspace.name}'
                )
            if role.is_system:
                raise ValidationError(
                    f'Cannot assign system role {role.name} to membership'
                )

        # Atomic replacement
        with transaction.atomic():
            self.roles.set(roles)

    @classmethod
    def get_active_memberships(cls, workspace):
        """Get all active memberships for a workspace"""
        return cls.objects.filter(
            workspace=workspace,
            status=cls.Status.ACTIVE
        ).select_related('user').prefetch_related('roles')

    @classmethod
    def get_user_active_membership(cls, user, workspace):
        """
        Get user's active membership in workspace
        Returns None if no active membership exists
        """
        try:
            return cls.objects.prefetch_related('roles').get(
                user=user,
                workspace=workspace,
                status=cls.Status.ACTIVE
            )
        except cls.DoesNotExist:
            return None