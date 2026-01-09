"""
Category GraphQL Queries for Admin Store API

Provides category queries with workspace auto-scoping and hierarchical support
Critical for category management and navigation
"""

import graphene
import django_filters
from django.db import models
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from ..types.category_types import CategoryType, CategoryConnection
from ..types.product_types import ProductType
from workspace.store.models import Category, Product
from workspace.core.services import PermissionService

class CategoryFilterSet(django_filters.FilterSet):
    """
    FilterSet for Category with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    """

    # Custom filters for search and featured
    search = django_filters.CharFilter(method='filter_search', help_text="Search by name or description")
    is_featured = django_filters.BooleanFilter(field_name='is_featured', help_text="Filter by featured status")

    class Meta:
        model = Category
        fields = {
            'name': ['exact', 'icontains'],
            'slug': ['exact'],
            'is_visible': ['exact'],
            'is_featured': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        """
        Search filter that searches both name and description
        """
        if value:
            return queryset.filter(
                models.Q(name__icontains=value) |
                models.Q(description__icontains=value)
            )
        return queryset


class CategoryQueries(graphene.ObjectType):
    """
    Category queries with workspace auto-scoping

    Security: All queries automatically scoped to authenticated workspace
    Performance: Uses DataLoaders for N+1 query prevention
    Hierarchical: Supports parent/child relationships and tree navigation
    """

    categories = DjangoFilterConnectionField(
        CategoryType,
        filterset_class=CategoryFilterSet,
        description="List all categories with pagination and filtering"
    )

    category = graphene.Field(
        CategoryType,
        id=graphene.ID(required=True),
        description="Get single category by ID"
    )

    category_by_slug = graphene.Field(
        CategoryType,
        slug=graphene.String(required=True),
        description="Get category by slug"
    )

    featured_categories = graphene.List(
        CategoryType,
        limit=graphene.Int(default_value=6),
        description="Get featured categories for homepage"
    )

    category_products = graphene.List(
        ProductType,
        category_id=graphene.ID(required=True),
        first=graphene.Int(default_value=50),
        description="Get products in a specific category"
    )

    def resolve_categories(self, info, **kwargs):
        """
        Resolve categories with workspace auto-scoping

        Performance: Uses select_related for featured_media (N+1 prevention)
        Security: Automatically scoped to authenticated workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'category:view'):
            raise GraphQLError("Insufficient permissions to view categories")

        return Category.objects.filter(
            workspace=workspace,
            is_visible=True
        ).select_related('featured_media').order_by('name')

    def resolve_category(self, info, id):
        """
        Resolve single category with workspace validation

        Security: Ensures category belongs to authenticated workspace
        Performance: Uses select_related for featured_media
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'category:view'):
            raise GraphQLError("Insufficient permissions to view category")

        try:
            return Category.objects.select_related('featured_media').get(
                id=id,
                workspace=workspace
            )
        except Category.DoesNotExist:
            raise GraphQLError("Category not found")


    def resolve_category_by_slug(self, info, slug):
        """
        Resolve category by slug

        Performance: Uses slug indexing with media optimization
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'category:view'):
            raise GraphQLError("Insufficient permissions to view category")

        try:
            return Category.objects.select_related('featured_media').get(
                workspace=workspace,
                slug=slug,
                is_visible=True
            )
        except Category.DoesNotExist:
            raise GraphQLError("Category not found")

    def resolve_featured_categories(self, info, limit):
        """
        Resolve featured categories

        Performance: Limited query with media optimization
        Security: Workspace auto-scoped
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'category:view'):
            raise GraphQLError("Insufficient permissions to view categories")

        return Category.objects.filter(
            workspace=workspace,
            is_visible=True
        ).select_related('featured_media').order_by('name')[:limit]

    def resolve_category_products(self, info, category_id, first):
        """
        Resolve products in a specific category

        Performance: Optimized query with media optimization
        Security: Validates category belongs to workspace
        """
        workspace = info.context.workspace
        user = info.context.user

        # CHECK PERMISSION
        if not PermissionService.has_permission(user, workspace, 'product:view'):
            raise GraphQLError("Insufficient permissions to view products")

        try:
            # Validate category belongs to workspace
            category = Category.objects.get(
                id=category_id,
                workspace=workspace
            )

            # Get products in this category with media optimization
            products = Product.objects.filter(
                workspace=workspace,
                category=category,
                is_active=True,
                status='published'
            ).select_related(
                'category',
                'featured_media'
            ).prefetch_related(
                'gallery_items__media'
            ).order_by('-created_at')[:first]

            return products

        except Category.DoesNotExist:
            raise GraphQLError("Category not found")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Category products query failed: {str(e)}", exc_info=True)
            raise GraphQLError(f"Failed to fetch category products: {str(e)}")