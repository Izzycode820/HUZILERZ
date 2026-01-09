"""
GraphQL types for Category/Collection models
Comprehensive types matching admin model structure
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Category
from .common_types import BaseConnection


class ImageType(graphene.ObjectType):
    """
    Image type with WebP support and multiple variations

    Provides optimized images for different use cases:
    - url: Original uploaded image
    - optimized/optimized_webp: 1200px for category banners
    - thumbnail/thumbnail_webp: 300px for category cards
    - tiny/tiny_webp: 150px for list views
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


class CategoryType(DjangoObjectType):
    """
    GraphQL type for Category model - Collections in storefront

    Matches admin model structure exactly
    Themes can query only the fields they need
    """

    id = graphene.ID(required=True)
    product_count = graphene.Int()

    # Shopify-style collection image
    category_image = graphene.Field('medialib.graphql.types.media_types.MediaUploadType', description="Category banner image")

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'description', 'slug',
            'is_visible', 'is_featured', 'sort_order',
            'meta_title', 'meta_description',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_product_count(self, info):
        """Get count of published products in this collection"""
        return self.active_products.count()

    def resolve_category_image(self, info):
        """
        Get category banner image (returns MediaUploadType with url, thumbnail_url, optimized_url)
        """
        # Simply return the featured_media object
        return self.featured_media


class CategoryConnection(graphene.relay.Connection):
    """
    Cursor-based pagination for categories
    """
    class Meta:
        node = CategoryType

    total_count = graphene.Int()

    def resolve_total_count(self, info):
        return self.length