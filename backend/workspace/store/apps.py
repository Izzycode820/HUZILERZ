from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workspace.store'
    label = 'workspace_store'
    verbose_name = 'Workspace Store Extension'

    def ready(self):
        """
        Import signals when app is ready

        This registers signal handlers for automatic cache invalidation
        when products/categories are created, updated, or deleted.
        """
        import workspace.store.signals  # noqa: F401
