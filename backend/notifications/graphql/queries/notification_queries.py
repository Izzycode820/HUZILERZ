"""
Notification GraphQL Queries

Provides notification queries with user-level and workspace-scoped access patterns.
Follows subscription auth middleware and store query patterns.

Query Patterns:
- User-level: myNotifications, unreadNotificationCount (all user's notifications)
- Workspace-scoped: workspaceNotifications, workspaceUnreadCount (specific workspace)
"""

import graphene
from graphql import GraphQLError
from ..types.notification_types import NotificationType, NotificationTypeEnum
from notifications.models import Notification
import logging

logger = logging.getLogger('notifications.graphql')


class NotificationQueries(graphene.ObjectType):
    """
    Notification queries with dual access patterns
    
    User-level: Authenticated user can see all their notifications
    Workspace-scoped: User can filter to specific workspace notifications
    
    Security: Queries automatically scoped to authenticated user
    Performance: Uses indexed queries, results are paginated
    """
    
    # =========================================================================
    # USER-LEVEL QUERIES (no workspace context needed)
    # =========================================================================
    
    my_notifications = graphene.List(
        NotificationType,
        unread_only=graphene.Boolean(
            default_value=False,
            description="If true, only return unread notifications"
        ),
        notification_type=NotificationTypeEnum(
            description="Optional type filter"
        ),
        limit=graphene.Int(
            default_value=50,
            description="Max results (default 50, max 100)"
        ),
        description="Get all notifications for authenticated user (user-level + all workspaces)"
    )
    
    unread_notification_count = graphene.Int(
        description="Get total unread notification count for user"
    )
    
    notification = graphene.Field(
        NotificationType,
        id=graphene.ID(required=True, description="Notification ID"),
        description="Get single notification by ID"
    )
    
    # =========================================================================
    # WORKSPACE-SCOPED QUERIES (require X-Workspace-Id header)
    # =========================================================================
    
    workspace_notifications = graphene.List(
        NotificationType,
        unread_only=graphene.Boolean(
            default_value=False,
            description="If true, only return unread notifications"
        ),
        notification_type=NotificationTypeEnum(
            description="Optional type filter"
        ),
        limit=graphene.Int(
            default_value=50,
            description="Max results (default 50, max 100)"
        ),
        description="Get notifications for current workspace + user-level notifications"
    )
    
    workspace_unread_count = graphene.Int(
        description="Get unread count for current workspace + user-level"
    )
    
    # =========================================================================
    # RESOLVERS
    # =========================================================================
    
    def resolve_my_notifications(
        self,
        info,
        unread_only=False,
        notification_type=None,
        limit=50
    ):
        """
        Resolve all user's notifications (user-level + all workspaces)
        
        Security: Scoped to authenticated user
        Performance: Uses composite index, limited results
        """
        user = info.context.user
        if not user or not getattr(info.context, 'is_authenticated', False):
            raise GraphQLError("Authentication required")
        
        # Enforce max limit
        limit = min(limit, 100)
        
        # Build query - all notifications for this user
        queryset = Notification.objects.filter(
            recipient=user
        ).select_related('workspace').order_by('-created_at')
        
        if unread_only:
            queryset = queryset.filter(read_at__isnull=True)
        
        if notification_type:
            type_value = notification_type.value if hasattr(notification_type, 'value') else notification_type
            queryset = queryset.filter(notification_type=type_value)
        
        return queryset[:limit]
    
    def resolve_unread_notification_count(self, info):
        """
        Resolve total unread count for user
        
        Performance: COUNT query with composite index, < 50ms
        """
        user = info.context.user
        if not user or not getattr(info.context, 'is_authenticated', False):
            return 0
        
        return Notification.objects.filter(
            recipient=user,
            read_at__isnull=True
        ).count()
    
    def resolve_notification(self, info, id):
        """
        Resolve single notification
        
        Security: Only returns if user is recipient
        """
        user = info.context.user
        if not user or not getattr(info.context, 'is_authenticated', False):
            raise GraphQLError("Authentication required")
        
        try:
            return Notification.objects.select_related('workspace').get(
                id=id,
                recipient=user
            )
        except Notification.DoesNotExist:
            raise GraphQLError("Notification not found")
    
    def resolve_workspace_notifications(
        self,
        info,
        unread_only=False,
        notification_type=None,
        limit=50
    ):
        """
        Resolve notifications for current workspace + user-level
        
        Query: (workspace == current) OR (workspace IS NULL)
        Security: Requires workspace context via X-Workspace-Id header
        """
        user = info.context.user
        workspace = info.context.workspace
        
        if not user or not getattr(info.context, 'is_authenticated', False):
            raise GraphQLError("Authentication required")
        
        if not workspace:
            raise GraphQLError("Workspace context required - send X-Workspace-Id header")
        
        # Enforce max limit
        limit = min(limit, 100)
        
        # Build query - current workspace + user-level (NULL workspace)
        from django.db.models import Q
        queryset = Notification.objects.filter(
            recipient=user
        ).filter(
            Q(workspace=workspace) | Q(workspace__isnull=True)
        ).select_related('workspace').order_by('-created_at')
        
        if unread_only:
            queryset = queryset.filter(read_at__isnull=True)
        
        if notification_type:
            type_value = notification_type.value if hasattr(notification_type, 'value') else notification_type
            queryset = queryset.filter(notification_type=type_value)
        
        return queryset[:limit]
    
    def resolve_workspace_unread_count(self, info):
        """
        Resolve unread count for current workspace + user-level
        
        Performance: COUNT query with index
        """
        user = info.context.user
        workspace = info.context.workspace
        
        if not user or not getattr(info.context, 'is_authenticated', False):
            return 0
        
        if not workspace:
            return 0
        
        from django.db.models import Q
        return Notification.objects.filter(
            recipient=user,
            read_at__isnull=True
        ).filter(
            Q(workspace=workspace) | Q(workspace__isnull=True)
        ).count()


__all__ = ['NotificationQueries']
