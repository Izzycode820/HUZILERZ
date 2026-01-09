"""
Celery tasks for store operations

Provides background task processing for:
- Bulk operations (products, orders, inventory)
- Media processing (images, videos, 3D models)

Critical for performance and user experience
"""

from .bulk_operations import (
    bulk_publish_products,
    bulk_unpublish_products,
    bulk_update_prices,
    bulk_delete_products,
    bulk_update_inventory,
)

# Order processing tasks
from .order_tasks import bulk_update_order_status, send_whatsapp_order_notification

__all__ = [
    # Bulk operations
    'bulk_publish_products',
    'bulk_unpublish_products',
    'bulk_update_prices',
    'bulk_delete_products',
    'bulk_update_inventory',
    
    # Order processing
    'bulk_update_order_status',
    'send_whatsapp_order_notification',
]