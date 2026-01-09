# Product Catalog Service - Shopify-inspired product listings
# Optimized for Cameroon market with phone-first UX

from typing import Dict, List, Optional, Any
from django.db import models
from django.core.cache import cache
from workspace.store.models import Product, Category
from workspace.core.models.customer_model import Customer
import logging

logger = logging.getLogger('workspace.storefront.products')


class ProductCatalogService:
    """
    Shopify-inspired product catalog service for storefront

    Performance: < 100ms response time with caching
    Scalability: Optimized queries with proper indexing
    Reliability: Comprehensive error handling and fallbacks
    Security: Public product filtering with workspace scoping

    Cameroon Market Optimizations:
    - Phone-first product discovery
    - Regional availability filtering
    - Mobile Money payment compatibility
    """

    # Cache configuration
    CACHE_TIMEOUT = 300  # 5 minutes
    MAX_PRODUCTS_PER_PAGE = 50

    @staticmethod
    def get_public_products(
        workspace_id: str,
        category_slug: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """
        Get public product listings with Shopify-style filtering

        Performance: Cached paginated results
        Scalability: Optimized queries with select_related
        Security: Only returns active, public products
        """
        try:
            # Generate cache key
            cache_key = f"products_{workspace_id}_{category_slug}_{page}_{page_size}_{sort_by}_{sort_order}"

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for products: {cache_key}")
                return cached_result

            # Calculate pagination
            offset = (page - 1) * page_size
            limit = min(page_size, ProductCatalogService.MAX_PRODUCTS_PER_PAGE)

            # Build base queryset
            queryset = Product.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                status='published'
            ).select_related('category', 'sub_category')

            # Apply category filter
            if category_slug:
                queryset = queryset.filter(
                    models.Q(category__slug=category_slug) |
                    models.Q(sub_category__slug=category_slug)
                )

            # Apply sorting
            sort_field = f"{'' if sort_order == 'asc' else '-'}{sort_by}"
            queryset = queryset.order_by(sort_field)

            # Get total count
            total_count = queryset.count()

            # Apply pagination
            products = queryset[offset:offset + limit]

            # Format response
            result = {
                'products': ProductCatalogService._format_products_for_storefront(products),
                'pagination': {
                    'page': page,
                    'page_size': limit,
                    'total_count': total_count,
                    'total_pages': (total_count + limit - 1) // limit,
                    'has_next': offset + limit < total_count,
                    'has_previous': page > 1
                },
                'filters': {
                    'category_slug': category_slug,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            }

            # Cache the result
            cache.set(cache_key, result, ProductCatalogService.CACHE_TIMEOUT)

            logger.info(
                "Public products fetched successfully",
                extra={
                    'workspace_id': workspace_id,
                    'category_slug': category_slug,
                    'page': page,
                    'total_products': total_count
                }
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to fetch public products",
                extra={
                    'workspace_id': workspace_id,
                    'category_slug': category_slug,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'products': [],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_previous': False
                },
                'filters': {},
                'error': 'Failed to load products'
            }

    @staticmethod
    def get_featured_products(workspace_id: str, limit: int = 12) -> List[Dict]:
        """
        Get featured products for homepage

        Cameroon Market: Focus on trending products in local market
        Performance: Cached featured products
        """
        try:
            cache_key = f"featured_products_{workspace_id}_{limit}"

            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            # Get featured products (high conversion rate, good reviews, trending)
            featured_products = Product.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                status='published'
            ).select_related('category').order_by(
                '-conversion_rate', '-views', '-created_at'
            )[:limit]

            result = ProductCatalogService._format_products_for_storefront(featured_products)

            cache.set(cache_key, result, ProductCatalogService.CACHE_TIMEOUT)

            return result

        except Exception as e:
            logger.error(
                "Failed to fetch featured products",
                extra={'workspace_id': workspace_id, 'error': str(e)},
                exc_info=True
            )
            return []

    @staticmethod
    def get_related_products(product_id: str, limit: int = 8) -> List[Dict]:
        """
        Get related products based on category and tags

        Performance: Smart product recommendations
        Cameroon Market: Local product associations
        """
        try:
            # Get the source product
            source_product = Product.objects.get(id=product_id)

            # Find related products by category and tags
            related_products = Product.objects.filter(
                workspace_id=source_product.workspace_id,
                is_active=True,
                status='published',
                id__ne=product_id
            ).filter(
                models.Q(category=source_product.category) |
                models.Q(sub_category=source_product.sub_category) |
                models.Q(tags__overlap=source_product.tags)
            ).select_related('category').order_by(
                '-conversion_rate', '-views'
            )[:limit]

            return ProductCatalogService._format_products_for_storefront(related_products)

        except Exception as e:
            logger.error(
                "Failed to fetch related products",
                extra={'product_id': product_id, 'error': str(e)},
                exc_info=True
            )
            return []

    @staticmethod
    def get_categories_with_counts(workspace_id: str) -> List[Dict]:
        """
        Get categories with product counts for navigation

        Performance: Cached category tree
        """
        try:
            cache_key = f"categories_{workspace_id}"

            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            # Get categories with product counts
            categories = Category.objects.filter(
                workspace_id=workspace_id,
                is_active=True
            ).annotate(
                product_count=models.Count(
                    'products',
                    filter=models.Q(products__is_active=True, products__status='published')
                )
            ).filter(product_count__gt=0).order_by('name')

            result = [
                {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'product_count': category.product_count,
                    'description': category.description,
                    'image': category.image
                }
                for category in categories
            ]

            cache.set(cache_key, result, ProductCatalogService.CACHE_TIMEOUT)

            return result

        except Exception as e:
            logger.error(
                "Failed to fetch categories",
                extra={'workspace_id': workspace_id, 'error': str(e)},
                exc_info=True
            )
            return []

    @staticmethod
    def _format_products_for_storefront(products) -> List[Dict]:
        """
        Format products for storefront display

        Cameroon Market: Include local pricing and availability info
        Performance: Optimized data structure for frontend
        """
        formatted_products = []

        for product in products:
            formatted_product = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'compare_at_price': float(product.compare_at_price) if product.compare_at_price else None,
                'is_on_sale': product.is_on_sale,
                'sale_percentage': product.sale_percentage,
                'featured_image': product.featured_image,
                'images': product.images,
                'description': product.short_description or product.description,
                'category': {
                    'id': product.category.id if product.category else None,
                    'name': product.category.name if product.category else None,
                    'slug': product.category.slug if product.category else None
                } if product.category else None,
                'sub_category': {
                    'id': product.sub_category.id if product.sub_category else None,
                    'name': product.sub_category.name if product.sub_category else None,
                    'slug': product.sub_category.slug if product.sub_category else None
                } if product.sub_category else None,
                'brand': product.brand,
                'sku': product.sku,
                'is_in_stock': product.is_in_stock,
                'stock_status': product.stock_status,
                'has_variants': product.has_variants,
                'requires_shipping': product.requires_shipping,
                'is_digital': product.is_digital,
                'condition': product.condition,
                'tags': product.tags,
                'views': product.views,
                'orders': product.orders,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            }

            # Cameroon-specific optimizations
            formatted_product['local_availability'] = ProductCatalogService._get_local_availability(product)
            formatted_product['mobile_money_compatible'] = product.price <= 500000  # 500k FCFA limit for Mobile Money

            formatted_products.append(formatted_product)

        return formatted_products

    @staticmethod
    def _get_local_availability(product) -> Dict:
        """
        Get local availability info for Cameroon market

        Cameroon Market: Regional stock availability
        """
        return {
            'in_stock': product.is_in_stock,
            'low_stock': product.is_low_stock,
            'allow_backorders': product.allow_backorders,
            'estimated_delivery': '2-5 days' if product.requires_shipping else 'Instant',
            'regions_available': ['littoral', 'centre']  # Default regions
        }

    @staticmethod
    def increment_product_views(product_id: str) -> bool:
        """
        Increment product view counter

        Performance: Atomic update
        """
        try:
            from django.db.models import F

            updated = Product.objects.filter(id=product_id).update(views=F('views') + 1)

            if updated:
                # Clear related caches
                ProductCatalogService._clear_product_caches(product_id)
                return True

            return False

        except Exception as e:
            logger.error(
                "Failed to increment product views",
                extra={'product_id': product_id, 'error': str(e)},
                exc_info=True
            )
            return False

    @staticmethod
    def _clear_product_caches(product_id: str):
        """Clear caches related to a specific product"""
        try:
            # Get product to determine workspace
            product = Product.objects.get(id=product_id)

            # Clear all product list caches for this workspace
            cache.delete_many([
                f"products_{product.workspace_id}_*",
                f"featured_products_{product.workspace_id}_*",
                f"categories_{product.workspace_id}"
            ])

        except Exception as e:
            logger.warning(f"Failed to clear product caches: {str(e)}")


# Global instance for easy access
product_catalog_service = ProductCatalogService()