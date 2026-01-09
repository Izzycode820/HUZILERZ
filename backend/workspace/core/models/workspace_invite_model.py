# WorkspaceInvite Model - Invitation system for workspace member onboarding

import uuid
import secrets
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class WorkspaceInvite(models.Model):
    """
    Invitation system following industry standard pattern (Shopify/GitHub/Linear)

    State machine:
        CREATED -> SENT -> ACCEPTED -> CONSUMED
                        -> EXPIRED
                        -> CANCELLED

    Key principles:
    - No membership exists before acceptance
    - Role is fixed at invite time
    - Invite token is single-use
    - Invites expire after configurable period (default 7 days)
    """

    # Invite status choices
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        SENT = 'SENT', 'Sent'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        CONSUMED = 'CONSUMED', 'Consumed'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Workspace and inviter
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='invites'
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invites',
        help_text="User who sent the invitation"
    )

    # Invitee information
    email = models.EmailField(
        help_text="Email address of person being invited"
    )

    # Roles to assign upon acceptance (supports multiple roles like Shopify)
    roles = models.ManyToManyField(
        'workspace_core.Role',
        related_name='invites',
        help_text="Roles to assign when invite is accepted (supports multiple)"
    )

    # Invite token (secure, single-use)
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Secure token for accepting invitation"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True
    )

    # Expiration
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="When this invitation expires"
    )

    # Acceptance tracking
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When invitation was accepted"
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invites',
        help_text="User who accepted (may differ from invited email for existing users)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_core'
        db_table = 'workspace_invites'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'email', 'status']),
            models.Index(fields=['token']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['workspace', 'status']),
        ]

    def __str__(self):
        role_names = ', '.join([role.name for role in self.roles.all()]) if self.pk else 'No roles'
        return f"Invite: {self.email} -> {self.workspace.name} as {role_names} [{self.status}]"

    def clean(self):
        """Validate invite constraints"""
        super().clean()

        # Note: ManyToMany validation happens after save, so we validate in set_roles() method instead

        # Validate email not already member (if creating new invite)
        if not self.pk:
            from .membership_model import Membership
            if Membership.objects.filter(
                workspace=self.workspace,
                user__email=self.email,
                status=Membership.Status.ACTIVE
            ).exists():
                raise ValidationError({
                    'email': f'User {self.email} is already an active member of this workspace'
                })

    def save(self, *args, **kwargs):
        """Enforce validation and generate token"""
        # Generate secure token if not set
        if not self.token:
            self.token = self._generate_secure_token()

        # Set default expiration if not set (7 days from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)

        if not kwargs.pop('skip_validation', False):
            self.full_clean()

        super().save(*args, **kwargs)

    @staticmethod
    def _generate_secure_token():
        """
        Generate cryptographically secure token
        Returns 64-character hex string (256 bits of entropy)
        """
        return secrets.token_hex(32)

    @property
    def is_expired(self):
        """Check if invitation has expired"""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if invitation is valid for acceptance"""
        return (
            self.status in [self.Status.CREATED, self.Status.SENT] and
            not self.is_expired
        )

    def set_roles(self, role_ids):
        """
        Set roles for this invitation with validation
        Must be called after save()

        Args:
            role_ids: List of role IDs to assign

        Raises:
            ValidationError: If any role is invalid
        """
        from .role_model import Role

        if not self.pk:
            raise ValidationError("Cannot set roles on unsaved invite")

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
                    f'Cannot use system role {role.name} for invitations'
                )

        # Set roles
        self.roles.set(roles)

    def mark_sent(self):
        """
        Mark invitation as sent
        State transition: CREATED -> SENT
        """
        if self.status != self.Status.CREATED:
            raise ValidationError(
                f'Cannot mark invite as sent in {self.status} state'
            )

        self.status = self.Status.SENT
        self.save(update_fields=['status', 'updated_at'])

    def accept(self, user):
        """
        Accept invitation and create membership
        State transition: SENT -> ACCEPTED -> CONSUMED

        Args:
            user: User instance accepting the invitation

        Returns:
            Membership instance created

        Raises:
            ValidationError: If invite is invalid or already used
        """
        from django.db import transaction
        from .membership_model import Membership

        # Validation
        if not self.is_valid:
            if self.is_expired:
                self.status = self.Status.EXPIRED
                self.save(update_fields=['status', 'updated_at'])
                raise ValidationError('Invitation has expired')
            raise ValidationError(f'Invitation is not valid (status: {self.status})')

        # CRITICAL: Prevent duplicate acceptance
        if self.status in [self.Status.ACCEPTED, self.Status.CONSUMED]:
            raise ValidationError('Invitation has already been accepted')

        # CRITICAL: Check if user already has membership
        existing_membership = Membership.objects.filter(
            workspace=self.workspace,
            user=user
        ).first()

        if existing_membership:
            if existing_membership.status == Membership.Status.ACTIVE:
                raise ValidationError('User is already an active member of this workspace')
            else:
                # Reactivate suspended membership and update roles
                existing_membership.status = Membership.Status.ACTIVE
                existing_membership.save()

                # Set roles from invitation
                role_ids = list(self.roles.values_list('id', flat=True))
                existing_membership.set_roles(role_ids)

                # Mark invite as consumed
                self.status = self.Status.CONSUMED
                self.accepted_at = timezone.now()
                self.accepted_by = user
                self.save(update_fields=['status', 'accepted_at', 'accepted_by', 'updated_at'])

                return existing_membership

        # Create new membership
        with transaction.atomic():
            # Create membership (without roles first, then add via M2M)
            membership = Membership.objects.create(
                user=user,
                workspace=self.workspace,
                status=Membership.Status.ACTIVE,
                invited_by=self.invited_by
            )

            # Assign roles from invitation
            role_ids = list(self.roles.values_list('id', flat=True))
            membership.set_roles(role_ids)

            # Update invite status
            self.status = self.Status.CONSUMED
            self.accepted_at = timezone.now()
            self.accepted_by = user
            self.save(update_fields=['status', 'accepted_at', 'accepted_by', 'updated_at'])

        return membership

    def cancel(self):
        """
        Cancel invitation
        State transition: CREATED|SENT -> CANCELLED
        """
        if self.status not in [self.Status.CREATED, self.Status.SENT]:
            raise ValidationError(
                f'Cannot cancel invite in {self.status} state'
            )

        self.status = self.Status.CANCELLED
        self.save(update_fields=['status', 'updated_at'])

    def resend(self):
        """
        Resend invitation (extends expiration)
        Can only resend SENT or EXPIRED invites
        """
        if self.status not in [self.Status.SENT, self.Status.EXPIRED]:
            raise ValidationError(
                f'Cannot resend invite in {self.status} state'
            )

        # Extend expiration
        self.expires_at = timezone.now() + timedelta(days=7)
        self.status = self.Status.SENT
        self.save(update_fields=['expires_at', 'status', 'updated_at'])

    @classmethod
    def get_pending_invites(cls, workspace):
        """Get all pending (valid, not expired) invites for workspace"""
        return cls.objects.filter(
            workspace=workspace,
            status__in=[cls.Status.CREATED, cls.Status.SENT],
            expires_at__gt=timezone.now()
        ).prefetch_related('roles').select_related('invited_by')

    @classmethod
    def get_by_token(cls, token):
        """
        Get invite by token
        Returns None if not found
        """
        try:
            return cls.objects.select_related('workspace').prefetch_related('roles').get(token=token)
        except cls.DoesNotExist:
            return None

    @classmethod
    def cleanup_expired_invites(cls):
        """
        Mark expired invites as EXPIRED
        Should be run periodically (e.g., daily cron job)

        Returns:
            Number of invites marked as expired
        """
        expired_invites = cls.objects.filter(
            status__in=[cls.Status.CREATED, cls.Status.SENT],
            expires_at__lte=timezone.now()
        )

        count = expired_invites.update(
            status=cls.Status.EXPIRED,
            updated_at=timezone.now()
        )

        return count
