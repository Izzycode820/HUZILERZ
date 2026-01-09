"""
Notification WebSocket Routing

URL pattern for notification WebSocket connections.
"""

from django.urls import re_path
from notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]
