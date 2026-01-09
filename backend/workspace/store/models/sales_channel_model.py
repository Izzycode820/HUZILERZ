"""
Sales Channel Models - Shopify-style with multi-platform support
PRODUCTION-READY: Industry standard models for sales channel management
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from workspace.core.models.base_models import TenantScopedModel


class SalesChannel(TenantScopedModel):
    """
    Shopify-style sales channels for multi-platform sales

    Production Best Practices:
    - Tenant scoping for multi-workspace
    - Platform integration support
    - Performance optimizations
    """

    # Sales Channel Types
    CHANNEL_TYPE_CHOICES = [
        ('web', 'Web Store'),
        ('mobile', 'Mobile App'),
        ('onsite', 'On-site POS'),
        ('marketplace', 'Marketplace'),
        ('social', 'Social Media'),
    ]

    name = models.CharField(
        max_length=100,
        help_text="Sales channel name (e.g., 'Main Website', 'Mobile App', 'Store POS')"
    )

    channel_type = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPE_CHOICES,
        default='web'
    )

    # Channel Configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this sales channel is active"
    )

    base_url = models.URLField(
        null=True,
        blank=True,
        help_text="Base URL for this channel (for web/mobile)"
    )

    api_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="API key for channel integration"
    )

    # Channel Settings
    supports_inventory_sync = models.BooleanField(
        default=True,
        help_text="Whether this channel supports inventory synchronization"
    )

    supports_order_sync = models.BooleanField(
        default=True,
        help_text="Whether this channel supports order synchronization"
    )

    supports_customer_sync = models.BooleanField(
        default=False,
        help_text="Whether this channel supports customer synchronization"
    )

    # Analytics
    total_orders = models.PositiveIntegerField(
        default=0,
        help_text="Total orders from this channel"
    )

    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total revenue from this channel"
    )

    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last synchronization timestamp"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'workspace_store_sales_channels'
        indexes = [
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['workspace', 'channel_type']),
            models.Index(fields=['workspace', 'name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.channel_type})"


class ChannelProduct(TenantScopedModel):
    """
    Product-channel mapping for sales channel specific settings

    Production Best Practices:
    - Channel-specific product configurations
    - Performance optimizations
    - Inventory synchronization
    """

    sales_channel = models.ForeignKey(
        SalesChannel,
        on_delete=models.CASCADE,
        related_name='channel_products'
    )

    product_id = models.CharField(
        max_length=100,
        help_text="Product ID in the sales channel"
    )

    # Channel-specific Settings
    is_visible = models.BooleanField(
        default=True,
        help_text="Whether product is visible on this channel"
    )

    channel_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Channel-specific price (overrides base price)"
    )

    channel_inventory = models.IntegerField(
        default=0,
        help_text="Channel-specific inventory quantity"
    )

    sync_inventory = models.BooleanField(
        default=True,
        help_text="Whether to sync inventory with this channel"
    )

    sync_pricing = models.BooleanField(
        default=False,
        help_text="Whether to sync pricing with this channel"
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last synchronization timestamp"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'workspace_store_channel_products'
        indexes = [
            models.Index(fields=['workspace', 'sales_channel', 'is_visible']),
            models.Index(fields=['workspace', 'product_id']),
            models.Index(fields=['sales_channel', 'product_id']),
        ]
        unique_together = ['sales_channel', 'product_id']

    def __str__(self):
        return f"{self.product_id} - {self.sales_channel.name}"


class ChannelOrder(TenantScopedModel):
    """
    Order-channel mapping for sales channel order tracking

    Production Best Practices:
    - Channel-specific order data
    - Order synchronization
    - Performance optimizations
    """

    sales_channel = models.ForeignKey(
        SalesChannel,
        on_delete=models.CASCADE,
        related_name='channel_orders'
    )

    channel_order_id = models.CharField(
        max_length=100,
        help_text="Order ID in the sales channel"
    )

    local_order_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Local order ID (if synchronized)"
    )

    # Order Status
    channel_status = models.CharField(
        max_length=50,
        help_text="Order status in the sales channel"
    )

    local_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Order status in local system"
    )

    # Order Data
    order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Order amount in the sales channel"
    )

    currency = models.CharField(
        max_length=3,
        default='XAF',
        help_text="Order currency"
    )

    customer_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Customer email from sales channel"
    )

    # Sync Information
    is_synced = models.BooleanField(
        default=False,
        help_text="Whether order is synchronized with local system"
    )

    sync_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of synchronization attempts"
    )

    last_sync_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last synchronization attempt timestamp"
    )

    sync_error = models.TextField(
        null=True,
        blank=True,
        help_text="Last synchronization error message"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'workspace_store_channel_orders'
        indexes = [
            models.Index(fields=['workspace', 'sales_channel', 'is_synced']),
            models.Index(fields=['workspace', 'channel_order_id']),
            models.Index(fields=['sales_channel', 'channel_order_id']),
        ]

    def __str__(self):
        return f"{self.channel_order_id} - {self.sales_channel.name}"


class SalesChannelService:
    """
    Service class for sales channel operations

    Production Best Practices:
    - Business logic separation
    - Performance optimizations
    - Error handling
    """

    @staticmethod
    def get_active_channels(workspace):
        """Get active sales channels for workspace"""
        try:
            return SalesChannel.objects.filter(
                workspace=workspace,
                is_active=True
            ).order_by('name')

        except Exception as e:
            # Log error and return empty queryset
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting active channels for workspace {workspace.id}: {str(e)}")
            return SalesChannel.objects.none()

    @staticmethod
    def sync_channel_inventory(workspace, sales_channel, product_id, quantity):
        """Sync inventory for a product in a sales channel"""
        try:
            channel_product, created = ChannelProduct.objects.get_or_create(
                workspace=workspace,
                sales_channel=sales_channel,
                product_id=product_id,
                defaults={
                    'channel_inventory': quantity,
                    'last_synced_at': timezone.now()
                }
            )

            if not created:
                channel_product.channel_inventory = quantity
                channel_product.last_synced_at = timezone.now()
                channel_product.save()

            return True, "Inventory synchronized successfully"

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error syncing inventory for product {product_id}: {str(e)}")
            return False, "Unable to sync inventory"

    @staticmethod
    def create_channel_order(workspace, sales_channel, order_data):
        """Create a channel order from external source"""
        try:
            channel_order = ChannelOrder.objects.create(
                workspace=workspace,
                sales_channel=sales_channel,
                channel_order_id=order_data.get('order_id'),
                channel_status=order_data.get('status', 'pending'),
                order_amount=order_data.get('amount', Decimal('0.00')),
                currency=order_data.get('currency', 'XAF'),
                customer_email=order_data.get('customer_email'),
                is_synced=False
            )

            return channel_order, "Channel order created successfully"

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating channel order: {str(e)}")
            return None, "Unable to create channel order"

    @staticmethod
    def get_channel_analytics(workspace, sales_channel=None):
        """Get analytics for sales channels"""
        try:
            channels = SalesChannel.objects.filter(workspace=workspace)

            if sales_channel:
                channels = channels.filter(id=sales_channel.id)

            analytics = {
                'total_channels': channels.count(),
                'active_channels': channels.filter(is_active=True).count(),
                'total_orders': sum(channel.total_orders for channel in channels),
                'total_revenue': float(sum(channel.total_revenue for channel in channels)),
                'channels_by_type': dict(channels.values_list('channel_type').annotate(count=models.Count('id'))),
            }

            return analytics

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting channel analytics: {str(e)}")
            return {'error': 'Analytics temporarily unavailable'}