"""
Category GraphQL Types for Admin Store API

Provides GraphQL types for Category model with hierarchical support
and proper DataLoader integration for N+1 query prevention
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Category
from .common_types import BaseConnection


class BreadcrumbType(graphene.ObjectType):
    """
    Proper GraphQL type for breadcrumb navigation

    Following GraphQL Architecture Standards:
    - No JSONString usage for structured data
    - Proper typed fields for type safety
    - Clear field documentation
    """
    name = graphene.String(description="Category name in breadcrumb")
    slug = graphene.String(description="Category slug for URL")
    level = graphene.Int(description="Hierarchy level (0 for root)")


class CategoryType(DjangoObjectType):
    """
    GraphQL type for Category model

    Features:
    - All category fields with proper typing
    - Hierarchical parent/child relationships
    - Breadcrumb navigation
    - Category analytics properties
    - SEO optimization fields
    """
    id = graphene.ID(required=True) 

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'description', 'slug',
            'sort_order', 'is_visible', 'is_featured',
            'meta_title', 'meta_description',
            'featured_media',  # NEW MEDIA SYSTEM: Expose featured_media FK
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    # Shopify-style collection fields
    product_count = graphene.Int(description="Count of products in this collection")

    # MEDIA SYSTEM
    featured_image_url = graphene.String(description="Featured image URL from featured_media FK")

    def resolve_product_count(self, info):
        """
        Get count of products in this collection
        """
        return self.product_count

    def resolve_featured_image_url(self, info):
        """
        Get featured image URL from featured_media FK

        Returns:
            str: CDN URL of featured image, or None if not set
        """
        if self.featured_media:
            return self.featured_media.file_url
        return None


# Category Connection for pagination
class CategoryConnection(graphene.relay.Connection):
    """
    Category connection with pagination support
    """
    class Meta:
        node = CategoryType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()