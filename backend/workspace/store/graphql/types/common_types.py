"""
Common GraphQL Types for Admin Store API

Provides base types for pagination, filtering, and common patterns
"""

import graphene
from graphene_django import DjangoObjectType
from graphene.relay import Node


class CustomNode(Node):
    """
    Custom Node that returns plain IDs instead of base64-encoded Relay Global IDs

    This allows us to:
    - Use Connection/edges pattern for pagination (industry standard)
    - Return plain UUIDs instead of encoded IDs (Shopify/Stripe pattern)

    Result: Best of both worlds!
    """
    class Meta:
        name = 'Node'

    @staticmethod
    def to_global_id(type_name, id):
        """Return plain ID instead of base64 encoding"""
        return str(id)

    @staticmethod
    def get_node_from_global_id(info, global_id, only_type=None):
        """
        Get node from plain UUID
        Since we're using plain IDs, just pass through to parent's get_node
        """
        # The global_id is already a plain UUID, so we can use it directly
        # The graphene-django will handle the model lookup via get_node
        return Node.get_node_from_global_id(info, global_id, only_type)


class PageInfo(graphene.ObjectType):
    """
    Pagination information for Relay-style cursor pagination
    """
    has_next_page = graphene.Boolean(required=True)
    has_previous_page = graphene.Boolean(required=True)
    start_cursor = graphene.String()
    end_cursor = graphene.String()


class DateRangeInput(graphene.InputObjectType):
    """
    Input type for date range filtering
    """
    start_date = graphene.Date(required=True)
    end_date = graphene.Date(required=True)


class ProductFilterInput(graphene.InputObjectType):
    """
    Input type for filtering products
    """
    status = graphene.String()
    category = graphene.ID()
    has_variants = graphene.Boolean()
    track_inventory = graphene.Boolean()
    search = graphene.String()


class OrderFilterInput(graphene.InputObjectType):
    """
    Input type for filtering orders
    """
    status = graphene.String()
    order_source = graphene.String()
    payment_status = graphene.String()
    shipping_region = graphene.String()
    search = graphene.String()


class InventoryFilterInput(graphene.InputObjectType):
    """
    Input type for filtering inventory
    """
    location = graphene.ID()
    variant = graphene.ID()
    is_low_stock = graphene.Boolean()
    is_out_of_stock = graphene.Boolean()


class SEOType(graphene.ObjectType):
    """
    Shopify-style SEO type for Product/Category
    Reusable across all entities that need SEO
    """
    title = graphene.String(description="SEO meta title (max 60 chars recommended)")
    description = graphene.String(description="SEO meta description (max 160 chars recommended)")


class SEOInput(graphene.InputObjectType):
    """
    SEO input for mutations with validation

    Best practices for scale:
    - meta_title: 50-60 characters (Google display limit)
    - meta_description: 150-160 characters (Google display limit)
    - slug: URL-friendly, unique within workspace

    Server-side fallback:
    - If not provided, auto-populated from name/description
    - Truncated if exceeds limits
    """
    meta_title = graphene.String(description="SEO meta title (max 60 chars, auto-populated from name if empty)")
    meta_description = graphene.String(description="SEO meta description (max 160 chars, auto-populated from description if empty)")
    slug = graphene.String(description="URL-friendly slug (auto-generated from name if empty)")


# Base connection class for pagination
class BaseConnection(graphene.Connection):
    """
    Base connection class with total count
    """
    class Meta:
        abstract = True

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()


