from django.apps import AppConfig


class StorefrontConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workspace.storefront'
    label = 'workspace_storefront'
    verbose_name = 'Workspace Storefront Extension'

    def ready(self):
        """Import signals when app is ready"""
        pass
