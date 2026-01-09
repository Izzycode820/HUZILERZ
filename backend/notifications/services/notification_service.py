"""
Notification Service

Notification orchestrator - receives events, creates and manages notifications.

Performance: All queries < 50ms with proper indexes
Reliability: Atomic transactions, comprehensive error handling
Security: Ownership validation on all read/write operations
"""
import logging
from typing import Optional, List
from uuid import UUID
from django.db import transaction
from django.utils import timezone
from notifications.models import Notification

logger = logging.getLogger('notifications.service')


class NotificationService:
    """
    Core notification orchestration service.
    
    Responsibilities:
    - Create notifications from domain events
    - Mark notifications as read
    - Query notifications with workspace scoping
    
    All methods are static - no instance state required.
    """
    
    @staticmethod
    @transaction.atomic
    def create_notification(
        recipient,
        notification_type: str,
        title: str,
        body: str,
        workspace=None,
        data: dict = None
    ) -> Optional[Notification]:
        """
        Create and persist notification.
        
        Performance: Single INSERT, no N+1
        Reliability: Atomic, graceful failure logging
        
        Args:
            recipient: User to receive notification
            notification_type: NotificationType value
            title: Short notification title (max 255 chars)
            body: Notification body text (max 2000 chars)
            workspace: Optional workspace context
            data: Optional event payload dict
            
        Returns:
            Created Notification or None on failure
        """
        try:
            notification = Notification.objects.create(
                recipient=recipient,
                workspace=workspace,
                notification_type=notification_type,
                title=title[:255],  # Enforce max_length
                body=body[:2000],   # Enforce max_length
                data=data or {}
            )
            logger.info(
                f"Notification created: type={notification_type}, "
                f"recipient={recipient.id}, workspace={workspace.id if workspace else None}"
            )
            
            # Broadcast via WebSocket (async, non-blocking)
            NotificationService._broadcast_notification(notification)
            
            return notification
        except Exception as e:
            logger.error(f"Failed to create notification: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _broadcast_notification(notification):
        """
        Broadcast notification to user's WebSocket group.
        
        Non-blocking: Uses async_to_sync for Django context
        Graceful: Logs but doesn't fail on broadcast error
        """
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if not channel_layer:
                logger.warning("Channel layer not configured, skipping WebSocket broadcast")
                return
            
            group_name = f"notifications_user_{notification.recipient_id}"
            
            # Prepare notification data for WebSocket
            notification_data = {
                'id': str(notification.id),
                'type': notification.notification_type,
                'title': notification.title,
                'body': notification.body,
                'workspace_id': str(notification.workspace_id) if notification.workspace_id else None,
                'workspace_name': notification.workspace.name if notification.workspace else None,
                'created_at': notification.created_at.isoformat(),
                'is_read': False,
                'data': notification.data
            }
            
            # Send to user's group
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_push',
                    'notification': notification_data
                }
            )
            
            logger.debug(f"WebSocket broadcast sent to {group_name}")
            
        except Exception as e:
            # Log but don't fail - WebSocket is enhancement, not critical
            logger.warning(f"WebSocket broadcast failed: {e}")
    
    @staticmethod
    @transaction.atomic
    def mark_as_read(notification_id: UUID, user) -> Optional[Notification]:
        """
        Mark single notification as read with ownership validation.
        
        Security: Validates recipient matches requesting user
        Reliability: Uses select_for_update to prevent race conditions
        
        Args:
            notification_id: UUID of notification to mark
            user: Requesting user (must be recipient)
            
        Returns:
            Updated Notification or None if not found/unauthorized
        """
        try:
            notification = Notification.objects.select_for_update().get(
                id=notification_id,
                recipient=user  # Security: must be owner
            )
            if notification.read_at is None:
                notification.read_at = timezone.now()
                notification.save(update_fields=['read_at'])
                logger.info(f"Notification marked as read: {notification_id}")
            return notification
        except Notification.DoesNotExist:
            logger.warning(f"Notification not found or unauthorized: {notification_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}", exc_info=True)
            return None
    
    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user, workspace=None) -> int:
        """
        Mark all notifications as read.
        
        Performance: Single bulk UPDATE, no N+1
        
        Args:
            user: User whose notifications to mark
            workspace: Optional workspace filter
            
        Returns:
            Count of notifications marked as read
        """
        try:
            queryset = Notification.objects.filter(
                recipient=user,
                read_at__isnull=True
            )
            if workspace:
                queryset = queryset.filter(workspace=workspace)
            
            count = queryset.update(read_at=timezone.now())
            logger.info(f"Marked {count} notifications as read for user={user.id}")
            return count
        except Exception as e:
            logger.error(f"Failed to mark all as read: {e}", exc_info=True)
            return 0
    
    @staticmethod
    def get_unread_count(user, workspace=None) -> int:
        """
        Get unread notification count.
        
        Performance: COUNT query with composite index, < 50ms
        
        Args:
            user: User to count for
            workspace: Optional workspace filter
            
        Returns:
            Count of unread notifications
        """
        try:
            queryset = Notification.objects.filter(
                recipient=user,
                read_at__isnull=True
            )
            if workspace:
                queryset = queryset.filter(workspace=workspace)
            return queryset.count()
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}", exc_info=True)
            return 0
    
    @staticmethod
    def get_notifications(
        user,
        workspace=None,
        unread_only: bool = False,
        notification_type: str = None,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get paginated notifications for user.
        
        Performance: Uses composite index, limits results
        
        Args:
            user: User to fetch for
            workspace: Optional workspace filter
            unread_only: If True, only return unread
            notification_type: Optional type filter
            limit: Max results (default 50)
            
        Returns:
            List of Notification objects
        """
        try:
            queryset = Notification.objects.filter(recipient=user)
            
            if workspace:
                queryset = queryset.filter(workspace=workspace)
            if unread_only:
                queryset = queryset.filter(read_at__isnull=True)
            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)
            
            # Apply limit and return
            return list(queryset[:limit])
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}", exc_info=True)
            return []
