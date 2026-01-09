"""
Inventory GraphQL Queries for Admin Store API

Provides inventory queries with workspace auto-scoping and regional filtering
Critical for Cameroon multi-region inventory management
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.inventory_types import InventoryType, LocationType, InventoryConnection
from workspace.store.models import Inventory, Location
from workspace.core.services import PermissionService

class InventoryFilterSet(django_filters.FilterSet):
    """
    FilterSet for Inventory with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django_filter 2.0+ for security
    Regional: Supports Cameroon's 10 regions filtering
    Shopify-style: Only essential fields for simple inventory tracking
    """
    class Meta:
        model = Inventory
        fields = {
            'variant': ['exact'],
            'location': ['exact'],
            'quantity': ['exact', 'gte', 'lte'],
            'is_available': ['exact'],
        }


class InventoryQueries(graphene.ObjectType):
    """
    Inventory queries with workspace auto-scoping

    Security: All queries automatically scoped to authenticated workspace
    Performance: Uses DataLoaders for N+1 query prevention
    Regional: Supports Cameroon's 10 regions with regional filtering
    """

    inventory = DjangoFilterConnectionField(
        InventoryType,
        filterset_class=InventoryFilterSet,
        description="List all inventory with pagination and filtering"
    )

    locations = graphene.List(
        LocationType,
        description="Get all locations for authenticated workspace"
    )

    inventory_by_variant = graphene.List(
        InventoryType,
        variant_id=graphene.ID(required=True),
        description="Get inventory for specific variant across all regions"
    )

    inventory_by_location = graphene.List(
        InventoryType,
        location_id=graphene.ID(required=True),
        description="Get inventory for specific location"
    )

    low_stock_items = graphene.List(
        InventoryType,
        threshold=graphene.Int(default_value=5),
        description="Get low stock items across all regions"
    )

    def resolve_inventory(self, info, **kwargs):
        """
        Resolve inventory with workspace auto-scoping

        Performance: Uses select_related for variant, location, and variant media (N+1 prevention)
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'inventory:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        return Inventory.objects.filter(
            workspace=workspace
        ).select_related(
            'variant__featured_media',  # Prevent N+1 for variant images
            'variant__product',  # Prevent N+1 for product data
            'location'
        ).order_by('location__name', 'variant__sku')

    def resolve_locations(self, info):
        """
        Resolve locations for authenticated workspace

        Performance: Returns Cameroon's 10 regions for workspace
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'inventory:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        return Location.objects.filter(
            workspace=workspace,
            is_active=True
        ).order_by('name')

    def resolve_inventory_by_variant(self, info, variant_id):
        """
        Resolve inventory for specific variant across all regions

        Performance: Uses select_related for variant media and location
        Security: Validates variant belongs to workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'inventory:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        try:
            # Verify variant belongs to workspace
            from workspace.store.models import ProductVariant
            variant = ProductVariant.objects.select_related('featured_media').get(
                id=variant_id,
                workspace=workspace
            )

            return Inventory.objects.filter(
                workspace=workspace,
                variant=variant
            ).select_related('location').order_by('location__name')

        except ProductVariant.DoesNotExist:
            raise GraphQLError("Variant not found")

    def resolve_inventory_by_location(self, info, location_id):
        """
        Resolve inventory for specific location

        Performance: Uses select_related for variant data and variant media
        Security: Validates location belongs to workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'inventory:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        try:
            # Verify location belongs to workspace
            location = Location.objects.get(
                id=location_id,
                workspace=workspace
            )

            return Inventory.objects.filter(
                workspace=workspace,
                location=location
            ).select_related(
                'variant__featured_media',  # Prevent N+1 for variant images
                'variant__product'  # Prevent N+1 for product data
            ).order_by('variant__sku')

        except Location.DoesNotExist:
            raise GraphQLError("Location not found")

    def resolve_low_stock_items(self, info, threshold):
        """
        Resolve low stock items across all regions

        Performance: Efficient query with proper indexing and variant media optimization
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'inventory:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        return Inventory.objects.filter(
            workspace=workspace,
            quantity__gt=0,  # Not out of stock
            quantity__lte=threshold
        ).select_related(
            'variant__featured_media',  # Prevent N+1 for variant images
            'variant__product',  # Prevent N+1 for product data
            'location'
        ).order_by('quantity', 'location__name')