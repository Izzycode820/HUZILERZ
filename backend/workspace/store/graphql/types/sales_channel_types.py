"""
Sales Channel GraphQL Types for Admin Store API

Provides GraphQL types for SalesChannel, ChannelProduct, and ChannelOrder models
with proper workspace scoping
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import SalesChannel, ChannelProduct, ChannelOrder
from .common_types import BaseConnection


class SalesChannelType(DjangoObjectType):
    """
    GraphQL type for SalesChannel model

    Features:
    - All sales channel fields with proper typing
    - Multi-platform support
    - Sync status tracking
    """
    id = graphene.ID(required=True)

    class Meta:
        model = SalesChannel
        fields = (
            'id', 'name', 'channel_type', 'is_active', 'base_url',
            'supports_inventory_sync', 'supports_order_sync',
            'supports_customer_sync', 'total_orders', 'total_revenue',
            'last_sync_at', 'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    active_products = graphene.Int()
    pending_orders = graphene.Int()

    def resolve_active_products(self, info):
        """Get count of active products on this channel"""
        return self.channel_products.filter(is_visible=True).count()

    def resolve_pending_orders(self, info):
        """Get count of pending orders from this channel"""
        return self.channel_orders.filter(is_synced=False).count()


class ChannelProductType(DjangoObjectType):
    """
    GraphQL type for ChannelProduct model

    Features:
    - Product visibility per channel
    - Channel-specific pricing
    - Sync tracking
    """
    id = graphene.ID(required=True)

    class Meta:
        model = ChannelProduct
        fields = (
            'id', 'product_id', 'is_visible', 'channel_price',
            'channel_inventory', 'sync_inventory', 'sync_pricing',
            'last_synced_at', 'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    sales_channel = graphene.Field(SalesChannelType)

    def resolve_sales_channel(self, info):
        """Get sales channel for this product"""
        return self.sales_channel


class ChannelOrderType(DjangoObjectType):
    """
    GraphQL type for ChannelOrder model

    Features:
    - Cross-platform order tracking
    - Sync status monitoring
    """
    id = graphene.ID(required=True)

    class Meta:
        model = ChannelOrder
        fields = (
            'id', 'channel_order_id', 'local_order_id',
            'channel_status', 'local_status', 'order_amount',
            'currency', 'customer_email', 'is_synced',
            'sync_attempts', 'last_sync_attempt', 'sync_error',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    sales_channel = graphene.Field(SalesChannelType)

    def resolve_sales_channel(self, info):
        """Get sales channel for this order"""
        return self.sales_channel


# Connection classes for pagination
class SalesChannelConnection(graphene.relay.Connection):
    """Sales channel connection with pagination support"""
    class Meta:
        node = SalesChannelType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()


class ChannelProductConnection(graphene.relay.Connection):
    """Channel product connection with pagination support"""
    class Meta:
        node = ChannelProductType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()


class ChannelOrderConnection(graphene.relay.Connection):
    """Channel order connection with pagination support"""
    class Meta:
        node = ChannelOrderType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()
