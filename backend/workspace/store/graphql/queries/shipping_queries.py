"""
Shipping GraphQL Queries for Admin Store API - Cameroon Context

Simple Package queries for dropdown population and settings page
"""

import graphene
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.shipping_types import PackageType, PackageConnection
from workspace.store.models import Package
from workspace.core.services import PermissionService

class PackageFilterSet(django_filters.FilterSet):
    """FilterSet for Package with explicit field definitions"""

    class Meta:
        model = Package
        fields = {
            'name': ['exact', 'icontains'],
            'method': ['exact', 'icontains'],
            'package_type': ['exact'],
            'size': ['exact'],
            'is_active': ['exact'],
            'use_as_default': ['exact'],
        }


class ShippingQueries(graphene.ObjectType):
    """
    Shipping queries with workspace auto-scoping

    Simple Package queries for:
    - Dropdown on product add page
    - Settings page listing
    - Default package retrieval
    """

    packages = DjangoFilterConnectionField(
        PackageType,
        filterset_class=PackageFilterSet,
        description="List all packages with pagination and filtering (for dropdown and settings)"
    )

    package = graphene.Field(
        PackageType,
        id=graphene.ID(required=True),
        description="Get single package by ID"
    )

    active_packages = graphene.List(
        PackageType,
        description="Get active packages (for product dropdown)"
    )

    default_package = graphene.Field(
        PackageType,
        description="Get default fallback package"
    )

    def resolve_packages(self, info, **kwargs):
        """
        Resolve packages with workspace auto-scoping

        Performance: Uses proper indexing
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'shipping:view'):
        #     raise GraphQLError("Insufficient permissions to view shipping packages")
 
        return Package.objects.filter(
            workspace=workspace
        ).select_related('workspace').order_by('method', 'name')

    def resolve_package(self, info, id):
        """
        Resolve single package with workspace validation

        Security: Ensures package belongs to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'shipping:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return Package.objects.select_related('workspace').get(
                id=id,
                workspace=workspace
            )
        except Package.DoesNotExist:
            raise GraphQLError("Package not found")

    def resolve_active_packages(self, info):
        """
        Resolve active packages for product dropdown

        Performance: Filtered query with proper indexing
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'shipping:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        return Package.objects.filter(
            workspace=workspace,
            is_active=True
        ).select_related('workspace').order_by('method', 'name')

    def resolve_default_package(self, info):
        """
        Resolve default fallback package

        Used when product has no package assigned
        """
        workspace = info.context.workspace
        user = info.context.user

        # # CHECK PERMISSION
        # if not PermissionService.has_permission(user, workspace, 'shipping:view'):
        #     raise GraphQLError("Insufficient permissions to view products")
 
        try:
            return Package.objects.get(
                workspace=workspace,
                use_as_default=True,
                is_active=True
            )
        except Package.DoesNotExist:
            return None
