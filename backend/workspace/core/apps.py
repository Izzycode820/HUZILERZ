from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workspace.core'
    label = 'workspace_core'
    verbose_name = 'Workspace Core'
    
    def ready(self):
        """Import signals and receivers when Django starts"""
        try:
            import workspace.core.signals
            import workspace.core.receivers  # Register subscription event receivers
        except ImportError:
            pass