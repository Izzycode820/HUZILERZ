"""
Notification GraphQL Types

Provides GraphQL types for Notification model with proper DjangoObjectType
following store module patterns.
"""

import graphene
from graphene_django import DjangoObjectType
from notifications.models import Notification
from notifications.models.notification import NotificationType as NotificationTypeChoices
from .common_types import BaseConnection


class NotificationTypeEnum(graphene.Enum):
    """
    GraphQL enum for notification types.
    Mirrors NotificationType model choices.
    """
    ORDER_CREATED = 'order_created'
    ORDER_PAID = 'order_paid'
    ORDER_CANCELLED = 'order_cancelled'
    ORDER_STATUS_CHANGED = 'order_status_changed'
    SUBSCRIPTION_ACTIVATED = 'subscription_activated'
    SUBSCRIPTION_EXPIRED = 'subscription_expired'
    PAYMENT_FAILED = 'payment_failed'
    STOCK_LOW = 'stock_low'
    STOCK_OUT = 'stock_out'


class NotificationType(DjangoObjectType):
    """
    GraphQL type for Notification model
    
    Features:
    - All notification fields with proper typing
    - Workspace relationship for store-level notifications
    - Read status tracking
    
    Security: Only exposed to authenticated recipient
    """
    id = graphene.ID(required=True)
    
    class Meta:
        model = Notification
        fields = (
            'id', 'notification_type', 'title', 'body', 'data',
            'read_at', 'created_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection
    
    def resolve_id(self, info):
        return str(self.id)
    
    # Virtual fields
    is_read = graphene.Boolean(description="Whether notification has been read")
    notification_type_display = graphene.String(description="Human-readable notification type")
    workspace_name = graphene.String(description="Workspace name for store-level notifications")
    
    def resolve_is_read(self, info):
        """Resolve is_read property"""
        return self.read_at is not None
    
    def resolve_notification_type_display(self, info):
        """Resolve human-readable notification type"""
        return self.get_notification_type_display()
    
    def resolve_workspace_name(self, info):
        """Resolve workspace name for display"""
        if self.workspace:
            return self.workspace.name
        return None


class NotificationConnection(graphene.relay.Connection):
    """
    Notification connection with pagination support
    """
    class Meta:
        node = NotificationType
    
    total_count = graphene.Int()
    unread_count = graphene.Int()
    
    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()
    
    def resolve_unread_count(self, info, **kwargs):
        """Resolve unread count from queryset"""
        return self.iterable.filter(read_at__isnull=True).count()


__all__ = [
    'NotificationType',
    'NotificationTypeEnum',
    'NotificationConnection'
]
