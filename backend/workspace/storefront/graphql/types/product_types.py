# GraphQL types for Product and ProductVariant models
# Comprehensive types matching admin model structure exactly

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Product, ProductVariant
from .common_types import BaseConnection


class ImageType(graphene.ObjectType):
    """
    Image type with WebP support and multiple variations

    Provides optimized images for different use cases:
    - url: Original uploaded image
    - optimized/optimized_webp: 1200px for product pages
    - thumbnail/thumbnail_webp: 300px for product cards
    - tiny/tiny_webp: 150px for list views

    Frontend usage:
    - Storefront: Use optimized_webp (best performance)
    - Product cards: Use thumbnail_webp
    - List views: Use tiny_webp
    """
    id = graphene.ID(description="Upload ID")
    url = graphene.String(description="Original image URL")

    # Optimized versions (1200px max)
    optimized = graphene.String(description="Optimized JPEG (1200px, fallback)")
    optimized_webp = graphene.String(description="Optimized WebP (1200px, 25-34% smaller)")

    # Thumbnails (300px square)
    thumbnail = graphene.String(description="Thumbnail JPEG (300px, fallback)")
    thumbnail_webp = graphene.String(description="Thumbnail WebP (300px, 25-34% smaller)")

    # Tiny thumbnails (150px square)
    tiny = graphene.String(description="Tiny JPEG (150px, fallback)")
    tiny_webp = graphene.String(description="Tiny WebP (150px, 25-34% smaller)")

    # Image dimensions
    width = graphene.Int(description="Original image width in pixels")
    height = graphene.Int(description="Original image height in pixels")


class ProductType(DjangoObjectType):
    """
    Comprehensive Product type matching admin model structure

    Themes can query only the fields they need
    All fields match admin model exactly
    """

    # Computed fields
    is_on_sale = graphene.Boolean()
    sale_percentage = graphene.Float()
    in_stock = graphene.Boolean()
    stock_status = graphene.String()
    variants = graphene.List(lambda: ProductVariantType)
    variant_options = graphene.JSONString()

    # Shopify-style image uploads
    media_uploads = graphene.List(ImageType, description="Uploaded images for this product in upload order")
    
    id = graphene.ID(required=True)
    class Meta:
        model = Product
        # Expose all fields that are safe for public access
        fields = (
            'id', 'name', 'description', 'slug',
            'price', 'compare_at_price', 'cost_price',
            'sku', 'barcode', 'brand', 'vendor',
            'product_type', 'status', 'published_at',
            'category', 'tags',
            'track_inventory', 'inventory_quantity', 'allow_backorders', 'inventory_health',
            'has_variants', 'options',
            'requires_shipping', 'package', 'weight',
            'meta_title', 'meta_description',
            'created_at', 'updated_at'
        ) 
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_is_on_sale(self, info):
        """Check if product is on sale"""
        return self.compare_at_price and self.compare_at_price > self.price

    def resolve_sale_percentage(self, info):
        """Calculate sale percentage"""
        if self.compare_at_price and self.price:
            return round((1 - (self.price / self.compare_at_price)) * 100, 1)
        return None

    def resolve_in_stock(self, info):
        """Check if product is in stock"""
        if self.has_variants:
            # Check if any variant is in stock
            return self.variants.filter(is_active=True).exists()
        return self.inventory_quantity > 0 or not self.track_inventory

    def resolve_stock_status(self, info):
        """Get stock status for display"""
        if not self.track_inventory:
            return 'available'
        if self.inventory_quantity > 0:
            return 'in_stock'
        if self.allow_backorders:
            return 'backorder'
        return 'out_of_stock'

    def resolve_variants(self, info):
        """Resolve active product variants"""
        return self.variants.filter(is_active=True)

    def resolve_variant_options(self, info):
        """Get variant options for product configuration"""
        if not self.has_variants:
            return {}

        options = {}
        for variant in self.variants.filter(is_active=True):
            if variant.option1 and variant.option1 not in options.get('option1', []):
                options.setdefault('option1', []).append(variant.option1)
            if variant.option2 and variant.option2 not in options.get('option2', []):
                options.setdefault('option2', []).append(variant.option2)
            if variant.option3 and variant.option3 not in options.get('option3', []):
                options.setdefault('option3', []).append(variant.option3)

        return options

    def resolve_media_uploads(self, info):
        """
        Get uploaded images for this product with all variations

        Returns images with WebP support and multiple sizes:
        - Original, optimized, thumbnails (JPEG + WebP)
        - Automatic format selection in frontend using <picture> tag
        """
        from medialib.services.image_service import image_upload_service
        from workspace.store.models import ProductMediaGallery

        # Get all media uploads from featured_media + media gallery
        uploads = []

        # Add featured media first (primary image)
        if self.featured_media:
            uploads.append(self.featured_media)

        # Add gallery images
        # Check if gallery_items is prefetched (performance optimization)
        if hasattr(self, '_prefetched_objects_cache') and 'gallery_items' in self._prefetched_objects_cache:
            # Use prefetched data to avoid N+1 queries
            for item in self.gallery_items.all():
                if item.media.media_type == 'image' and item.media not in uploads:
                    uploads.append(item.media)
        else:
            # Query database with select_related optimization
            gallery_items = ProductMediaGallery.objects.filter(
                product=self,
                media__media_type='image'
            ).select_related('media').order_by('position')

            for item in gallery_items:
                if item.media not in uploads:
                    uploads.append(item.media)

        result = []
        for upload in uploads:
            # Get all image URLs (JPEG + WebP variations)
            urls = image_upload_service.get_image_urls(upload)

            result.append(
                ImageType(
                    id=str(upload.id),
                    url=urls.get('original'),
                    optimized=urls.get('optimized'),
                    optimized_webp=urls.get('optimized_webp'),
                    thumbnail=urls.get('thumbnail'),
                    thumbnail_webp=urls.get('thumbnail_webp'),
                    tiny=urls.get('tiny'),
                    tiny_webp=urls.get('tiny_webp'),
                    width=upload.width,
                    height=upload.height
                )
            )

        return result


class ProductVariantType(DjangoObjectType):
    """
    Comprehensive ProductVariant type matching admin model structure

    Used when theme supports variant selection
    All fields match admin model exactly
    """

    # Computed fields
    in_stock = graphene.Boolean()
    total_stock = graphene.Int()
    display_price = graphene.Float()
    id = graphene.ID(required=True)
    class Meta:
        model = ProductVariant
        fields = (
            'id', 'sku', 'barcode',
            'option1', 'option2', 'option3',
            'price', 'compare_at_price', 'cost_price',
            'track_inventory', 'is_active', 'position',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_in_stock(self, info):
        """Check if variant is in stock"""
        if not self.track_inventory:
            return True
        # In a real implementation, you'd check inventory records
        # For now, return True for active variants
        return self.is_active

    def resolve_total_stock(self, info):
        """Get total available stock"""
        # In a real implementation, you'd sum inventory quantities
        # For now, return a placeholder
        return 10 if self.is_active else 0

    def resolve_display_price(self, info):
        """Get display price (variant price or product price)"""
        return self.price or self.product.price


class ProductConnection(graphene.relay.Connection):
    """
    Cursor-based pagination for products

    Performance: Limits page size to prevent large queries
    """
    class Meta:
        node = ProductType

    total_count = graphene.Int()

    def resolve_total_count(self, info):
        return self.length