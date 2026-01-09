# Order Model - Customer orders for stores

from django.db import models
from django.conf import settings
from decimal import Decimal
from workspace.core.models.base_models import TenantScopedModel


class Order(TenantScopedModel):
    """
    Customer order model for store workspaces
    """
    
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('on_hold', 'On Hold'),
        ('processing', 'Processing'),
        ('unfulfilled', 'Unfulfilled'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('returned', 'Returned'),
    ]
    
    # Order identification
    order_number = models.CharField(max_length=50, unique=True, help_text="Unique order identifier")

    # ORDER SOURCE TRACKING (WhatsApp vs Payment)
    order_source = models.CharField(
        max_length=20,
        choices=[
            ('whatsapp', 'WhatsApp Order'),
            ('payment', 'Payment Gateway'),
            ('manual', 'Manual Entry')
        ],
        default='payment',
        db_index=True,
        help_text="Source of the order"
    )

    # CUSTOMER RELATIONSHIP (Shopify-style: ForeignKey + snapshot)
    customer = models.ForeignKey(
        'workspace_core.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        db_index=True,
        help_text="Reference to customer (for relationships and queries)"
    )

    # CUSTOMER SNAPSHOT (Historical data - preserved even if customer changes/deleted)
    customer_email = models.EmailField(blank=True, help_text="Customer email at time of order")
    customer_name = models.CharField(max_length=255, help_text="Customer full name at time of order")
    customer_phone = models.CharField(max_length=20, help_text="Customer phone number at time of order")

    # SHIPPING REGION FOR ANALYTICS
    shipping_region = models.CharField(
        max_length=50,
        choices=[
            ('centre', 'Centre Region'),
            ('littoral', 'Littoral Region'),
            ('west', 'West Region'),
            ('northwest', 'Northwest Region'),
            ('southwest', 'Southwest Region'),
            ('adamawa', 'Adamawa Region'),
            ('east', 'East Region'),
            ('far_north', 'Far North Region'),
            ('north', 'North Region'),
            ('south', 'South Region')
        ],
        db_index=True,
        help_text="Shipping destination region"
    )
    
    # Shipping address
    shipping_address = models.JSONField(help_text="Complete shipping address")
    billing_address = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Billing address if different from shipping (optional for MoMo/COD)"
    )
    
    # Order details
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, help_text="Order subtotal")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Shipping cost")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Tax amount")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount applied")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Final order total")

    # Discount tracking (for Option 2: deduct on payment confirmation)
    discount_code = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Applied discount code (for reference)"
    )
    applied_discount = models.ForeignKey(
        'workspace_store.Discount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Reference to applied discount (usage counted on payment)"
    )
    
    # Payment information
    PAYMENT_METHODS = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('whatsapp', 'WhatsApp Order'),
        ('mobile_money', 'Mobile Money'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cash_on_delivery',
        help_text="Payment method used"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    
    # Order metadata
    currency = models.CharField(max_length=3, default='XAF', help_text="Order currency")
    notes = models.TextField(blank=True, help_text="Order notes")
    tracking_number = models.CharField(max_length=100, blank=True, help_text="Shipping tracking number")
    
    # Timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="When order was confirmed")
    shipped_at = models.DateTimeField(null=True, blank=True, help_text="When order was shipped")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="When order was delivered")

    # Archive tracking
    is_archived = models.BooleanField(default=False, db_index=True, help_text="Whether order is archived")
    archived_at = models.DateTimeField(null=True, blank=True, help_text="When order was archived")
    
    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'status', '-created_at']),
            models.Index(fields=['workspace', 'customer_email']),
            models.Index(fields=['order_number']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['workspace', 'order_source', '-created_at']),
            models.Index(fields=['workspace', 'shipping_region', '-created_at']),
            models.Index(fields=['workspace', 'payment_method', '-created_at']),
            models.Index(fields=['workspace', 'is_archived', '-created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not provided
        if not self.order_number:
            self.order_number = self._generate_order_number()

        # Validate payment method compatibility
        self.validate_payment_method_for_order_source()

        super().save(*args, **kwargs)
    
    def _generate_order_number(self):
        """Generate unique order number"""
        import uuid
        from datetime import datetime
        
        # Format: YYYYMMDD-XXXX (date + short UUID)
        date_str = datetime.now().strftime('%Y%m%d')
        short_uuid = str(uuid.uuid4())[:8].upper()
        return f"{date_str}-{short_uuid}"
    
    @property
    def item_count(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def is_paid(self):
        """Check if order is paid"""
        return self.payment_status == 'paid'
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed'] and not self.is_paid
    
    @property
    def can_be_refunded(self):
        """Check if order can be refunded"""
        return self.payment_status == 'paid' and self.status != 'refunded'

    @property
    def requires_payment_processing(self):
        """Check if order requires payment processing"""
        return self.payment_method not in ['whatsapp', 'cash_on_delivery']

    @property
    def is_whatsapp_order(self):
        """Check if this is a WhatsApp order"""
        return self.payment_method == 'whatsapp'

    @property
    def is_cash_on_delivery(self):
        """Check if this is a cash on delivery order"""
        return self.payment_method == 'cash_on_delivery'

    @property
    def can_mark_as_paid(self):
        """Check if order can be marked as paid"""
        # WhatsApp and COD orders can be marked as paid when delivered
        return self.payment_status == 'pending'

    @property
    def can_be_archived(self):
        """Check if order can be archived"""
        # Only completed or cancelled orders can be archived
        return self.status in ['delivered', 'cancelled', 'refunded'] and not self.is_archived

    @property
    def can_be_unarchived(self):
        """Check if order can be unarchived"""
        return self.is_archived
    
    def calculate_totals(self):
        """Recalculate order totals from items"""
        self.subtotal = sum(
            item.quantity * item.unit_price 
            for item in self.items.all()
        )
        self.total_amount = (
            self.subtotal + 
            self.shipping_cost + 
            self.tax_amount - 
            self.discount_amount
        )
        self.save(update_fields=['subtotal', 'total_amount'])
    
    def update_status(self, new_status, user=None):
        """Update order status with timestamp tracking"""
        from django.utils import timezone
        
        old_status = self.status
        self.status = new_status
        
        # Update relevant timestamp fields
        now = timezone.now()
        if new_status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = now
        elif new_status == 'shipped' and not self.shipped_at:
            self.shipped_at = now
        elif new_status == 'delivered' and not self.delivered_at:
            self.delivered_at = now
        
        self.save()
        
        # Log status change (would integrate with audit log)
        return f"Order {self.order_number} status changed from {old_status} to {new_status}"
    
    def get_absolute_url(self):
        """Get order tracking URL"""
        return f"/store/{self.workspace.slug}/orders/{self.order_number}"

    def mark_as_paid(self):
        """Mark order as paid (for COD and WhatsApp orders)"""
        if not self.can_mark_as_paid:
            raise ValueError(f"Order {self.order_number} cannot be marked as paid")

        self.payment_status = 'paid'
        self.save(update_fields=['payment_status'])
        return f"Order {self.order_number} marked as paid"

    def get_whatsapp_order_summary(self):
        """Get WhatsApp order summary for admin DM"""
        items_summary = "\n".join([
            f"- {item.quantity}x {item.product_name} - {item.total_price} XAF"
            for item in self.items.all()
        ])

        return f"""
            📦 New WhatsApp Order
            Order: {self.order_number}
            Customer: {self.customer_name}
            Phone: {self.customer_phone}
            Region: {self.shipping_region}

            Items:
            {items_summary}

            Total: {self.total_amount} XAF
            """.strip()

    def validate_payment_method_for_order_source(self):
        """Validate payment method compatibility with order source"""
        # WhatsApp orders should use WhatsApp payment method
        if self.order_source == 'whatsapp' and self.payment_method != 'whatsapp':
            raise ValueError("WhatsApp orders must use WhatsApp payment method")

        # Payment gateway orders should use payment methods
        if self.order_source == 'payment' and self.payment_method == 'whatsapp':
            raise ValueError("Payment gateway orders cannot use WhatsApp payment method")


class OrderItem(models.Model):
    """Individual items within an order"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    # FOREIGN KEYS TO ACTUAL PRODUCTS (for analytics)
    product = models.ForeignKey(
        'workspace_store.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Reference to actual product (for analytics)"
    )

    variant = models.ForeignKey(
        'workspace_store.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Reference to specific variant ordered"
    )

    product_name = models.CharField(max_length=255, help_text="Product name at time of order")
    product_sku = models.CharField(max_length=100, blank=True, help_text="Product SKU at time of order")
    quantity = models.PositiveIntegerField(help_text="Quantity ordered")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit at time of order")

    # Product snapshot
    product_data = models.JSONField(default=dict, help_text="Product details at time of order")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When item was added to order")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last modification time")

    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_order_items'
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
    
    @property
    def total_price(self):
        """Calculate total price for this item"""
        return self.quantity * self.unit_price


class OrderComment(models.Model):
    """
    User-generated comments/posts on the order timeline.
    Distinct from system-generated OrderHistory.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.TextField(help_text="Comment content")
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=True, help_text="If true, visible only to staff")
    
    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_order_comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
        ]

    def __str__(self):
        return f"Comment on Order {self.order.order_number} by {self.author}"


class OrderHistory(models.Model):
    """
    System-generated timeline of order state changes.
    Tracks all order lifecycle events for audit and timeline display.
    """

    ACTION_TYPES = [
        # Order lifecycle
        ('created', 'Order Created'),
        ('status_changed', 'Status Changed'),
        ('cancelled', 'Order Cancelled'),
        ('archived', 'Order Archived'),
        ('unarchived', 'Order Unarchived'),

        # Payment tracking
        ('marked_as_paid', 'Marked as Paid'),
        ('payment_failed', 'Payment Failed'),
        ('refunded', 'Refunded'),

        # Fulfillment tracking
        ('fulfilled', 'Order Fulfilled'),
        ('unfulfilled', 'Order Unfulfilled'),
        ('partially_fulfilled', 'Partially Fulfilled'),

        # Shipping tracking
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('delivery_failed', 'Delivery Failed'),

        # Other actions
        ('notes_updated', 'Notes Updated'),
        ('customer_notified', 'Customer Notified'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='history'
    )
    workspace = models.ForeignKey(
        'workspace_core.Workspace',
        on_delete=models.CASCADE,
        related_name='order_history'
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text="Type of action performed"
    )
    details = models.JSONField(
        default=dict,
        help_text="Additional context about the action (old_status, new_status, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: Track which user performed the action (null for system actions)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the action (null for system actions)"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'store_order_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
        verbose_name_plural = 'Order histories'

    def __str__(self):
        return f"{self.get_action_display()} - Order {self.order.order_number}"

    def get_display_message(self):
        """
        Generate human-readable message for timeline display
        """
        action_messages = {
            'created': f"Order created from {self.details.get('order_source', 'unknown source')}",
            'status_changed': f"Status changed from {self.details.get('old_status', 'unknown')} to {self.details.get('new_status', 'unknown')}",
            'cancelled': f"Order cancelled{' - ' + self.details.get('reason', '') if self.details.get('reason') else ''}",
            'archived': "Order archived",
            'unarchived': "Order unarchived",
            'marked_as_paid': "Marked as paid",
            'payment_failed': "Payment failed",
            'refunded': "Order refunded",
            'fulfilled': "Order fulfilled",
            'unfulfilled': "Order unfulfilled",
            'partially_fulfilled': "Order partially fulfilled",
            'shipped': "Order shipped",
            'out_for_delivery': "Out for delivery",
            'delivered': "Order delivered",
            'delivery_failed': "Delivery failed",
            'notes_updated': "Notes updated",
            'customer_notified': "Customer notified",
        }

        return action_messages.get(self.action, f"{self.get_action_display()}")