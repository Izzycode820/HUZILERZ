"""
MediaLib Django App Configuration

Production-grade media management system for Django
"""

from django.apps import AppConfig


class MedialibConfig(AppConfig):
    """
    MediaLib application configuration

    Features:
    - Automatic signal registration for media cleanup
    - Model registration
    - Service initialization
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medialib'
    verbose_name = 'Media Library'

    def ready(self):
        """
        Register signals when Django starts

        This ensures automatic media cleanup when entities are deleted
        """
        # Import signals to register them
        try:
            import medialib.signals.media_signals  # noqa: F401
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to register medialib signals: {e}")
