# GraphQL queries for Category Operations
# Comprehensive category queries for flexible theme development

import graphene
import django_filters
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from ..types.category_types import CategoryType
from ..types.product_types import ProductType
from workspace.store.models import Category, Product


class CategoryFilterSet(django_filters.FilterSet):
    """
    FilterSet for Category with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    """
    class Meta:
        model = Category
        fields = {
            'name': ['exact', 'icontains'],
            'slug': ['exact'],
            'is_visible': ['exact'],
            'is_featured': ['exact'],
        }


class CategoryQueries(graphene.ObjectType):
    """
    Comprehensive Category Queries for Storefront

    All operations a typical e-commerce theme might need
    Themes can query only the fields they need
    Domain-based workspace identification
    """

    # Core Category Queries
    categories = DjangoFilterConnectionField(
        CategoryType,
        filterset_class=CategoryFilterSet,
        description="Browse categories with filtering and pagination"
    )

    category = graphene.Field(
        CategoryType,
        category_slug=graphene.String(required=True),
        description="Get single category details by slug"
    )

    category_by_id = graphene.Field(
        CategoryType,
        category_id=graphene.ID(required=True),
        description="Get single category details by ID"
    )

    categories_by_slugs = graphene.List(
        CategoryType,
        slugs=graphene.List(graphene.String, required=True),
        description="Get specific categories by their slugs"
    )

    # Category Products Queries
    category_products = graphene.List(
        ProductType,
        category_slug=graphene.String(required=True),
        search=graphene.String(),
        min_price=graphene.Float(),
        max_price=graphene.Float(),
        in_stock=graphene.Boolean(),
        sort_by=graphene.String(default_value='newest'),
        limit=graphene.Int(default_value=20),
        description="Get products from a specific category with filtering"
    )

    # Featured Categories
    featured_categories = graphene.List(
        CategoryType,
        limit=graphene.Int(default_value=6),
        description="Get featured categories for homepage"
    )

    # Category Analytics
    category_count = graphene.Int(
        is_visible=graphene.Boolean(default_value=True),
        description="Get count of categories matching criteria"
    )

    def resolve_categories(self, info, **kwargs):
        """
        Resolve categories query with domain-based workspace identification

        Performance: Uses proper indexing
        Security: Workspace identified by middleware from domain
        """
        workspace = info.context.workspace

        # Scope to validated workspace and filter visible categories
        return Category.objects.filter(
            workspace=workspace,
            is_visible=True
        ).order_by('sort_order', 'name')

    def resolve_category(self, info, category_slug):
        """Get single category by slug"""
        workspace = info.context.workspace

        try:
            return Category.objects.get(
                workspace=workspace,
                slug=category_slug,
                is_visible=True
            )
        except Category.DoesNotExist:
            return None

    def resolve_category_by_id(self, info, category_id):
        """Get single category by ID"""
        workspace = info.context.workspace

        try:
            return Category.objects.get(
                workspace=workspace,
                id=category_id,
                is_visible=True
            )
        except Category.DoesNotExist:
            return None

    def resolve_categories_by_slugs(self, info, slugs):
        """Get specific categories by their slugs"""
        workspace = info.context.workspace

        queryset = Category.objects.filter(
            workspace=workspace,
            slug__in=slugs,
            is_visible=True
        ).order_by('sort_order', 'name')

        return list(queryset)

    def resolve_category_products(self, info, category_slug,
                                  search=None, min_price=None, max_price=None,
                                  in_stock=None, sort_by='newest', limit=20):
        """
        Get products from a specific category with filtering

        Themes can filter products within a category
        """
        workspace = info.context.workspace

        try:
            category = Category.objects.get(
                workspace=workspace,
                slug=category_slug,
                is_visible=True
            )
        except Category.DoesNotExist:
            return []

        # Base query - published products in this category
        queryset = Product.objects.filter(
            workspace=workspace,
            category=category,
            status='published',
            is_active=True
        ).select_related('category', 'featured_media').prefetch_related('gallery_items__media')

        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(brand__icontains=search) |
                Q(tags__contains=[search])
            )

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if in_stock:
            queryset = queryset.filter(
                Q(track_inventory=False) |
                Q(inventory_quantity__gt=0) |
                Q(allow_backorders=True)
            )

        # Apply sorting
        sort_mapping = {
            'price_asc': 'price',
            'price_desc': '-price',
            'newest': '-created_at',
            'oldest': 'created_at',
            'name_asc': 'name',
            'name_desc': '-name',
            'best_selling': '-orders',
            'most_viewed': '-views',
        }
        order_by = sort_mapping.get(sort_by, '-created_at')
        queryset = queryset.order_by(order_by)

        # Limit results
        limit = min(limit or 20, 50)

        return list(queryset[:limit])

    def resolve_featured_categories(self, info, limit=6):
        """Get featured categories for homepage"""
        workspace = info.context.workspace

        queryset = Category.objects.filter(
            workspace=workspace,
            is_featured=True,
            is_visible=True
        ).order_by('sort_order', 'name')

        limit = min(limit or 6, 20)
        return list(queryset[:limit])

    def resolve_category_count(self, info, is_visible=True):
        """Get count of categories matching criteria"""
        workspace = info.context.workspace

        queryset = Category.objects.filter(
            workspace=workspace,
            is_visible=is_visible
        )

        return queryset.count()