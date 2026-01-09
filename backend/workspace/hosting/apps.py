from django.apps import AppConfig


class HostingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workspace.hosting'
    label = 'workspace_hosting'
    verbose_name = 'Workspace Hosting Extension'

    def ready(self):
        """Import receivers when Django starts"""
        import workspace.hosting.receivers