"""
Order GraphQL Queries for Admin Store API

Provides order queries with workspace auto-scoping and Cameroon-specific filtering
Critical for order management and regional analytics
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.order_types import OrderType, OrderConnection
from workspace.store.models import Order
from workspace.core.services import PermissionService

class OrderFilterSet(django_filters.FilterSet):
    """
    FilterSet for Order with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    Regional: Supports Cameroon's 10 regions filtering
    """
    class Meta:
        model = Order
        fields = {
            'order_number': ['exact', 'icontains'],
            'status': ['exact'],
            'order_source': ['exact'],
            'payment_status': ['exact'],
            'payment_method': ['exact'],
            'shipping_region': ['exact'],
            'customer_email': ['exact', 'icontains'],
            'customer_name': ['icontains'],
            'created_at': ['exact', 'gte', 'lte'],
            'total_amount': ['exact', 'gte', 'lte'],
            'is_archived': ['exact'],
        }


class OrderQueries(graphene.ObjectType):
    """
    Order queries with workspace auto-scoping

    Security: All queries automatically scoped to authenticated workspace
    Performance: Uses DataLoaders for N+1 query prevention
    Regional: Supports Cameroon's 10 regions with regional filtering
    """

    orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilterSet,
        description="List all orders with pagination and filtering"
    )

    order = graphene.Field(
        OrderType,
        id=graphene.ID(required=True),
        description="Get single order by ID"
    )

    orders_by_status = graphene.List(
        OrderType,
        status=graphene.String(required=True),
        description="Get orders by status"
    )

    orders_by_region = graphene.List(
        OrderType,
        region=graphene.String(required=True),
        description="Get orders by shipping region"
    )

    orders_by_source = graphene.List(
        OrderType,
        source=graphene.String(required=True),
        description="Get orders by source (whatsapp, payment, manual)"
    )

    recent_orders = graphene.List(
        OrderType,
        limit=graphene.Int(default_value=10),
        description="Get recent orders"
    )

    def resolve_orders(self, info, **kwargs):
        """
        Resolve orders with workspace auto-scoping

        Performance: Uses select_related for customer data
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:view'):
            raise GraphQLError("Insufficient permissions to view products")

        return Order.objects.filter(
            workspace=workspace
        ).select_related().order_by('-created_at')

    def resolve_order(self, info, id):
        """
        Resolve single order with workspace validation

        Security: Ensures order belongs to authenticated workspace
        Performance: Uses select_related for related fields
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:view'):
            raise GraphQLError("Insufficient permissions to view products")

        try:
            return Order.objects.select_related().get(
                id=id,
                workspace=workspace
            )
        except Order.DoesNotExist:
            raise GraphQLError("Order not found")

    def resolve_orders_by_status(self, info, status):
        """
        Resolve orders by status

        Performance: Efficient query with status indexing
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:view'):
            raise GraphQLError("Insufficient permissions to view products")

        return Order.objects.filter(
            workspace=workspace,
            status=status
        ).select_related().order_by('-created_at')

    def resolve_orders_by_region(self, info, region):
        """
        Resolve orders by shipping region

        Performance: Uses regional indexing
        Security: Workspace auto-scoped
        Regional: Cameroon's 10 regions supported
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:view'):
            raise GraphQLError("Insufficient permissions to view products")

        # Validate region is one of Cameroon's 10 regions (must match DB model choices)
        valid_regions = [
            'centre', 'littoral', 'west', 'northwest', 'southwest',
            'adamawa', 'east', 'far_north', 'north', 'south'
        ]

        if region not in valid_regions:
            raise GraphQLError(f"Invalid region. Must be one of: {', '.join(valid_regions)}")

        return Order.objects.filter(
            workspace=workspace,
            shipping_region=region
        ).select_related().order_by('-created_at')

    def resolve_orders_by_source(self, info, source):
        """
        Resolve orders by source (WhatsApp, Payment, Manual)

        Performance: Uses source indexing
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:view'):
            raise GraphQLError("Insufficient permissions to view products")

        valid_sources = ['whatsapp', 'payment', 'manual']

        if source not in valid_sources:
            raise GraphQLError("Invalid order source")

        return Order.objects.filter(
            workspace=workspace,
            order_source=source
        ).select_related().order_by('-created_at')

    def resolve_recent_orders(self, info, limit):
        """
        Resolve recent orders

        Performance: Limited query with proper indexing
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'order:view'):
            raise GraphQLError("Insufficient permissions to view products")

        return Order.objects.filter(
            workspace=workspace
        ).select_related().order_by('-created_at')[:limit]