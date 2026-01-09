"""
Store Event Receivers - Handle order/customer timeline tracking

Listens to storefront events and creates history entries asynchronously.
Follows CLAUDE.md principles: decoupled, async, graceful failure.

Design Principles:
- Decoupled: No direct imports between storefront and store history models
- Async: Use Celery tasks for non-blocking history creation
- Graceful failure: History errors never block order/customer operations
- Comprehensive logging: All events logged for debugging
"""
import logging
from django.dispatch import receiver
from notifications.events import order_created, order_paid

logger = logging.getLogger('store.receivers')


@receiver(order_created)
def create_order_history_on_creation(sender, order, workspace, **kwargs):
    """
    Create OrderHistory entry when order is created from storefront.

    Triggered by: CheckoutService._emit_order_created_event()

    Reliability: Async via Celery - does not block checkout

    Event Args:
        order: Order instance
        workspace: Workspace instance
    """
    try:
        from workspace.store.tasks.order_tasks import create_order_history_entry

        # Queue async task to create history entry
        create_order_history_entry.delay(
            order_id=str(order.id),
            workspace_id=str(workspace.id),
            action='created',
            details={
                'order_source': getattr(order, 'order_source', 'unknown'),
                'payment_method': getattr(order, 'payment_method', 'unknown'),
                'total_amount': str(getattr(order, 'total_amount', 0)),
                'customer_name': getattr(order, 'customer_name', ''),
            }
        )

        logger.info(
            f"OrderHistory creation queued for order {order.id}",
            extra={'order_id': str(order.id), 'workspace_id': str(workspace.id)}
        )

    except Exception as e:
        # Log but do not raise - history failure should not block order creation
        logger.error(
            f"Failed to queue OrderHistory creation: {e}",
            extra={'order_id': str(order.id)},
            exc_info=True
        )


@receiver(order_paid)
def create_order_history_on_payment(sender, order, workspace, **kwargs):
    """
    Create OrderHistory entry when order is marked as paid.

    Triggered by: OrderProcessingService.mark_order_as_paid()

    Reliability: Async via Celery
    """
    try:
        from workspace.store.tasks.order_tasks import create_order_history_entry

        create_order_history_entry.delay(
            order_id=str(order.id),
            workspace_id=str(workspace.id),
            action='marked_as_paid',
            details={
                'payment_method': getattr(order, 'payment_method', 'unknown'),
                'total_amount': str(getattr(order, 'total_amount', 0)),
            }
        )

        logger.info(f"OrderHistory payment entry queued for order {order.id}")

    except Exception as e:
        logger.error(
            f"Failed to queue OrderHistory payment entry: {e}",
            extra={'order_id': str(order.id)},
            exc_info=True
        )
