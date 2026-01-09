"""
Signal Handlers for Workspace Data Synchronization
Automatically trigger sync events when workspace data changes
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.apps import apps
from django.core.cache import cache
from workspace.core.services.base_data_export_service import WorkspaceDataChangeDetector
from .tasks import trigger_workspace_sync_async
import logging

logger = logging.getLogger('workspace.sync.signals')


class WorkspaceSyncSignalHandler:
    """
    Centralized signal handler for workspace synchronization
    Manages all workspace model changes and triggers appropriate sync events
    """

    # Models that trigger sync when changed (workspace-agnostic)
    SYNC_MODELS = {
        'core.Workspace': {
            'sync_fields': ['name', 'description', 'settings'],
            'event_prefix': 'workspace'
        }
    }

    # Store-specific models
    STORE_SYNC_MODELS = {
        'store.Product': {
            'sync_fields': [
                'name', 'description', 'price', 'featured_image', 'images',
                'is_active', 'stock_quantity', 'category', 'tags'
            ],
            'event_prefix': 'product'
        },
        'store.Order': {
            'sync_fields': ['status', 'total_amount'],
            'event_prefix': 'order'
        }
    }

    # Blog-specific models
    BLOG_SYNC_MODELS = {
        'core.BaseWorkspaceContentModel': {
            'sync_fields': [
                'title', 'content', 'excerpt', 'featured_image',
                'is_active', 'status', 'tags'
            ],
            'event_prefix': 'post'
        }
    }

    # Services-specific models
    SERVICES_SYNC_MODELS = {
        'services.Service': {
            'sync_fields': [
                'name', 'description', 'price', 'duration_minutes',
                'is_active', 'booking_enabled'
            ],
            'event_prefix': 'service'
        },
        'services.Booking': {
            'sync_fields': ['status', 'scheduled_at'],
            'event_prefix': 'booking'
        }
    }

    @classmethod
    def get_all_sync_models(cls):
        """Get all models that trigger sync across all workspace types"""
        all_models = {}
        all_models.update(cls.SYNC_MODELS)
        all_models.update(cls.STORE_SYNC_MODELS)
        all_models.update(cls.BLOG_SYNC_MODELS)
        all_models.update(cls.SERVICES_SYNC_MODELS)
        return all_models

    @classmethod
    def should_trigger_sync(cls, model_label: str, changed_fields: list) -> bool:
        """
        Determine if model changes should trigger sync

        Args:
            model_label: Model label in format 'app.Model'
            changed_fields: List of changed field names

        Returns:
            Boolean indicating if sync should be triggered
        """
        all_models = cls.get_all_sync_models()

        if model_label not in all_models:
            return False

        sync_fields = all_models[model_label]['sync_fields']
        return WorkspaceDataChangeDetector.should_trigger_sync(changed_fields, sync_fields)

    @classmethod
    def get_event_type(cls, model_label: str, instance, created: bool) -> str:
        """
        Get appropriate event type for model change

        Args:
            model_label: Model label in format 'app.Model'
            instance: Model instance
            created: Whether instance was created

        Returns:
            Event type string
        """
        all_models = cls.get_all_sync_models()

        if model_label not in all_models:
            return 'unknown.updated'

        event_prefix = all_models[model_label]['event_prefix']

        if created:
            return f"{event_prefix}.created"
        else:
            # Special handling for status changes
            if hasattr(instance, 'status'):
                if model_label == 'core.BaseWorkspaceContentModel' and instance.status == 'published':
                    return f"{event_prefix}.published"

            return f"{event_prefix}.updated"


# Store model change tracking in cache for comparison
def get_instance_cache_key(instance):
    """Generate cache key for instance data"""
    model_label = f"{instance._meta.app_label}.{instance._meta.model_name}"
    return f"sync_cache:{model_label}:{instance.pk}"


@receiver(pre_save)
def cache_instance_data(sender, instance, **kwargs):
    """
    Cache instance data before save to detect changes
    Only cache for models that trigger sync
    """
    try:
        model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"

        if model_label in WorkspaceSyncSignalHandler.get_all_sync_models():
            # Only cache if instance has a workspace (tenant-scoped)
            if hasattr(instance, 'workspace') or hasattr(instance, 'workspace_id'):
                if instance.pk:  # Only for existing instances
                    # Get current data from database
                    try:
                        current_instance = sender.objects.get(pk=instance.pk)
                        current_data = {}

                        # Cache relevant fields
                        sync_config = WorkspaceSyncSignalHandler.get_all_sync_models()[model_label]
                        for field in sync_config['sync_fields']:
                            if hasattr(current_instance, field):
                                current_data[field] = getattr(current_instance, field)

                        # Cache for 5 minutes
                        cache_key = get_instance_cache_key(instance)
                        cache.set(cache_key, current_data, 300)

                    except sender.DoesNotExist:
                        pass  # Instance doesn't exist yet, no need to cache

    except Exception as e:
        # Don't let caching errors break the save operation
        logger.warning(f"Failed to cache instance data: {str(e)}")


@receiver(post_save)
def handle_workspace_model_change(sender, instance, created, **kwargs):
    """
    Handle post-save signal for workspace-related models
    Triggers sync events for relevant changes
    """
    try:
        model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"

        # Only process models that trigger sync
        if model_label not in WorkspaceSyncSignalHandler.get_all_sync_models():
            return

        # Get workspace ID
        workspace_id = None
        if hasattr(instance, 'workspace'):
            workspace_id = str(instance.workspace.id) if instance.workspace else None
        elif hasattr(instance, 'workspace_id'):
            workspace_id = str(instance.workspace_id) if instance.workspace_id else None
        elif model_label == 'core.Workspace':
            workspace_id = str(instance.id)

        if not workspace_id:
            return  # No workspace context, skip sync

        # Detect changes
        changed_fields = []
        if not created:
            # Get cached data for comparison
            cache_key = get_instance_cache_key(instance)
            previous_data = cache.get(cache_key)

            if previous_data:
                changed_fields = WorkspaceDataChangeDetector.detect_changes(
                    instance, previous_data
                )
                # Clean up cache
                cache.delete(cache_key)
            else:
                # Fallback: assume all sync fields changed
                sync_config = WorkspaceSyncSignalHandler.get_all_sync_models()[model_label]
                changed_fields = sync_config['sync_fields']
        else:
            # New instance: all fields are "changed"
            sync_config = WorkspaceSyncSignalHandler.get_all_sync_models()[model_label]
            changed_fields = sync_config['sync_fields']

        # Check if sync should be triggered
        if WorkspaceSyncSignalHandler.should_trigger_sync(model_label, changed_fields):
            # Get event type
            event_type = WorkspaceSyncSignalHandler.get_event_type(model_label, instance, created)

            # Prepare sync data
            sync_data = prepare_sync_data(instance, changed_fields)

            # Get user context if available
            user_id = None
            if hasattr(instance, '_sync_user_id'):
                user_id = instance._sync_user_id

            # Trigger async sync
            trigger_workspace_sync_async.delay(
                workspace_id=workspace_id,
                event_type=event_type,
                entity_type=sender._meta.model_name,
                entity_id=str(instance.pk),
                data=sync_data,
                changed_fields=changed_fields,
                user_id=user_id
            )

            logger.info(
                f"Triggered sync for {event_type} in workspace {workspace_id} "
                f"({len(changed_fields)} fields changed)"
            )

    except Exception as e:
        # Don't let sync errors break the save operation
        logger.error(f"Failed to handle workspace model change: {str(e)}")


@receiver(post_delete)
def handle_workspace_model_delete(sender, instance, **kwargs):
    """
    Handle post-delete signal for workspace-related models
    Triggers sync events for deletions
    """
    try:
        model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"

        # Only process models that trigger sync
        if model_label not in WorkspaceSyncSignalHandler.get_all_sync_models():
            return

        # Get workspace ID
        workspace_id = None
        if hasattr(instance, 'workspace'):
            workspace_id = str(instance.workspace.id) if instance.workspace else None
        elif hasattr(instance, 'workspace_id'):
            workspace_id = str(instance.workspace_id) if instance.workspace_id else None

        if not workspace_id:
            return  # No workspace context, skip sync

        # Get event prefix and create delete event
        sync_config = WorkspaceSyncSignalHandler.get_all_sync_models()[model_label]
        event_prefix = sync_config['event_prefix']
        event_type = f"{event_prefix}.deleted"

        # Prepare deletion data
        sync_data = {
            'deleted_entity': {
                'id': str(instance.pk),
                'type': sender._meta.model_name,
                'name': getattr(instance, 'name', None) or getattr(instance, 'title', None) or str(instance)
            },
            'deleted_at': timezone.now().isoformat()
        }

        # Trigger async sync
        trigger_workspace_sync_async.delay(
            workspace_id=workspace_id,
            event_type=event_type,
            entity_type=sender._meta.model_name,
            entity_id=str(instance.pk),
            data=sync_data,
            changed_fields=['deleted'],
            user_id=None
        )

        logger.info(f"Triggered sync for {event_type} in workspace {workspace_id}")

    except Exception as e:
        # Don't let sync errors break the delete operation
        logger.error(f"Failed to handle workspace model delete: {str(e)}")


def prepare_sync_data(instance, changed_fields: list) -> dict:
    """
    Prepare sync data for an instance based on changed fields

    Args:
        instance: Model instance
        changed_fields: List of changed field names

    Returns:
        Dict with sync data
    """
    try:
        sync_data = {}

        # Add basic instance data
        sync_data['id'] = str(instance.pk)

        # Add model-specific data based on type
        model_label = f"{instance._meta.app_label}.{instance._meta.model_name}"

        if model_label == 'store.Product':
            sync_data.update({
                'name': instance.name,
                'description': instance.description,
                'price': str(instance.price),
                'featured_image': instance.featured_image,
                'images': instance.images,
                'is_active': instance.is_active,
                'stock_quantity': instance.stock_quantity,
                'category': instance.category,
                'tags': instance.tags,
                'is_on_sale': instance.is_on_sale,
                'sale_percentage': instance.sale_percentage
            })

        elif model_label == 'core.BaseWorkspaceContentModel':
            sync_data.update({
                'title': instance.title,
                'content': instance.content,
                'excerpt': instance.excerpt,
                'featured_image': instance.featured_image,
                'is_active': instance.is_active,
                'status': instance.status,
                'tags': instance.tags,
                'slug': getattr(instance, 'slug', None)
            })

        elif model_label == 'services.Service':
            sync_data.update({
                'name': instance.name,
                'description': instance.description,
                'price': str(instance.price),
                'duration_minutes': instance.duration_minutes,
                'is_active': instance.is_active,
                'booking_enabled': instance.booking_enabled,
                'category': getattr(instance, 'category', None)
            })

        elif model_label == 'core.Workspace':
            sync_data.update({
                'name': instance.name,
                'description': instance.description,
                'type': instance.type,
                'slug': instance.slug
            })

        # Add changed fields metadata
        sync_data['_sync_metadata'] = {
            'changed_fields': changed_fields,
            'model_type': instance._meta.model_name,
            'updated_at': getattr(instance, 'updated_at', timezone.now()).isoformat()
        }

        return sync_data

    except Exception as e:
        logger.error(f"Failed to prepare sync data: {str(e)}")
        return {
            'id': str(instance.pk),
            'error': 'Failed to prepare sync data',
            '_sync_metadata': {
                'changed_fields': changed_fields,
                'model_type': instance._meta.model_name,
                'has_error': True
            }
        }


# Register signal handlers for specific models
def register_sync_signals():
    """
    Register signal handlers for all sync-enabled models
    Called when Django app is ready
    """
    try:
        # Get all registered models
        all_models = WorkspaceSyncSignalHandler.get_all_sync_models()

        for model_label in all_models.keys():
            try:
                app_label, model_name = model_label.split('.')
                model_class = apps.get_model(app_label, model_name)

                # Signals are already connected via decorators
                # This function serves as documentation of what's connected
                logger.info(f"Sync signals registered for {model_label}")

            except LookupError:
                logger.warning(f"Model {model_label} not found, skipping sync registration")

        logger.info(f"Registered sync signals for {len(all_models)} model types")

    except Exception as e:
        logger.error(f"Failed to register sync signals: {str(e)}")


# Utility functions for manual sync triggering

def trigger_manual_sync(workspace_id: str, event_type: str, data: dict, user_id: str = None):
    """
    Manually trigger a sync event
    Useful for testing or administrative actions
    """
    try:
        trigger_workspace_sync_async.delay(
            workspace_id=workspace_id,
            event_type=event_type,
            entity_type='Manual',
            entity_id='manual',
            data=data,
            changed_fields=['manual_trigger'],
            user_id=user_id
        )

        logger.info(f"Manually triggered sync: {event_type} for workspace {workspace_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to trigger manual sync: {str(e)}")
        return False


def disable_sync_for_instance(instance):
    """
    Temporarily disable sync for an instance
    Useful during bulk operations or migrations
    """
    instance._skip_sync = True


def enable_sync_for_instance(instance):
    """
    Re-enable sync for an instance
    """
    if hasattr(instance, '_skip_sync'):
        delattr(instance, '_skip_sync')


def set_sync_user_context(instance, user):
    """
    Set user context for sync operations
    Allows tracking who triggered the change
    """
    if user and hasattr(user, 'id'):
        instance._sync_user_id = str(user.id)