"""
Notification WebSocket Consumer

Real-time notification delivery via WebSocket.
Industry Standard: AsyncWebsocketConsumer with user-specific groups.

Architecture:
- Each user joins a group: `notifications_user_{user_id}`
- When notification is created, signal broadcasts to user's group
- Frontend receives push update instantly
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

logger = logging.getLogger('notifications.websocket')


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    
    Connection URL: ws://host/ws/notifications/
    Auth: JWT token passed as query param ?token=<jwt>
    
    Features:
    - User-specific groups for targeted delivery
    - JWT authentication on connect
    - Graceful error handling
    """
    
    async def connect(self):
        """
        Handle WebSocket connection.
        
        Auth: Validates JWT token from query string
        Group: Joins user-specific notification group
        """
        try:
            # Extract token from query string
            query_string = self.scope.get('query_string', b'').decode()
            token = self._extract_token(query_string)
            
            if not token:
                logger.warning("WebSocket connection rejected: No token provided")
                await self.close(code=4001)
                return
            
            # Validate JWT and get user
            user = await self._authenticate_token(token)
            
            if not user:
                logger.warning("WebSocket connection rejected: Invalid token")
                await self.close(code=4002)
                return
            
            # Store user in scope
            self.scope['user'] = user
            self.user_id = str(user.id)
            
            # Create user-specific group name
            self.group_name = f"notifications_user_{self.user_id}"
            
            # Join user's notification group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
            
            logger.info(f"WebSocket connected: user={self.user_id}, group={self.group_name}")
            
            # Send initial unread count
            unread_count = await self._get_unread_count()
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'unread_count': unread_count
            }))
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected: user={getattr(self, 'user_id', 'unknown')}")
    
    async def receive(self, text_data):
        """
        Handle incoming messages from client.
        
        Supported actions:
        - mark_read: Mark notification as read
        - mark_all_read: Mark all notifications as read
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self._mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'type': 'notification_read',
                        'notification_id': notification_id,
                        'success': success
                    }))
            
            elif action == 'mark_all_read':
                workspace_id = data.get('workspace_id')
                count = await self._mark_all_read(workspace_id)
                await self.send(text_data=json.dumps({
                    'type': 'all_notifications_read',
                    'count': count
                }))
            
            elif action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received on WebSocket")
        except Exception as e:
            logger.error(f"WebSocket receive error: {str(e)}", exc_info=True)
    
    async def notification_push(self, event):
        """
        Handle notification push from channel layer.
        
        Called when: Signal broadcasts new notification to user's group
        """
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification']
        }))
    
    async def unread_count_update(self, event):
        """Handle unread count update from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'unread_count': event['count']
        }))
    
    # Helper methods
    
    def _extract_token(self, query_string):
        """Extract JWT token from query string."""
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        return params.get('token')
    
    @database_sync_to_async
    def _authenticate_token(self, token):
        """Validate JWT token and return user."""
        try:
            from authentication.services.token_service import TokenService
            from django.contrib.auth import get_user_model
            
            payload = TokenService.verify_access_token(token)
            User = get_user_model()
            return User.objects.get(id=payload['user_id'])
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None
    
    @database_sync_to_async
    def _get_unread_count(self):
        """Get unread notification count for user."""
        from notifications.models import Notification
        return Notification.objects.filter(
            recipient_id=self.user_id,
            read_at__isnull=True
        ).count()
    
    @database_sync_to_async
    def _mark_notification_read(self, notification_id):
        """Mark single notification as read."""
        from notifications.models import Notification
        from django.utils import timezone
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient_id=self.user_id
            )
            if notification.read_at is None:
                notification.read_at = timezone.now()
                notification.save(update_fields=['read_at'])
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def _mark_all_read(self, workspace_id=None):
        """Mark all notifications as read."""
        from notifications.models import Notification
        from django.utils import timezone
        from django.db.models import Q
        
        queryset = Notification.objects.filter(
            recipient_id=self.user_id,
            read_at__isnull=True
        )
        
        if workspace_id:
            queryset = queryset.filter(
                Q(workspace_id=workspace_id) | Q(workspace__isnull=True)
            )
        
        return queryset.update(read_at=timezone.now())
