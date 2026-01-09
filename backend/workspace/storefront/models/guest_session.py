# Guest Session Model - Track guest shopping sessions for storefront

import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone


class GuestSession(models.Model):
    """
    Track guest shopping sessions for storefront
    Sessions allow customers to browse and checkout without registration
    """

    # Session identification
    session_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique session identifier (URL-safe token)"
    )

    # Workspace relationship
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='guest_sessions'
    )

    # Cart relationship (one session = one cart)
    cart = models.OneToOneField(
        'Cart',  # Cart is in the same app (storefront)
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='guest_session'
    )

    # Session tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the guest"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Browser user agent string"
    )

    # Expiration management
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text="Session expiration timestamp (default 7 days)"
    )

    class Meta:
        app_label = 'workspace_storefront'
        db_table = 'storefront_guest_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['workspace', 'expires_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Session {self.session_id[:8]}... for {self.workspace.name}"

    @property
    def is_expired(self):
        """Check if session has expired"""
        return timezone.now() > self.expires_at

    def extend_expiration(self, days=7):
        """
        Extend session expiration
        Called on cart activity to keep active sessions alive
        """
        self.expires_at = timezone.now() + timedelta(days=days)
        self.save(update_fields=['expires_at'])

    @classmethod
    def create_session(cls, workspace, ip_address=None, user_agent=None):
        """
        Create a new guest session with unique token
        Returns: GuestSession instance
        """
        session_id = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=7)

        session = cls.objects.create(
            session_id=session_id,
            workspace=workspace,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else '',
            expires_at=expires_at
        )

        return session

    @classmethod
    def cleanup_expired_sessions(cls):
        """
        Clean up expired sessions
        Should be run periodically (e.g., daily cron job)
        """
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]

        return expired_count
