"""
Store Signals - Automatic Cache Invalidation
Invalidate storefront cache when products/categories change

Security & Robustness:
- Transaction-safe: Uses on_commit() to only invalidate after successful commit
- Error isolation: Task failures don't crash signal handlers
- Race condition safe: Celery task has 30s debounce lock
- No DB queries in signals: All data extracted before task queue
"""
import logging
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='workspace_store.Product')
def invalidate_cache_on_product_save(sender, instance, created, **kwargs):
    """
    Invalidate cache when product is created or updated

    Transaction Safety:
    - Only queues invalidation AFTER database commit succeeds
    - If transaction rolls back, invalidation never fires

    Triggers:
    - Product created
    - Product updated (name, price, status, etc.)

    Args:
        instance: Product instance
        created: True if new product, False if update
    """
    # Extract all needed data NOW (before potential transaction rollback)
    workspace_id = str(instance.workspace_id)
    product_id = str(instance.id)
    product_name = instance.name
    action = "created" if created else "updated"

    # Queue invalidation ONLY after transaction commits successfully
    # This prevents cache invalidation for data that might be rolled back
    def queue_invalidation():
        try:
            from workspace.hosting.tasks.cache_invalidation_tasks import invalidate_on_content_change

            logger.info(
                f"Product {action}: {product_name} (id: {product_id}) "
                f"- queuing cache invalidation for workspace {workspace_id}"
            )

            # Queue async cache invalidation (5s debounce in task)
            invalidate_on_content_change.delay(
                workspace_id=workspace_id,
                content_type='product',
                content_id=product_id
            )
        except Exception as e:
            # Task queueing failure should NOT crash the save operation
            logger.error(
                f"Failed to queue cache invalidation for product {product_id}: {str(e)}",
                exc_info=True,
                extra={
                    'workspace_id': workspace_id,
                    'product_id': product_id,
                    'action': action
                }
            )
            # Don't raise - save operation should succeed even if cache invalidation fails

    transaction.on_commit(queue_invalidation)


@receiver(post_delete, sender='workspace_store.Product')
def invalidate_cache_on_product_delete(sender, instance, **kwargs):
    """
    Invalidate cache when product is deleted

    Note: post_delete fires AFTER deletion completes, no transaction.on_commit needed

    Args:
        instance: Product instance (before deletion)
    """
    # Extract data immediately (instance will be gone after this signal)
    workspace_id = str(instance.workspace_id)
    product_id = str(instance.id)
    product_name = instance.name

    try:
        from workspace.hosting.tasks.cache_invalidation_tasks import invalidate_on_content_change

        logger.info(
            f"Product deleted: {product_name} (id: {product_id}) "
            f"- queuing cache invalidation for workspace {workspace_id}"
        )

        # Queue async cache invalidation
        invalidate_on_content_change.delay(
            workspace_id=workspace_id,
            content_type='product',
            content_id=product_id
        )
    except Exception as e:
        # Don't crash delete operation if cache invalidation fails
        logger.error(
            f"Failed to queue cache invalidation for deleted product {product_id}: {str(e)}",
            exc_info=True,
            extra={
                'workspace_id': workspace_id,
                'product_id': product_id
            }
        )


@receiver(post_save, sender='workspace_store.Category')
def invalidate_cache_on_category_save(sender, instance, created, **kwargs):
    """
    Invalidate cache when category is created or updated

    Transaction Safety:
    - Only queues invalidation AFTER database commit succeeds

    Triggers:
    - Category created
    - Category updated (name, slug, visibility, etc.)

    Args:
        instance: Category instance
        created: True if new category, False if update
    """
    # Extract all needed data NOW (before potential transaction rollback)
    workspace_id = str(instance.workspace_id)
    category_id = str(instance.id)
    category_name = instance.name
    action = "created" if created else "updated"

    # Queue invalidation ONLY after transaction commits successfully
    def queue_invalidation():
        try:
            from workspace.hosting.tasks.cache_invalidation_tasks import invalidate_on_content_change

            logger.info(
                f"Category {action}: {category_name} (id: {category_id}) "
                f"- queuing cache invalidation for workspace {workspace_id}"
            )

            # Queue async cache invalidation (5s debounce in task)
            invalidate_on_content_change.delay(
                workspace_id=workspace_id,
                content_type='category',
                content_id=category_id
            )
        except Exception as e:
            # Task queueing failure should NOT crash the save operation
            logger.error(
                f"Failed to queue cache invalidation for category {category_id}: {str(e)}",
                exc_info=True,
                extra={
                    'workspace_id': workspace_id,
                    'category_id': category_id,
                    'action': action
                }
            )

    transaction.on_commit(queue_invalidation)


@receiver(post_delete, sender='workspace_store.Category')
def invalidate_cache_on_category_delete(sender, instance, **kwargs):
    """
    Invalidate cache when category is deleted

    Note: post_delete fires AFTER deletion completes, no transaction.on_commit needed

    Args:
        instance: Category instance (before deletion)
    """
    # Extract data immediately (instance will be gone after this signal)
    workspace_id = str(instance.workspace_id)
    category_id = str(instance.id)
    category_name = instance.name

    try:
        from workspace.hosting.tasks.cache_invalidation_tasks import invalidate_on_content_change

        logger.info(
            f"Category deleted: {category_name} (id: {category_id}) "
            f"- queuing cache invalidation for workspace {workspace_id}"
        )

        # Queue async cache invalidation
        invalidate_on_content_change.delay(
            workspace_id=workspace_id,
            content_type='category',
            content_id=category_id
        )
    except Exception as e:
        # Don't crash delete operation if cache invalidation fails
        logger.error(
            f"Failed to queue cache invalidation for deleted category {category_id}: {str(e)}",
            exc_info=True,
            extra={
                'workspace_id': workspace_id,
                'category_id': category_id
            }
        )
        
        return

    try:
        from workspace.core.services.customer_service import customer_mutation_service
        
        # Use on_commit to ensure order is really saved before logging history
        def log_history():
            customer_mutation_service.log_order_event(
                workspace=workspace,
                customer_id=str(customer.id),
                action=action,
                order_data=details
            )

        transaction.on_commit(log_history)

    except Exception as e:
        logger.error(f"Failed to log order history for order {instance.id}: {str(e)}")
