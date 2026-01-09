from django.apps import AppConfig


class ThemeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'theme'
    verbose_name = 'Theme Management'

    def ready(self):
        """Import signals when app is ready"""
        import theme.signals  # noqa
