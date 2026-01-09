"""
Discount GraphQL Queries for Admin Store API

Provides discount queries with workspace auto-scoping
Critical for discount management and validation
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.discount_types import DiscountType, DiscountConnection
from workspace.store.models import Discount
from workspace.core.services import PermissionService

class DiscountFilterSet(django_filters.FilterSet):
    """
    FilterSet for Discount with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    """
    class Meta:
        model = Discount
        fields = {
            'code': ['exact', 'icontains'],
            'name': ['icontains'],
            'method': ['exact'],
            'discount_type': ['exact'],
            'status': ['exact'],
        }


class DiscountQueries(graphene.ObjectType):
    """
    Discount queries with workspace auto-scoping

    Security: All queries automatically scoped to authenticated workspace
    Performance: Uses select_related for N+1 query prevention
    """

    discounts = DjangoFilterConnectionField(
        DiscountType,
        filterset_class=DiscountFilterSet,
        description="List all discounts with pagination and filtering"
    )

    discount = graphene.Field(
        DiscountType,
        id=graphene.ID(required=True),
        description="Get single discount by ID"
    )

    discount_by_code = graphene.Field(
        DiscountType,
        code=graphene.String(required=True),
        description="Get discount by code"
    )

    active_discounts = graphene.List(
        DiscountType,
        limit=graphene.Int(default_value=50),
        description="Get active discounts"
    )

    def resolve_discounts(self, info, **kwargs):
        """
        Resolve discounts with workspace auto-scoping

        Performance: Uses select_related and proper indexing
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'discount:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        return Discount.objects.filter(
            workspace=workspace
        ).select_related('workspace').order_by('-created_at')

    def resolve_discount(self, info, id):
        """
        Resolve single discount with workspace validation

        Security: Ensures discount belongs to authenticated workspace
        Performance: Uses select_related for workspace data
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'discount:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return Discount.objects.select_related('workspace').get(
                id=id,
                workspace=workspace
            )
        except Discount.DoesNotExist:
            raise GraphQLError("Discount not found")

    def resolve_discount_by_code(self, info, code):
        """
        Resolve discount by code with workspace validation

        Security: Ensures discount belongs to authenticated workspace
        Performance: Code normalized and indexed
        """
        workspace = info.context.workspace
        normalized_code = code.upper().strip()
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'discount:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return Discount.objects.select_related('workspace').get(
                workspace=workspace,
                code=normalized_code
            )
        except Discount.DoesNotExist:
            raise GraphQLError(f"Discount with code {code} not found")

    def resolve_active_discounts(self, info, limit):
        """
        Resolve active discounts

        Performance: Limited query with proper indexing
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'discount:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        return Discount.objects.filter(
            workspace=workspace,
            status='active'
        ).select_related('workspace').order_by('-created_at')[:limit]
