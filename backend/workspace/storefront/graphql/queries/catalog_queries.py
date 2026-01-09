# GraphQL queries for Product Catalog Operations
# Comprehensive product queries for flexible theme development

import graphene
import django_filters
from django.db import models
from django.db.models import Q, Prefetch, F
from graphene_django.filter import DjangoFilterConnectionField
from ..types.product_types import ProductType, ProductConnection
from workspace.store.models import Product


class ProductFilterSet(django_filters.FilterSet):
    """
    FilterSet for Product with explicit field definitions

    Security: Explicitly defines filterable fields to prevent data exposure
    Best Practice: Required by django-filter 2.0+ for security
    """
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'sku': ['exact', 'icontains'],
            'status': ['exact'],
            'category': ['exact'],
            'brand': ['icontains'],
            'vendor': ['icontains'],
            'product_type': ['exact'],
            'price': ['exact', 'gte', 'lte'],
            'inventory_quantity': ['exact', 'gte', 'lte'],
            'inventory_health': ['exact'],
            'requires_shipping': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
        }


class ProductQueries(graphene.ObjectType):
    """
    Comprehensive Product Queries for Storefront

    All operations a typical e-commerce theme might need
    Themes can query only the fields they need
    Domain-based workspace identification
    """

    # Core Product Queries
    products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilterSet,
        # Frontend-friendly filtering arguments
        search=graphene.String(description="Search products by name, description, or brand"),
        category_slug=graphene.String(description="Filter by category slug"),
        min_price=graphene.Float(description="Minimum price filter"),
        max_price=graphene.Float(description="Maximum price filter"),
        in_stock=graphene.Boolean(description="Filter by stock availability"),
        brand=graphene.String(description="Filter by brand name"),
        sort_by=graphene.String(description="Sort order: 'price_asc', 'price_desc', 'name_asc', 'name_desc', 'newest', 'oldest'"),
        description="Browse published products with filtering and pagination"
    )

    product = graphene.Field(
        ProductType,
        product_slug=graphene.String(required=True),
        description="Get single product details by slug with variants"
    )

    product_by_id = graphene.Field(
        ProductType,
        product_id=graphene.ID(required=True),
        description="Get single product details by ID"
    )

    # Specialized Product Queries
    products_on_sale = graphene.List(
        ProductType,
        limit=graphene.Int(default_value=12),
        description="Get products currently on sale"
    )

    new_products = graphene.List(
        ProductType,
        limit=graphene.Int(default_value=12),
        description="Get newest products"
    )

    related_products = graphene.List(
        ProductType,
        product_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=8),
        description="Get products related to a specific product"
    )

    # Search & Discovery
    search_products = graphene.List(
        ProductType,
        query=graphene.String(required=True),
        category_slug=graphene.String(),
        limit=graphene.Int(default_value=20),
        description="Search products by query string"
    )

    # Product Counts & Analytics
    product_count = graphene.Int(
        category_slug=graphene.String(),
        in_stock=graphene.Boolean(),
        description="Get count of products matching criteria"
    )

    def resolve_products(self, info, **kwargs):
        """
        Resolve products query with domain-based workspace identification

        Performance: Uses select_related and proper indexing
        Security: Workspace identified by middleware from domain

        Supports frontend-friendly filtering:
        - search: Full-text search across name, description, brand
        - category_slug: Filter by category slug
        - min_price/max_price: Price range filtering
        - in_stock: Stock availability
        - brand: Brand name filtering
        - sort_by: Flexible sorting options
        """
        workspace = info.context.workspace

        # Base queryset: validated workspace and published products
        queryset = Product.objects.filter(
            workspace=workspace,
            status='published',
            is_active=True
        ).select_related('category', 'featured_media').prefetch_related('gallery_items__media')

        # Apply search filter (maps to name, description, brand)
        search = kwargs.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(brand__icontains=search) |
                Q(tags__contains=[search])
            )

        # Apply category filter (maps to category__slug)
        category_slug = kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Apply price range filters (maps to price__gte, price__lte)
        min_price = kwargs.get('min_price')
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        max_price = kwargs.get('max_price')
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        # Apply stock filter (maps to inventory_quantity__gt or track_inventory)
        in_stock = kwargs.get('in_stock')
        if in_stock:
            queryset = queryset.filter(
                Q(track_inventory=False) |
                Q(inventory_quantity__gt=0) |
                Q(allow_backorders=True)
            )

        # Apply brand filter (maps to brand__icontains)
        brand = kwargs.get('brand')
        if brand:
            queryset = queryset.filter(brand__icontains=brand)

        # Apply sorting (maps to order_by)
        sort_by = kwargs.get('sort_by', 'newest')
        sort_mapping = {
            'price_asc': 'price',
            'price_desc': '-price',
            'name_asc': 'name',
            'name_desc': '-name',
            'newest': '-created_at',
            'oldest': 'created_at',
        }
        order_by = sort_mapping.get(sort_by, '-created_at')
        queryset = queryset.order_by(order_by)

        return queryset

    def resolve_product(self, info, product_slug):
        """Get single product by slug with variants"""
        workspace = info.context.workspace

        try:
            return Product.objects.select_related('category').prefetch_related(
                'variants'
            ).get(
                workspace=workspace,
                slug=product_slug,
                status='published',
                is_active=True
            )
        except Product.DoesNotExist:
            return None

    def resolve_product_by_id(self, info, product_id):
        """Get single product by ID"""
        workspace = info.context.workspace

        try:
            return Product.objects.select_related('category').prefetch_related(
                'variants'
            ).get(
                workspace=workspace,
                id=product_id,
                status='published',
                is_active=True
            )
        except Product.DoesNotExist:
            return None

    def resolve_products_on_sale(self, info, limit=12):
        """Get products currently on sale"""
        workspace = info.context.workspace

        queryset = Product.objects.filter(
            workspace=workspace,
            status='published',
            is_active=True,
            compare_at_price__gt=models.F('price')  # Products with compare_at_price > price
        ).select_related('category').order_by('-created_at')

        limit = min(limit or 12, 50)
        return queryset[:limit]

    def resolve_new_products(self, info, limit=12):
        """Get newest products"""
        workspace = info.context.workspace

        queryset = Product.objects.filter(
            workspace=workspace,
            status='published',
            is_active=True
        ).select_related('category').order_by('-created_at')

        limit = min(limit or 12, 50)
        return queryset[:limit]

    def resolve_related_products(self, info, product_id, limit=8):
        """Get products related to a specific product"""
        workspace = info.context.workspace

        try:
            source_product = Product.objects.get(
                id=product_id,
                workspace=workspace
            )

            # Find related products by category and tags
            related_products = Product.objects.filter(
                workspace=workspace,
                status='published',
                is_active=True
            ).exclude(
                id=product_id
            ).filter(
                Q(category=source_product.category) |
                Q(tags__overlap=source_product.tags)
            ).select_related('category').order_by('-created_at')

            limit = min(limit or 8, 20)
            return related_products[:limit]

        except Product.DoesNotExist:
            return []

    def resolve_search_products(self, info, query, category_slug=None, limit=20):
        """Search products by query string"""
        workspace = info.context.workspace

        queryset = Product.objects.filter(
            workspace=workspace,
            status='published',
            is_active=True
        ).filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(tags__contains=[query])
        ).select_related('category')

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        limit = min(limit or 20, 50)
        return queryset[:limit]

    def resolve_product_count(self, info, category_slug=None, in_stock=None):
        """Get count of products matching criteria"""
        workspace = info.context.workspace

        queryset = Product.objects.filter(
            workspace=workspace,
            status='published',
            is_active=True
        )

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if in_stock:
            queryset = queryset.filter(
                Q(track_inventory=False) |
                Q(inventory_quantity__gt=0) |
                Q(allow_backorders=True)
            )

        return queryset.count()