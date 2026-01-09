"""
Customer GraphQL Types - Shared across all workspace types
Production-ready types matching product_types.py pattern
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.core.models.customer_model import Customer
from workspace.store.graphql.types.common_types import BaseConnection


class CustomerHistoryType(DjangoObjectType):
    """
    GraphQL type for Customer History
    """
    class Meta:
        from workspace.core.models.customer_model import CustomerHistory
        model = CustomerHistory
        fields = ('id', 'action', 'details', 'created_at', 'performed_by')
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    details = graphene.JSONString()
    display_message = graphene.String()

    def resolve_display_message(self, info):
        return self.get_display_message()


class CustomerType(DjangoObjectType):
    """
    GraphQL type for Customer model

    Features:
    - All customer fields with proper typing
    - Cameroon region support
    - Order tracking
    - Address management for order creation
    """
    id = graphene.ID(required=True) 

    class Meta:
        model = Customer
        fields = (
            'id', 'name', 'phone', 'email', 'customer_type',
            'city', 'region', 'address', 'tags',
            'total_orders', 'total_spent',
            'first_order_at', 'last_order_at',
            'sms_notifications', 'whatsapp_notifications',
            'is_active', 'verified_at',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    # Computed properties from model
    is_verified = graphene.Boolean()
    has_email = graphene.Boolean()
    is_frequent_buyer = graphene.Boolean()
    average_order_value = graphene.Decimal()
    lifetime_value = graphene.Decimal()
    is_high_value = graphene.Boolean()
    
    # History List (Pattern matching ProductType.variants)
    history = graphene.List(CustomerHistoryType)

    def resolve_history(self, info):
        """
        Resolve customer history
        """
        return self.history.all().order_by('-created_at')

    def resolve_is_verified(self, info):
        """Check if customer is verified"""
        return self.is_verified

    def resolve_has_email(self, info):
        """Check if customer has email"""
        return bool(self.email)

    def resolve_is_frequent_buyer(self, info):
        """Check if customer is frequent buyer (3+ orders)"""
        return self.total_orders >= 3

    def resolve_average_order_value(self, info):
        """Calculate average order value"""
        return self.average_order_value

    def resolve_lifetime_value(self, info):
        """Get customer lifetime value"""
        return self.lifetime_value

    def resolve_is_high_value(self, info):
        """Check if customer is high value"""
        return self.is_high_value


# Customer Info Input (for quick order creation)
class CustomerInfoInput(graphene.InputObjectType):
    """
    Input type for customer information
    Simplified for Cameroon context
    """
    name = graphene.String()
    phone = graphene.String()
    email = graphene.String()
    city = graphene.String()
    region = graphene.String()
    address = graphene.String()


# Customer Connection for pagination
class CustomerConnection(graphene.relay.Connection):
    """
    Customer connection with pagination support
    """
    class Meta:
        node = CustomerType

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()
