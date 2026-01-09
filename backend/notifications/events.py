"""
Store/Storefront Domain Events

Custom signals for store operations that trigger notifications.
These events are emitted by business logic, consumed by notification receivers.

Design: Events know nothing about notifications - they are pure domain events.
"""
from django.dispatch import Signal

# ============================================================================
# ORDER EVENTS
# ============================================================================

order_created = Signal()
"""
Emitted when a new order is created via storefront checkout.
Args: order, workspace, user (workspace owner)
Triggers: New order notification to merchant
"""

order_paid = Signal()
"""
Emitted when order is marked as paid (COD/WhatsApp confirmation).
Args: order, workspace, user
Triggers: Payment confirmation notification to merchant
"""

order_cancelled = Signal()
"""
Emitted when order is cancelled by merchant or system.
Args: order, workspace, user, reason
Triggers: Order cancellation notification (future)
"""

order_status_changed = Signal()
"""
Emitted when order status changes (processing, shipped, delivered).
Args: order, workspace, old_status, new_status
Triggers: Status update notification (future)
"""

# ============================================================================
# INVENTORY EVENTS (Future)
# ============================================================================

stock_low = Signal()
"""
Emitted when product stock falls below threshold.
Args: product, workspace, current_qty, threshold
Triggers: Low stock alert to merchant
"""

stock_out = Signal()
"""
Emitted when product goes out of stock.
Args: product, workspace
Triggers: Out of stock alert to merchant
"""
