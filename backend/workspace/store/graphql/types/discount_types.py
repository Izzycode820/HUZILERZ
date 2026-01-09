"""
Discount GraphQL Types for Admin Store API

Provides GraphQL types for Discount model
with proper workspace scoping
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Discount, DiscountUsage
from .common_types import BaseConnection


class DiscountType(DjangoObjectType):
    """
    GraphQL type for Discount model

    Features:
    - All discount fields with proper typing
    - Computed status properties
    - Usage tracking
    - Support for amount_off_product and buy_x_get_y discount types
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Discount
        fields = (
            'id', 'code', 'name', 'method', 'discount_type',
            # Amount off product fields
            'discount_value_type', 'value',
            # Buy X Get Y fields - Customer buys
            'customer_buys_type', 'customer_buys_quantity', 'customer_buys_value',
            'customer_buys_product_ids',
            # Buy X Get Y fields - Customer gets
            'customer_gets_quantity', 'customer_gets_product_ids',
            'bxgy_discount_type', 'bxgy_value', 'max_uses_per_order',
            # Usage limits
            'usage_limit', 'usage_count', 'usage_limit_per_customer',
            # Active dates
            'starts_at', 'ends_at',
            # Minimum purchase requirements
            'minimum_requirement_type', 'minimum_purchase_amount', 'minimum_quantity_items',
            # Customer targeting
            'applies_to_all_customers', 'customer_segmentation',
            # Product targeting
            'applies_to_all_products', 'product_ids', 'category_ids',
            # Regional targeting
            'applies_to_regions', 'applies_to_customer_types',
            # Maximum discount uses
            'limit_total_uses', 'limit_one_per_customer',
            # Combinations
            'can_combine_with_product_discounts', 'can_combine_with_order_discounts',
            # Status and analytics
            'status', 'total_discount_amount', 'total_orders',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    is_active = graphene.Boolean()
    is_expired = graphene.Boolean()
    remaining_usage = graphene.Int()

    def resolve_is_active(self, info):
        """Check if discount is currently active"""
        return self.is_active

    def resolve_is_expired(self, info):
        """Check if discount has expired"""
        return self.is_expired

    def resolve_remaining_usage(self, info):
        """Get remaining usage count"""
        if self.usage_limit:
            return max(0, self.usage_limit - self.usage_count)
        return None


class DiscountUsageType(DjangoObjectType):
    """
    GraphQL type for DiscountUsage model

    Features:
    - Usage tracking data
    - Order and customer context
    """
    id = graphene.ID(required=True)

    class Meta:
        model = DiscountUsage
        fields = (
            'id', 'discount', 'order_id', 'customer_id',
            'order_amount', 'discount_amount', 'final_amount',
            'applied_at', 'ip_address'
        )
        interfaces = (graphene.relay.Node,)

    def resolve_id(self, info):
        return str(self.id)


# Discount Connection for pagination
class DiscountConnection(graphene.relay.Connection):
    """
    Discount connection with pagination support
    """
    class Meta:
        node = DiscountType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()
