# Variant GraphQL Queries
# GraphQL queries for product variants

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from workspace.store.graphql.types.variant_types import ProductVariantType, ProductVariantConnection
from workspace.store.models.variant_model import ProductVariant
from workspace.core.services import PermissionService
from graphql import GraphQLError

class ProductVariantFilterSet(django_filters.FilterSet):
    """
    FilterSet for ProductVariant with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    """
    class Meta:
        model = ProductVariant
        fields = {
            'sku': ['exact', 'icontains'],
            'is_active': ['exact'],
            'track_inventory': ['exact'],
        }


class VariantQueries:
    """Variant GraphQL queries"""

    # Single variant by ID
    variant = graphene.Field(
        ProductVariantType,
        id=graphene.String(required=True),
        description="Get variant by ID"
    )

    # Variants by product
    variants_by_product = graphene.List(
        ProductVariantType,
        product_id=graphene.String(required=True),
        only_active=graphene.Boolean(default_value=True),
        description="Get variants by product ID"
    )

    # Paginated variants list
    variants = DjangoFilterConnectionField(
        ProductVariantType,
        filterset_class=ProductVariantFilterSet,
        description="Get paginated list of variants"
    )

    def resolve_variant(self, info, id):
        """Resolve variant by ID with workspace scoping"""
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'variant:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return ProductVariant.objects.get(
                id=id,
                workspace=workspace,
                is_active=True
            )
        except ProductVariant.DoesNotExist:
            return None

    def resolve_variants_by_product(self, info, product_id, only_active=True):
        """Resolve variants by product ID with workspace scoping"""
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'variant:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        queryset = ProductVariant.objects.filter(
            workspace=workspace,
            product_id=product_id
        )

        if only_active:
            queryset = queryset.filter(is_active=True)

        return queryset.select_related('product').order_by('position', 'id')

    def resolve_variants(self, info, **kwargs):
        """Resolve paginated variants with workspace scoping"""
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'variant:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        return ProductVariant.objects.filter(
            workspace=workspace,
            is_active=True
        ).select_related('product').order_by('product', 'position', 'id')