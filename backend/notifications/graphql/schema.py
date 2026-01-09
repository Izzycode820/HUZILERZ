"""
Notifications GraphQL Schema

Combines queries and mutations for notification operations.
Routes:
- USER-LEVEL: myNotifications, unreadCount (auth required, no workspace)
- WORKSPACE-SCOPED: workspaceNotifications, workspaceUnreadCount (auth + workspace required)
- MUTATIONS: markAsRead, markAllAsRead (auth required)
"""

import graphene
from notifications.graphql.queries.notification_queries import NotificationQueries
from notifications.graphql.mutations.notification_mutations import NotificationMutations


class Query(
    NotificationQueries,
    graphene.ObjectType
):
    """
    Combined notification queries
    
    User-level queries (auth only, no workspace):
    - myNotifications: All user's notifications
    - unreadNotificationCount: Total unread count
    - notification: Single notification by ID
    
    Workspace-scoped queries (auth + workspace header):
    - workspaceNotifications: Current workspace + user-level notifications
    - workspaceUnreadCount: Unread count for current workspace
    """
    pass


class Mutation(
    NotificationMutations,
    graphene.ObjectType
):
    """
    Notification mutations
    
    User-level mutations (auth required):
    - markNotificationAsRead: Mark single notification as read
    - markAllNotificationsAsRead: Bulk mark as read
    """
    pass


# Schema instance (queries + mutations)
schema = graphene.Schema(query=Query, mutation=Mutation)
