"""
Analytics Signal Handlers

Signal-based event tracking for commerce analytics.
Uses EventTrackingService for tier-gated event creation.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from uuid import uuid4
import logging

logger = logging.getLogger('workspace.analytics.signals')


@receiver(post_save, sender='workspace_store.Order')
def track_order_events(sender, instance, created, **kwargs):
    """
    Track order-related analytics events.
    
    Events:
    - order_completed: When order is created with paid status
    - customer_created: When this is the customer's first order
    
    Performance: Non-blocking, graceful failure
    """
    if not created:
        return
    
    try:
        from workspace.analytics.services import EventTrackingService
        from workspace.store.models import Order
        
        workspace = instance.workspace
        service = EventTrackingService(workspace)
        
        # Generate session ID (use from order metadata if available)
        session_id = uuid4()
        if hasattr(instance, 'metadata') and instance.metadata:
            session_str = instance.metadata.get('session_id')
            if session_str:
                try:
                    from uuid import UUID
                    session_id = UUID(session_str)
                except (ValueError, TypeError):
                    pass
        
        # Track order completed
        if instance.payment_status == 'paid':
            service.track_order_completed(instance, session_id)
        elif instance.payment_status == 'failed':
            service.track_order_failed(instance, session_id)
        else:
            # For pending orders (COD, WhatsApp), still track as completed
            # since they represent real intent
            if instance.order_source in ('whatsapp', 'manual') or instance.payment_method == 'cash_on_delivery':
                service.track_order_completed(instance, session_id)
        
        # Check if this is a new customer (first order)
        if instance.customer_email:
            previous_orders = Order.objects.filter(
                workspace=workspace,
                customer_email=instance.customer_email,
                created_at__lt=instance.created_at
            ).exclude(id=instance.id).count()
            
            if previous_orders == 0:
                customer_id = None
                if instance.customer:
                    customer_id = instance.customer.id
                
                service.track_customer_created(
                    session_id=session_id,
                    customer_id=customer_id or uuid4(),
                    is_first_order=True
                )
        
        logger.debug(f"Tracked order events for order {instance.order_number}")
        
    except Exception as e:
        # Never fail order creation due to analytics
        logger.error(f"Failed to track order events: {e}", exc_info=True)


@receiver(post_save, sender='workspace_store.Transaction')
def track_payment_success(sender, instance, created, **kwargs):
    """
    Track successful payment for COD/WhatsApp orders marked as paid.
    
    When an order is marked as paid (via mark_as_paid mutation),
    track the order_completed event if not already tracked.
    """
    if not created:
        return
    
    try:
        if instance.status != 'completed':
            return
        
        from workspace.analytics.services import EventTrackingService
        
        order = instance.order
        workspace = order.workspace
        service = EventTrackingService(workspace)
        
        # Generate session ID
        session_id = uuid4()
        
        # Track order completed (service handles deduplication via gating)
        service.track_order_completed(order, session_id)
        
        logger.debug(f"Tracked payment success for order {order.order_number}")
        
    except Exception as e:
        logger.error(f"Failed to track payment success: {e}", exc_info=True)


# Product stock tracking for future use
_stock_cache = {}


@receiver(pre_save, sender='workspace_store.Product')
def cache_old_stock(sender, instance, **kwargs):
    """Cache old stock value before save for comparison"""
    if instance.id:
        try:
            from workspace.store.models import Product
            old_instance = Product.objects.get(id=instance.id)
            _stock_cache[instance.id] = old_instance.inventory_quantity
        except Exception:
            pass


@receiver(post_save, sender='workspace_store.Product')
def track_inventory_changes(sender, instance, created, **kwargs):
    """
    Track inventory stock level changes.
    
    Note: This is for internal activity tracking, not customer analytics.
    Customer-facing events are tracked via EventTrackingService.
    """
    if created:
        return
    
    old_stock = _stock_cache.pop(instance.id, None)
    if old_stock is None:
        return
    
    new_stock = instance.inventory_quantity
    
    # Log significant stock changes for debugging
    if new_stock <= 5 and new_stock > 0 and old_stock > 5:
        logger.info(
            f"Low stock alert: {instance.name} has {new_stock} units "
            f"(was {old_stock}) in workspace {instance.workspace_id}"
        )
    elif new_stock == 0 and old_stock > 0:
        logger.warning(
            f"Out of stock: {instance.name} in workspace {instance.workspace_id}"
        )