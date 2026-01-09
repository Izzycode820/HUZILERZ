"""
Common GraphQL Types for Notifications API

Provides base types for pagination, filtering, and common patterns
Matches store/graphql/types/common_types.py patterns
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
        return Node.get_node_from_global_id(info, global_id, only_type)


class PageInfo(graphene.ObjectType):
    """
    Pagination information for Relay-style cursor pagination
    """
    has_next_page = graphene.Boolean(required=True)
    has_previous_page = graphene.Boolean(required=True)
    start_cursor = graphene.String()
    end_cursor = graphene.String()


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


__all__ = [
    'CustomNode',
    'PageInfo',
    'BaseConnection'
]
