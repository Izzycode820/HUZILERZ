"""
Order Processing Tasks

Background tasks for order operations:
- Bulk order status updates
- Order fulfillment processing
- Order notifications
- WhatsApp order notifications

Separate from core bulk operations for better organization.
"""

import logging
from celery import shared_task
from django.db import transaction
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def bulk_update_order_status(self, workspace_id, order_status_updates):
    """
    Background task for bulk updating order status

    order_status_updates format: [
        {'order_id': '123', 'new_status': 'shipped'},
        ...
    ]
    """
    from workspace.core.models import Workspace
    from workspace.store.models import Order

    total = len(order_status_updates)

    try:
        workspace = Workspace.objects.get(id=workspace_id)

        for i, update in enumerate(order_status_updates):
            try:
                with transaction.atomic():
                    order = Order.objects.select_for_update().get(
                        id=update['order_id'],
                        workspace=workspace
                    )

                    # Validate status transition
                    valid_transitions = {
                        'pending': ['confirmed', 'cancelled'],
                        'confirmed': ['processing', 'cancelled'],
                        'processing': ['shipped', 'cancelled'],
                        'shipped': ['delivered'],
                        'delivered': ['refunded'],
                        'cancelled': [],
                        'refunded': []
                    }

                    current_status = order.status
                    new_status = update['new_status']

                    if new_status not in valid_transitions.get(current_status, []):
                        logger.warning(f"Invalid status transition from {current_status} to {new_status} for order {update['order_id']} - skipping")
                        continue

                    order.status = new_status
                    order.save()

                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total,
                        'percent': int((i + 1) / total * 100)
                    }
                )

            except Order.DoesNotExist:
                logger.warning(f"Order {update['order_id']} not found - skipping")
            except Exception as e:
                logger.error(f"Failed to update status for order {update['order_id']}: {e}")

        return {'status': 'completed', 'total': total}

    except Workspace.DoesNotExist:
        logger.error(f"Workspace {workspace_id} not found")
        return {'status': 'failed', 'error': 'Workspace not found'}


@shared_task(bind=True, max_retries=3)
def send_whatsapp_order_notification(self, order_id, workspace_id):
    """
    Send WhatsApp DM to merchant about new WhatsApp order.

    Args:
        order_id: UUID of the order
        workspace_id: UUID of the workspace

    Retries 3 times with exponential backoff on failure.
    """
    # Pre-flight check: Validate Twilio credentials
    if not settings.TWILIO_ENABLED:
        logger.warning(f"Twilio disabled - skipping WhatsApp notification for order {order_id}")
        return

    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.ADMIN_WHATSAPP_NUMBER]):
        logger.error(
            "Twilio credentials incomplete - check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, ADMIN_WHATSAPP_NUMBER in .env"
        )
        return

    try:
        # 1. Import Order model (avoid circular imports)
        from workspace.store.models import Order

        # 2. Get order with workspace scoping
        order = Order.objects.filter(
            id=order_id,
            workspace_id=workspace_id
        ).first()

        if not order:
            logger.warning(f"Order {order_id} not found in workspace {workspace_id}")
            return

        # 3. Get message content from existing model method
        message_body = order.get_whatsapp_order_summary()

        # 4. Initialize Twilio client
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

        # 5. Send WhatsApp message
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=settings.ADMIN_WHATSAPP_NUMBER  # TODO: Make workspace-specific
        )

        logger.info(f"WhatsApp sent for order {order.order_number}, SID: {message.sid}, Status: {message.status}")

    except Exception as e:
        logger.error(f"WhatsApp task failed for order {order_id}: {e}", exc_info=True)
        # Retry with exponential backoff (60s, 120s, 240s)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))