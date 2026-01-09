"""
Order History Event Receivers - Timeline tracking for orders

Listens to order events and creates OrderHistory entries synchronously.
Follows CLAUDE.md principles: atomic, fast, reliable.

Design Principles:
- Sync execution: History created atomically with order (same transaction)
- Fast: Simple INSERT queries <5ms
- Graceful failure: Errors logged but don't block order operations
- Decoupled: No imports of storefront code
"""
import logging
from django.dispatch import receiver
from notifications.events import order_created, order_paid

logger = logging.getLogger('store.receivers.order_history')


@receiver(order_created)
def create_order_history_on_creation(sender, order, workspace, **kwargs):
    """
    Create OrderHistory entry when order is created from storefront.

    Triggered by: CheckoutService._emit_order_created_event()

    Execution: SYNC - runs in same transaction as order creation
    Performance: <5ms (single INSERT)

    Event Args:
        order: Order instance
        workspace: Workspace instance
    """
    try:
        from workspace.store.models import OrderHistory

        OrderHistory.objects.create(
            order=order,
            workspace=workspace,
            action='created',
            details={
                'order_source': getattr(order, 'order_source', 'unknown'),
                'payment_method': getattr(order, 'payment_method', 'unknown'),
                'total_amount': str(getattr(order, 'total_amount', 0)),
                'customer_name': getattr(order, 'customer_name', ''),
                'shipping_region': getattr(order, 'shipping_region', ''),
            },
            performed_by=None  # System action, not user-initiated
        )

        logger.info(
            f"OrderHistory created for order {order.order_number}",
            extra={'order_id': str(order.id), 'workspace_id': str(workspace.id)}
        )

    except Exception as e:
        # Log but do not raise - history failure should not block order creation
        logger.error(
            f"Failed to create OrderHistory: {e}",
            extra={'order_id': str(order.id)},
            exc_info=True
        )


@receiver(order_paid)
def create_order_history_on_payment(sender, order, workspace, **kwargs):
    """
    Create OrderHistory entry when order is marked as paid.

    Triggered by: OrderProcessingService.mark_order_as_paid()

    Execution: SYNC - atomic with payment status update
    """
    try:
        from workspace.store.models import OrderHistory

        OrderHistory.objects.create(
            order=order,
            workspace=workspace,
            action='marked_as_paid',
            details={
                'payment_method': getattr(order, 'payment_method', 'unknown'),
                'total_amount': str(getattr(order, 'total_amount', 0)),
            },
            performed_by=None  # System action
        )

        logger.info(f"OrderHistory payment entry created for order {order.order_number}")

    except Exception as e:
        logger.error(
            f"Failed to create OrderHistory payment entry: {e}",
            extra={'order_id': str(order.id)},
            exc_info=True
        )
