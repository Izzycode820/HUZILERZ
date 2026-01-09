"""
Notifications App Configuration

Handles app initialization and signal receiver registration.
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Notifications'

    def ready(self):
        """
        Register signal receivers when app is ready.
        
        This ensures receivers are connected after all apps are loaded.
        """
        # Import receivers to register them with Django signals
        import notifications.receivers  # noqa: F401
