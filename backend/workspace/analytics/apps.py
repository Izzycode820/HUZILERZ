from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workspace.analytics'
    label = 'workspace_analytics'
    verbose_name = 'Workspace Analytics Extension'

    def ready(self):
        """
        Import signal handlers when app is ready
        """
        import workspace.analytics.signals.activity_signals