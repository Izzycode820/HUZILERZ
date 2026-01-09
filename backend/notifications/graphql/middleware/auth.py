"""
Notification Authentication Middleware

Handles both user-level (subscription) and workspace-level (store) notifications
Industry Standard: JWT for identity, X-Workspace-Id header for context

Context Injection:
- User-level notifications: Only require authenticated user (no workspace)
- Workspace-level notifications: Require user + workspace context
"""

from graphql import GraphQLError
from authentication.services.token_service import TokenService
from workspace.core.models import Workspace, Membership
import logging

logger = logging.getLogger('notifications.graphql')


class NotificationAuthMiddleware:
    """
    Authentication middleware for notification GraphQL operations
    
    User-level operations (auth required, no workspace):
    - myNotifications: User's notifications (includes all workspaces + user-level)
    - unreadNotificationCount: Total unread count across all
    - markNotificationAsRead: Mark single notification read
    - markAllNotificationsAsRead: Mark all read (user-level only)
    
    Workspace-scoped operations (auth + workspace required):
    - workspaceNotifications: Notifications for specific workspace
    - workspaceUnreadCount: Unread count for specific workspace
    
    Security: Leverages existing JWT token service
    """
    
    # User-level queries: require auth but NOT workspace context
    USER_LEVEL_OPERATIONS = {
        'myNotifications',
        'unreadNotificationCount', 
        'markNotificationAsRead',
        'markAllNotificationsAsRead',
        'notification'
    }
    
    # Workspace-scoped operations: require auth AND workspace context
    WORKSPACE_SCOPED_OPERATIONS = {
        'workspaceNotifications',
        'workspaceUnreadCount'
    }
    
    def resolve(self, next, root, info, **kwargs):
        request = info.context
        
        # Check if already processed by another middleware
        if hasattr(info.context, '_notification_auth_processed') and info.context._notification_auth_processed:
            return next(root, info, **kwargs)
        
        # Get operation name
        operation_name = self._get_operation_name(info)
        
        # Skip if not a notification operation
        all_notification_ops = self.USER_LEVEL_OPERATIONS | self.WORKSPACE_SCOPED_OPERATIONS
        if operation_name not in all_notification_ops:
            return next(root, info, **kwargs)
        
        # All notification operations require authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            raise GraphQLError("Authentication required")
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = TokenService.verify_access_token(token)
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=payload['user_id'])
            
        except Exception as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise GraphQLError(f"Authentication failed: {str(e)}")
        
        # USER-LEVEL OPERATIONS: Auth required but NO workspace context needed
        if operation_name in self.USER_LEVEL_OPERATIONS:
            info.context.user = user
            info.context.user_id = str(user.id)
            info.context.workspace = None
            info.context.workspace_id = None
            info.context.is_authenticated = True
            info.context.jwt_payload = payload
            info.context._notification_auth_processed = True
            return next(root, info, **kwargs)
        
        # WORKSPACE-SCOPED OPERATIONS: Require workspace context
        workspace_id = request.META.get('HTTP_X_WORKSPACE_ID')
        
        if not workspace_id:
            raise GraphQLError(
                "No workspace context - send X-Workspace-Id header with your request"
            )
        
        # Validate workspace exists and user has access
        try:
            workspace = Workspace.objects.select_related('owner').get(
                id=workspace_id,
                status='active'
            )
        except Workspace.DoesNotExist:
            logger.warning(f"Workspace {workspace_id} not found or inactive (user: {user.id})")
            raise GraphQLError("Workspace not found or inactive")
        
        # Validate user has access
        if workspace.owner == user:
            workspace_role = 'owner'
        else:
            try:
                membership = Membership.objects.get(
                    workspace=workspace,
                    user=user,
                    is_active=True
                )
                workspace_role = membership.role
            except Membership.DoesNotExist:
                logger.error(
                    f"SECURITY: User {user.id} attempted unauthorized access to workspace {workspace_id}"
                )
                raise GraphQLError(
                    "Access denied - you do not have permission to access this workspace"
                )
        
        # Superuser override
        if user.is_superuser:
            workspace_role = 'superuser'
        
        # Inject into GraphQL context
        info.context.user = user
        info.context.user_id = str(user.id)
        info.context.workspace = workspace
        info.context.workspace_id = str(workspace.id)
        info.context.workspace_role = workspace_role
        info.context.is_authenticated = True
        info.context.jwt_payload = payload
        info.context._notification_auth_processed = True
        
        return next(root, info, **kwargs)
    
    def _get_operation_name(self, info):
        """Extract operation name from GraphQL info"""
        if info.field_name:
            return info.field_name
        
        if hasattr(info.operation, 'name') and info.operation.name:
            return info.operation.name.value
        
        return None
