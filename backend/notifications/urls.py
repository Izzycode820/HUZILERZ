"""
Notifications URL Configuration

GraphQL Endpoint: /api/notifications/graphql/
- User-level Queries (auth): myNotifications, unreadNotificationCount
- Workspace-scoped Queries (auth + workspace): workspaceNotifications, workspaceUnreadCount
- Mutations: markNotificationAsRead, markAllNotificationsAsRead
"""
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from notifications.graphql.schema import schema
from notifications.graphql.middleware.auth import NotificationAuthMiddleware

app_name = 'notifications'

urlpatterns = [
    # GraphQL endpoint for all notification queries and mutations
    # Authenticated operations with optional workspace context
    path('graphql/', csrf_exempt(GraphQLView.as_view(
        graphiql=True,
        schema=schema,
        middleware=[NotificationAuthMiddleware()]
    )), name='notification-graphql'),
]
