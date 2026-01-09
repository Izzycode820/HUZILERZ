"""
Product GraphQL Types for Admin Store API

Provides GraphQL types for Product and ProductVariant models
with proper DataLoader integration for N+1 query prevention
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Product
from .common_types import BaseConnection
from .variant_types import ProductVariantType
from medialib.graphql.types.media_types import MediaUploadType


class ProductType(DjangoObjectType):
    """
    GraphQL type for Product model

    Features:
    - All product fields with proper typing
    - Variants relationship with DataLoader
    - Category relationships
    - Stock and analytics properties
    """

    id = graphene.ID(required=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'slug', 'price', 'compare_at_price',
            'cost_price', 'charge_tax', 'payment_charges', 'charges_amount',
            'sku', 'barcode', 'brand', 'vendor', 'product_type',
            'status', 'published_at', 'category', 'tags', 'track_inventory',
            'inventory_quantity', 'allow_backorders', 'inventory_health',
            'has_variants', 'options', 'requires_shipping', 'package',
            'weight', 'meta_title', 'meta_description',
            'featured_media',  # NEW MEDIA SYSTEM: Expose featured_media FK
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    variants = graphene.List(ProductVariantType)
    total_stock = graphene.Int()
    is_in_stock = graphene.Boolean()
    is_low_stock = graphene.Boolean()
    is_on_sale = graphene.Boolean()
    sale_percentage = graphene.Int()
    profit_margin = graphene.Float()
    conversion_rate = graphene.Float()
    category_name = graphene.String()
    profit_amount = graphene.Decimal()
    stock_status = graphene.String()
    has_dimensions = graphene.Boolean()

    # MEDIA SYSTEM
    featured_image_url = graphene.String(description="Featured image URL from featured_media FK")
    media_gallery = graphene.List(MediaUploadType, description="Product media gallery (images, videos, 3D models)")

    def resolve_variants(self, info):
        """
        Resolve variants for this product with media optimization

        Performance: Uses select_related for variant featured_media (N+1 prevention)
        Note: Using direct query instead of DataLoader to avoid async/promise issues
        """
        from workspace.store.models import ProductVariant
        return ProductVariant.objects.filter(
            product_id=self.id,
            is_active=True
        ).select_related('featured_media').order_by('position')

    def resolve_total_stock(self, info):
        """
        Get total stock across variants or simple product
        """
        return self.inventory_quantity

    def resolve_is_in_stock(self, info):
        """
        Check if product is in stock
        """
        return self.inventory_quantity > 0

    def resolve_is_low_stock(self, info):
        """
        Check if product is low on stock
        """
        return 0 < self.inventory_quantity <= 5

    def resolve_is_on_sale(self, info):
        """
        Check if product is on sale
        """
        return bool(self.compare_at_price and self.compare_at_price > self.price)

    def resolve_sale_percentage(self, info):
        """
        Calculate sale percentage
        """
        if self.compare_at_price and self.price < self.compare_at_price:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0

    def resolve_profit_margin(self, info):
        """
        Calculate profit margin percentage
        """
        if self.cost_price and self.price > self.cost_price:
            return float(((self.price - self.cost_price) / self.price) * 100)
        return 0.0

    def resolve_conversion_rate(self, info):
        """
        Calculate view to inquiry conversion rate
        """
        # This would need actual view and inquiry tracking
        return 0.0

    def resolve_category_name(self, info):
        """Get category name"""
        return self.category.name if self.category else ""



    def resolve_profit_amount(self, info):
        """Calculate profit amount"""
        if self.cost_price:
            return self.price - self.cost_price
        return 0

    def resolve_stock_status(self, info):
        """Get human-readable stock status"""
        return self.inventory_health

    def resolve_has_dimensions(self, info):
        """Check if product has physical dimensions"""
        # NOTE: length, width, height fields removed - no longer supported
        return False

    def resolve_featured_image_url(self, info):
        """
        Get featured image URL from featured_media FK

        Returns:
            str: CDN URL of featured image, or None if not set
        """
        if self.featured_media:
            return self.featured_media.file_url
        return None

    def resolve_media_gallery(self, info):
        """
        Get media gallery items (images, videos, 3D models) ordered by position

        Returns:
            List[MediaUpload]: Ordered list of media items from ProductMediaGallery junction table

        Performance: Uses prefetched 'gallery_items__media' from query for N+1 prevention
        If not prefetched, falls back to optimized query with select_related
        """
        # Use prefetched data if available (from query optimization)
        if hasattr(self, '_prefetched_objects_cache') and 'gallery_items' in self._prefetched_objects_cache:
            return [item.media for item in self.gallery_items.all()]

        # Fallback: Query with optimization if not prefetched
        from workspace.store.models import ProductMediaGallery
        gallery_items = ProductMediaGallery.objects.filter(
            product=self
        ).select_related('media').order_by('position')

        return [item.media for item in gallery_items]


# Product Connection for pagination
class ProductConnection(graphene.relay.Connection):
    """
    Product connection with pagination support
    """
    class Meta:
        node = ProductType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()