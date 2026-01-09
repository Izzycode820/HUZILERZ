"""
Django app configuration for workspace sync system
"""
from django.apps import AppConfig


class SyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workspace.sync'
    label = 'workspace_sync'
    verbose_name = 'Workspace Data Synchronization'

    def ready(self):
        """Initialize sync system when Django starts"""
        # Import signal handlers to register them
        from . import signals