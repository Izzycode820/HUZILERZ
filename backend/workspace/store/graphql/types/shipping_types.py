"""
Shipping GraphQL Types for Admin Store API - Cameroon Context

Simple Package type for flexible shipping management
Perfect for informal markets with manual shipping rates
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.store.models import Package
from .common_types import BaseConnection


class PackageType(DjangoObjectType):
    """
    GraphQL type for Package model

    Features:
    - Simple shipping package configuration
    - Region-based fees stored in JSON (multiple regions per package)
    - Cameroon-specific flexibility
    """
    id = graphene.ID(required=True)

    class Meta:
        model = Package
        fields = (
            'id', 'name', 'package_type', 'size', 'weight',
            'region_fees', 'method', 'estimated_days',
            'use_as_default', 'is_active',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    # Computed fields
    product_count = graphene.Int()
    full_description = graphene.String()

    def resolve_product_count(self, info):
        """Get count of products using this package"""
        return self.products.count()

    def resolve_full_description(self, info):
        """Get full human-readable description with regions"""
        regions = ', '.join(self.region_fees.keys()) if self.region_fees else 'No regions'
        return f"{self.name} via {self.method} - {regions} ({self.estimated_days} days)"


# Connection class for pagination
class PackageConnection(graphene.relay.Connection):
    """Package connection with pagination support"""
    class Meta:
        node = PackageType

    total_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.iterable.count()
