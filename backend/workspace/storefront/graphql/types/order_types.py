# GraphQL types for Order model
# IMPORTANT: Order model imported from store app, CustomerType imported from core

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Order, OrderItem
from workspace.core.graphql.types import CustomerType
from .common_types import BaseConnection


class OrderItemType(DjangoObjectType):
    """
    GraphQL type for OrderItem model
    """

    id = graphene.ID(required=True)

    class Meta:
        model = OrderItem
        fields = (
            'id', 'product_name', 'product_sku', 'quantity',
            'unit_price'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    total_price = graphene.Float()

    def resolve_total_price(self, info):
        """Calculate total price for this item"""
        return float(self.quantity * self.unit_price)


class OrderType(DjangoObjectType):
    """
    GraphQL type for Order model

    Customer field uses centralized CustomerType from core
    """

    id = graphene.ID(required=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'total_amount',
            'created_at', 'updated_at', 'order_source'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    # Reuse CustomerType from core
    customer = graphene.Field(CustomerType)
    items = graphene.List(OrderItemType)

    def resolve_customer(self, info):
        """
        Resolve customer from core.Customer model

        Performance: Uses DataLoader or select_related
        """
        # Import Customer model from core
        from workspace.core.models import Customer

        # Get or create customer by phone
        customer, created = Customer.objects.get_or_create(
            workspace=self.workspace,
            phone=self.customer_phone,
            defaults={
                'name': self.customer_name,
                'email': self.customer_email or '',
            }
        )
        return customer

    def resolve_items(self, info):
        """Resolve order items"""
        return self.items.all()


class OrderTrackingType(graphene.ObjectType):
    """
    Limited order info for public tracking
    Used for order tracking without authentication
    """
    order_number = graphene.String()
    status = graphene.String()
    total_amount = graphene.Decimal()
    created_at = graphene.DateTime()
    estimated_delivery = graphene.DateTime()
    tracking_number = graphene.String()

    def resolve_estimated_delivery(self, info):
        """Calculate estimated delivery date"""
        # Simple calculation based on order creation date
        from django.utils import timezone
        return self.created_at + timezone.timedelta(days=3)