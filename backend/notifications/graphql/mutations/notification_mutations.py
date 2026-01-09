"""
Notification GraphQL Mutations

Provides mutations for notification operations with proper authentication.
Follows subscription middleware patterns.
"""

import graphene
from graphql import GraphQLError
from ..types.notification_types import NotificationType
from notifications.services import NotificationService
from notifications.models import Notification
import logging

logger = logging.getLogger('notifications.graphql')


class MarkNotificationAsRead(graphene.Mutation):
    """
    Mark a single notification as read.
    
    Security: Only the recipient can mark their notification as read.
    Reliability: Uses select_for_update to prevent race conditions.
    
    Access: User-level (no workspace required)
    """
    
    class Arguments:
        notification_id = graphene.ID(
            required=True,
            description="ID of notification to mark as read"
        )
    
    success = graphene.Boolean(description="Whether operation succeeded")
    notification = graphene.Field(
        NotificationType,
        description="Updated notification"
    )
    
    def mutate(self, info, notification_id):
        """Execute mark as read mutation"""
        user = info.context.user
        if not user or not getattr(info.context, 'is_authenticated', False):
            raise GraphQLError("Authentication required")
        
        notification = NotificationService.mark_as_read(
            notification_id=notification_id,
            user=user
        )
        
        if notification is None:
            raise GraphQLError("Notification not found or access denied")
        
        return MarkNotificationAsRead(
            success=True,
            notification=notification
        )


class MarkAllNotificationsAsRead(graphene.Mutation):
    """
    Mark all notifications as read.
    
    Modes:
    - No workspace_id: Mark only user-level notifications (workspace IS NULL)
    - With workspace_id: Mark user-level + specific workspace notifications
    
    Performance: Single bulk UPDATE query.
    Access: User-level (no workspace required)
    """
    
    class Arguments:
        workspace_id = graphene.ID(
            description="Optional: Include workspace notifications in bulk mark"
        )
        workspace_only = graphene.Boolean(
            default_value=False,
            description="If true, only mark workspace notifications (not user-level)"
        )
    
    success = graphene.Boolean(description="Whether operation succeeded")
    count = graphene.Int(description="Number of notifications marked as read")
    
    def mutate(self, info, workspace_id=None, workspace_only=False):
        """Execute mark all as read mutation"""
        user = info.context.user
        if not user or not getattr(info.context, 'is_authenticated', False):
            raise GraphQLError("Authentication required")
        
        from django.db.models import Q
        from django.utils import timezone
        
        # Build query based on parameters
        queryset = Notification.objects.filter(
            recipient=user,
            read_at__isnull=True
        )
        
        if workspace_id:
            # Validate workspace access
            from workspace.core.models import Workspace, Membership
            try:
                workspace = Workspace.objects.get(id=workspace_id, status='active')
                # Check access
                if workspace.owner != user:
                    try:
                        Membership.objects.get(workspace=workspace, user=user, is_active=True)
                    except Membership.DoesNotExist:
                        raise GraphQLError("Access denied to workspace")
            except Workspace.DoesNotExist:
                raise GraphQLError("Workspace not found")
            
            if workspace_only:
                # Only workspace notifications
                queryset = queryset.filter(workspace=workspace)
            else:
                # User-level + workspace notifications
                queryset = queryset.filter(
                    Q(workspace=workspace) | Q(workspace__isnull=True)
                )
        else:
            # Only user-level notifications (no workspace)
            queryset = queryset.filter(workspace__isnull=True)
        
        count = queryset.update(read_at=timezone.now())
        
        logger.info(f"Marked {count} notifications as read for user={user.id}")
        
        return MarkAllNotificationsAsRead(
            success=True,
            count=count
        )


class NotificationMutations(graphene.ObjectType):
    """
    Container for notification mutations.
    
    Include in main schema via:
        class Mutation(NotificationMutations, ...):
            pass
    """
    mark_notification_as_read = MarkNotificationAsRead.Field()
    mark_all_notifications_as_read = MarkAllNotificationsAsRead.Field()


__all__ = [
    'NotificationMutations',
    'MarkNotificationAsRead',
    'MarkAllNotificationsAsRead'
]
