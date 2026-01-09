"""
Sales Channel GraphQL Queries for Admin Store API

Provides sales channel queries with workspace auto-scoping
Critical for multi-platform sales management
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.sales_channel_types import (
    SalesChannelType, SalesChannelConnection,
    ChannelProductType, ChannelProductConnection,
    ChannelOrderType, ChannelOrderConnection
)
from workspace.store.models import SalesChannel, ChannelProduct, ChannelOrder
from workspace.core.services import PermissionService

class SalesChannelFilterSet(django_filters.FilterSet):
    """
    FilterSet for SalesChannel with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    """
    class Meta:
        model = SalesChannel
        fields = {
            'name': ['exact', 'icontains'],
            'channel_type': ['exact'],
            'is_active': ['exact'],
        }


class ChannelProductFilterSet(django_filters.FilterSet):
    """FilterSet for ChannelProduct"""
    class Meta:
        model = ChannelProduct
        fields = {
            'product_id': ['exact'],
            'is_visible': ['exact'],
        }


class ChannelOrderFilterSet(django_filters.FilterSet):
    """FilterSet for ChannelOrder"""
    class Meta:
        model = ChannelOrder
        fields = {
            'channel_order_id': ['exact'],
            'is_synced': ['exact'],
        }


class SalesChannelQueries(graphene.ObjectType):
    """
    Sales Channel queries with workspace auto-scoping

    Security: All queries automatically scoped to authenticated workspace
    Performance: Uses select_related for N+1 query prevention
    """

    sales_channels = DjangoFilterConnectionField(
        SalesChannelType,
        filterset_class=SalesChannelFilterSet,
        description="List all sales channels with pagination and filtering"
    )

    sales_channel = graphene.Field(
        SalesChannelType,
        id=graphene.ID(required=True),
        description="Get single sales channel by ID"
    )

    channel_products = DjangoFilterConnectionField(
        ChannelProductType,
        filterset_class=ChannelProductFilterSet,
        description="List channel products with pagination and filtering"
    )

    channel_product = graphene.Field(
        ChannelProductType,
        id=graphene.ID(required=True),
        description="Get single channel product by ID"
    )

    channel_orders = DjangoFilterConnectionField(
        ChannelOrderType,
        filterset_class=ChannelOrderFilterSet,
        description="List channel orders with pagination and filtering"
    )

    channel_order = graphene.Field(
        ChannelOrderType,
        id=graphene.ID(required=True),
        description="Get single channel order by ID"
    )

    active_channels = graphene.List(
        SalesChannelType,
        description="Get active sales channels"
    )

    def resolve_sales_channels(self, info, **kwargs):
        """
        Resolve sales channels with workspace auto-scoping

        Performance: Uses select_related and proper indexing
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'sales_channel:view'):
            raise GraphQLError("Insufficient permissions to view products")
 
        return SalesChannel.objects.filter(
            workspace=workspace
        ).select_related('workspace').order_by('-created_at')

    def resolve_sales_channel(self, info, id):
        """
        Resolve single sales channel with workspace validation

        Security: Ensures sales channel belongs to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'sales_channel:view'):
            raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return SalesChannel.objects.select_related('workspace').get(
                id=id,
                workspace=workspace
            )
        except SalesChannel.DoesNotExist:
            raise GraphQLError("Sales channel not found")

    def resolve_channel_products(self, info, **kwargs):
        """
        Resolve channel products with workspace auto-scoping
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'sales_channel:view'):
            raise GraphQLError("Insufficient permissions to view products")
 
        return ChannelProduct.objects.filter(
            workspace=workspace
        ).select_related('sales_channel', 'workspace').order_by('-created_at')

    def resolve_channel_product(self, info, id):
        """
        Resolve single channel product with workspace validation
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'sales_channel:view'):
            raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return ChannelProduct.objects.select_related('sales_channel', 'workspace').get(
                id=id,
                workspace=workspace
            )
        except ChannelProduct.DoesNotExist:
            raise GraphQLError("Channel product not found")

    def resolve_channel_orders(self, info, **kwargs):
        """
        Resolve channel orders with workspace auto-scoping
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'sales_channel:view'):
            raise GraphQLError("Insufficient permissions to view products")
 
        return ChannelOrder.objects.filter(
            workspace=workspace
        ).select_related('sales_channel', 'workspace').order_by('-created_at')

    def resolve_channel_order(self, info, id):
        """
        Resolve single channel order with workspace validation
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'sales_channel:view'):
            raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return ChannelOrder.objects.select_related('sales_channel', 'workspace').get(
                id=id,
                workspace=workspace
            )
        except ChannelOrder.DoesNotExist:
            raise GraphQLError("Channel order not found")

    def resolve_active_channels(self, info):
        """
        Resolve active sales channels

        Performance: Filtered query with proper indexing
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'sales_channel:view'):
            raise GraphQLError("Insufficient permissions to view products")
 
        return SalesChannel.objects.filter(
            workspace=workspace,
            is_active=True
        ).select_related('workspace').order_by('name')
