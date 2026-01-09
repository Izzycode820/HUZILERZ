# Variant GraphQL Types
# GraphQL types for product variants

import graphene
from graphene_django import DjangoObjectType
from django.db import models
from workspace.store.models.variant_model import ProductVariant
from workspace.store.graphql.types.common_types import BaseConnection
from medialib.graphql.types.media_types import MediaUploadType


class ProductVariantType(DjangoObjectType):
    """
    GraphQL type for ProductVariant model
    """
    id = graphene.ID(required=True)

    class Meta:
        model = ProductVariant
        fields = (
            'id', 'product', 'sku', 'barcode', 'option1', 'option2', 'option3',
            'price', 'compare_at_price', 'cost_price',
            'track_inventory', 'is_active', 'position',
            'featured_media',  # NEW MEDIA SYSTEM: Expose featured_media FK
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    # Simple computed fields
    display_name = graphene.String()
    effective_price = graphene.Float()
    inventory = graphene.List('workspace.store.graphql.types.inventory_types.InventoryType')
    total_stock = graphene.Int()
    is_available = graphene.Boolean()

    # MEDIA SYSTEM
    featured_image_url = graphene.String(description="Featured image URL from featured_media FK")


    def resolve_display_name(self, info):
        """Get human-readable variant name"""
        options = []
        if self.option1:
            options.append(self.option1)
        if self.option2:
            options.append(self.option2)
        if self.option3:
            options.append(self.option3)

        if options:
            return f"{self.product.name} ({', '.join(options)})"
        return self.product.name

    def resolve_effective_price(self, info):
        """Get effective price (variant price or product price)"""
        return float(self.price) if self.price is not None else float(self.product.price)

    def resolve_inventory(self, info):
        """
        Resolve inventory for this variant
        Note: Using direct query instead of DataLoader to avoid async/promise issues
        """
        from workspace.store.models import Inventory
        return Inventory.objects.filter(variant_id=self.id)

    def resolve_total_stock(self, info):
        """Get total available stock across all locations"""
        from workspace.store.models.inventory_model import Inventory
        return Inventory.objects.filter(
            variant=self,
            location__is_active=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

    def resolve_is_available(self, info):
        """Check if variant is available for purchase"""
        if not self.track_inventory:
            return True
        # Get total stock across all active locations
        from workspace.store.models.inventory_model import Inventory
        total = Inventory.objects.filter(
            variant=self,
            location__is_active=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        return total > 0

    def resolve_featured_image_url(self, info):
        """
        Get featured image URL from featured_media FK

        Returns:
            str: CDN URL of featured image, or None if not set
        """
        if self.featured_media:
            return self.featured_media.file_url
        return None


# Variant Connection for pagination
class ProductVariantConnection(graphene.relay.Connection):
    """Variant connection with pagination support"""

    class Meta:
        node = ProductVariantType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()