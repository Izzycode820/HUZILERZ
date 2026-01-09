"""
Inventory GraphQL Types for Admin Store API

Provides GraphQL types for Inventory and Location models
with proper DataLoader integration for N+1 query prevention
"""

import graphene
from graphene_django import DjangoObjectType
from django.db import models
from workspace.store.models import Inventory, Location
from workspace.store.graphql.types.common_types import BaseConnection
from medialib.graphql.types.media_types import MediaUploadType


class LocationType(DjangoObjectType):
    """
    GraphQL type for Location model

    Features:
    - All location fields with proper typing
    - Inventory relationship with DataLoader
    - Regional analytics properties
    - Cameroon region-specific data
    """
    id = graphene.ID(required=True)
    class Meta:
        model = Location
        fields = (
            'id', 'name', 'region', 'is_active', 'is_primary',
            'address_line1', 'address_line2', 'city', 'phone', 'email',
            'low_stock_threshold', 'manager_name', 'total_products',
            'total_stock_value', 'low_stock_alerts', 'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    total_stock = graphene.Int(
        description="Total stock quantity at this location"
    )
    total_value = graphene.Float(
        description="Total inventory value at this location"
    )
    low_stock_items = graphene.Int(
        description="Number of low stock items at this location"
    )
    out_of_stock_items = graphene.Int(
        description="Number of out-of-stock items at this location"
    )
    full_address = graphene.String(
        description="Formatted full address including city and region"
    )
    can_deactivate = graphene.Boolean(
        description="Whether this location can be deactivated (no inventory)"
    )

    def resolve_total_stock(self, info):
        """
        Calculate total stock at this location
        """
        total = Inventory.objects.filter(
            location=self,
            quantity__gt=0
        ).aggregate(total=models.Sum('quantity'))['total']
        return total or 0

    def resolve_total_value(self, info):
        """
        Calculate total inventory value at this location
        """
        from django.db.models import Sum, F

        total_value = Inventory.objects.filter(
            location=self
        ).aggregate(
            total_value=Sum(F('quantity') * F('variant__cost_price'))
        )['total_value']
        return float(total_value or 0)

    def resolve_low_stock_items(self, info):
        """
        Count low stock items at this location
        """
        return Inventory.objects.filter(
            location=self,
            quantity__gt=0,
            quantity__lte=self.low_stock_threshold
        ).count()

    def resolve_out_of_stock_items(self, info):
        """
        Count out-of-stock items at this location
        """
        return Inventory.objects.filter(
            location=self,
            quantity=0
        ).count()

    def resolve_full_address(self, info):
        """
        Get formatted full address
        """
        return self.full_address

    def resolve_can_deactivate(self, info):
        """
        Check if location can be deactivated (no inventory)
        """
        return self.can_deactivate()


class InventoryType(DjangoObjectType):
    """
    GraphQL type for Inventory model

    Features:
    - All inventory fields with proper typing
    - Variant and location relationships
    - Stock status properties
    - Atomic operations support
    - Shopify-style inventory tracking
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Inventory
        fields = (
            'id', 'quantity', 'onhand', 'available', 'condition',
            'is_available', 'created_at', 'updated_at', 'variant', 'location'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    variant = graphene.Field(
        'workspace.store.graphql.types.product_types.ProductVariantType',
        description="Product variant for this inventory entry"
    )
    location = graphene.Field(
        LocationType,
        description="Location where inventory is stored"
    )
    is_low_stock = graphene.Boolean(
        description="Whether inventory is below location's low stock threshold"
    )
    stock_status = graphene.String(
        description="Human-readable stock status: 'in_stock', 'low_stock', or 'out_of_stock'"
    )

    # Computed fields for inventory page display
    product_name = graphene.String(
        description="Product name derived from variant"
    )
    product_image = graphene.Field(
        MediaUploadType,
        description="Product primary image with all variations (thumbnail, WebP, etc.)"
    )
    sku = graphene.String(
        description="SKU (Stock Keeping Unit) from variant"
    )

    def resolve_variant(self, info):
        """
        Resolve variant for this inventory
        Note: Using direct query/FK access instead of DataLoader to avoid async/promise issues
        """
        return self.variant

    def resolve_location(self, info):
        """
        Resolve location for this inventory
        Note: Using direct query/FK access instead of DataLoader to avoid async/promise issues
        """
        return self.location

    def resolve_is_low_stock(self, info):
        """
        Check if inventory is low on stock
        """
        return self.is_low_stock

    def resolve_stock_status(self, info):
        """
        Get human-readable stock status
        """
        return self.stock_status

    def resolve_product_name(self, info):
        """
        Get product name from variant
        """
        if self.variant and self.variant.product:
            return self.variant.product.name
        return None

    def resolve_product_image(self, info):
        """
        Get primary product image with all variations (thumbnail, WebP, etc.)
        Returns MediaUploadType with all media metadata and URLs

        Logic:
        1. Return featured_media if set (primary image)
        2. Fallback to first image in media gallery (ordered by position)
        3. Return None if no images available

        Performance: Handles prefetched gallery_items for N+1 prevention
        """
        if not self.variant or not self.variant.product:
            return None

        product = self.variant.product

        # Primary: Return featured media if available
        if product.featured_media:
            return product.featured_media

        # Fallback: Get first image from gallery ordered by position
        # Check if gallery_items is prefetched (performance optimization)
        if hasattr(product, '_prefetched_objects_cache') and 'gallery_items' in product._prefetched_objects_cache:
            # Use prefetched data to avoid N+1 queries
            for item in product.gallery_items.all():
                if item.media.media_type == 'image':
                    return item.media
        else:
            # Query database with select_related optimization
            from workspace.store.models import ProductMediaGallery
            first_image = ProductMediaGallery.objects.filter(
                product=product,
                media__media_type='image'
            ).select_related('media').order_by('position').first()

            if first_image:
                return first_image.media

        return None

    def resolve_sku(self, info):
        """
        Get SKU from variant
        """
        if self.variant:
            return self.variant.sku
        return None


# Inventory Item Type for mutation responses
class InventoryItemType(graphene.ObjectType):
    """
    GraphQL type for inventory item in mutation responses

    Used instead of JSONString for proper type safety
    """
    id = graphene.String()
    location_id = graphene.String()
    location_name = graphene.String()
    quantity = graphene.Int()


# Inventory Connection for pagination
class InventoryConnection(graphene.relay.Connection):
    """
    Inventory connection with pagination support
    """
    class Meta:
        node = InventoryType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()
