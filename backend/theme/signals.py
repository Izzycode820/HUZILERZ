"""
Theme Signals - Trigger deployment infrastructure on publish
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

logger = logging.getLogger(__name__)

# Custom signal for theme publication
theme_published = Signal()  # No providing_args needed in Django 3.0+


@receiver(post_save, sender='theme.TemplateCustomization')
def handle_theme_activation(sender, instance, created, **kwargs):
    """
    Handle theme activation - lightweight content update only

    NEW FLOW (decoupled from infrastructure):
    - Infrastructure is provisioned once during workspace creation
    - Theme activation only updates the active customization pointer
    - CDN cache is invalidated asynchronously
    - NO DNS/SSL/CDN provisioning here

    Flow:
        Theme.publish() -> is_active=True -> Signal -> Update DeployedSite + Invalidate CDN
    """
    # Only trigger on activation (not creation)
    if not created and instance.is_active:
        try:
            # Check if theme was just activated (avoid duplicate triggers)
            if not hasattr(instance, '_skip_signal'):
                logger.info(
                    f"Theme activated: {instance.theme_name} for workspace {instance.workspace.id}"
                )

                # Enqueue lightweight deployment update (pointer update + CDN invalidation)
                from workspace.hosting.tasks.deployment_tasks import apply_theme_deployment
                apply_theme_deployment.apply_async(
                    args=[str(instance.workspace.id), str(instance.id)],
                    countdown=2  # Small delay to ensure transaction commits
                )

                logger.info(
                    f"Enqueued theme deployment for workspace {instance.workspace.id}"
                )

        except Exception as e:
            # Log error but don't fail theme publish
            logger.error(
                f"Failed to trigger theme deployment: {e}",
                exc_info=True
            )
