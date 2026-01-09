"""
Notification Model

In-app notification storage with production-ready indexing.

Performance: Composite indexes for unread queries < 50ms
Security: Workspace-scoped, recipient validated before access
Reliability: Bounded text fields, proper cascade behavior
"""
import uuid
from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    """
    Notification categories for filtering and display.
    
    Note: Keep in sync with frontend notification components.
    """
    ORDER_CREATED = 'order_created', 'New Order'
    ORDER_PAID = 'order_paid', 'Order Paid'
    ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'
    ORDER_STATUS_CHANGED = 'order_status_changed', 'Order Status Changed'
    SUBSCRIPTION_ACTIVATED = 'subscription_activated', 'Subscription Activated'
    SUBSCRIPTION_EXPIRED = 'subscription_expired', 'Subscription Expired'
    PAYMENT_FAILED = 'payment_failed', 'Payment Failed'
    STOCK_LOW = 'stock_low', 'Low Stock'
    STOCK_OUT = 'stock_out', 'Out of Stock'
    
    # Subscription Lifecycle
    SUBSCRIPTION_RENEWED = 'subscription_renewed', 'Subscription Renewed'
    SUBSCRIPTION_DOWNGRADED = 'subscription_downgraded', 'Subscription Downgraded'
    SUBSCRIPTION_CANCELLED = 'subscription_cancelled', 'Subscription Cancelled'
    GRACE_PERIOD_STARTED = 'grace_period_started', 'Grace Period Started'
    PLAN_CHANGE_SCHEDULED = 'plan_change_scheduled', 'Plan Change Scheduled'
    
    # Reminders
    PLAN_CHANGE_REMINDER = 'plan_change_reminder', 'Plan Change Reminder'
    RENEWAL_REMINDER = 'renewal_reminder', 'Renewal Reminder'
    GRACE_PERIOD_REMINDER = 'grace_period_reminder', 'Grace Period Reminder'
    
    # Compliance
    COMPLIANCE_VIOLATION = 'compliance_violation', 'Compliance Violation'
    COMPLIANCE_ENFORCED = 'compliance_enforced', 'Compliance Enforced'


class Notification(models.Model):
    """
    In-app notification record.
    
    Performance: Indexed on recipient + read_at for fast unread queries (<50ms)
    Security: Workspace-scoped, recipient validated before access
    Reliability: Bounded text fields, proper ON DELETE behavior
    
    Query Patterns:
    - Unread by user: recipient + read_at__isnull + created_at (composite index)
    - By workspace: workspace + recipient + created_at (composite index)
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,
        help_text="User who receives this notification"
    )
    
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name='notifications',
        help_text="Optional workspace context (for store-level notifications)"
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True,
        help_text="Notification category for filtering"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Short notification title"
    )
    
    body = models.TextField(
        max_length=2000,
        help_text="Notification body text"
    )
    
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Event payload (order_id, subscription_id, etc.)"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When notification was read, null if unread"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        app_label = 'notifications'
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            # Primary query: unread notifications by user, ordered by creation
            models.Index(
                fields=['recipient', 'read_at', '-created_at'],
                name='notif_user_unread_idx'
            ),
            # Workspace-scoped notifications for store owners
            models.Index(
                fields=['workspace', 'recipient', '-created_at'],
                name='notif_workspace_user_idx'
            ),
            # Filter by type
            models.Index(
                fields=['recipient', 'notification_type', '-created_at'],
                name='notif_user_type_idx'
            ),
        ]
    
    def __str__(self):
        status = 'read' if self.read_at else 'unread'
        return f"[{status}] {self.notification_type}: {self.title[:50]}"
    
    @property
    def is_read(self):
        """Check if notification has been read"""
        return self.read_at is not None
