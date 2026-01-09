# Product Detail Service - Individual product pages with variants
# Optimized for Cameroon market with comprehensive product info

from typing import Dict, List, Optional, Any
from django.db import models
from django.core.cache import cache
from workspace.store.models import Product, ProductVariant, Category
from workspace.store.models.inventory_model import Inventory
from workspace.store.models.location_model import Location
import logging

logger = logging.getLogger('workspace.storefront.product_detail')


class ProductDetailService:
    """
    Product detail service for individual product pages

    Performance: Comprehensive product data with variants
    Scalability: Optimized queries with prefetch_related
    Reliability: Complete product information with fallbacks
    Security: Public product access with workspace scoping

    Cameroon Market Optimizations:
    - Local pricing and availability
    - Mobile Money compatibility
    - Regional delivery information
    - Phone-friendly product data
    """

    # Cache configuration
    CACHE_TIMEOUT = 600  # 10 minutes for product details
    VARIANT_CACHE_TIMEOUT = 300  # 5 minutes for variant data

    @staticmethod
    def get_product_detail(
        workspace_id: str,
        product_slug: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive product detail with variants

        Performance: Single optimized query with all related data
        Cameroon Market: Local availability and pricing info
        """
        try:
            # Generate cache key
            cache_key = f"product_detail_{workspace_id}_{product_slug}"

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for product detail: {cache_key}")
                return cached_result

            # Get product with all related data
            product = Product.objects.select_related(
                'category', 'sub_category'
            ).prefetch_related(
                models.Prefetch(
                    'variants',
                    queryset=ProductVariant.objects.filter(is_active=True).prefetch_related(
                        models.Prefetch(
                            'inventory',
                            queryset=Inventory.objects.select_related('location')
                        )
                    )
                )
            ).get(
                workspace_id=workspace_id,
                slug=product_slug,
                is_active=True,
                status='published'
            )

            # Increment view counter
            ProductDetailService._increment_product_views(product)

            # Format product data
            result = ProductDetailService._format_product_detail(product, customer_id)

            # Cache the result
            cache.set(cache_key, result, ProductDetailService.CACHE_TIMEOUT)

            logger.info(
                "Product detail fetched successfully",
                extra={
                    'workspace_id': workspace_id,
                    'product_slug': product_slug,
                    'product_id': product.id
                }
            )

            return result

        except Product.DoesNotExist:
            logger.warning(
                "Product not found",
                extra={'workspace_id': workspace_id, 'product_slug': product_slug}
            )
            return {
                'error': 'Product not found',
                'product': None
            }
        except Exception as e:
            logger.error(
                "Failed to fetch product detail",
                extra={
                    'workspace_id': workspace_id,
                    'product_slug': product_slug,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'error': 'Failed to load product',
                'product': None
            }

    @staticmethod
    def get_product_by_id(
        workspace_id: str,
        product_id: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get product detail by ID (for internal use)"""
        try:
            product = Product.objects.select_related(
                'category', 'sub_category'
            ).prefetch_related(
                models.Prefetch(
                    'variants',
                    queryset=ProductVariant.objects.filter(is_active=True).prefetch_related('inventory')
                )
            ).get(
                workspace_id=workspace_id,
                id=product_id,
                is_active=True
            )

            return ProductDetailService._format_product_detail(product, customer_id)

        except Product.DoesNotExist:
            logger.warning(
                "Product not found by ID",
                extra={'workspace_id': workspace_id, 'product_id': product_id}
            )
            return {'error': 'Product not found', 'product': None}
        except Exception as e:
            logger.error(
                "Failed to fetch product by ID",
                extra={'workspace_id': workspace_id, 'product_id': product_id, 'error': str(e)},
                exc_info=True
            )
            return {'error': 'Failed to load product', 'product': None}

    @staticmethod
    def _format_product_detail(product: Product, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Format comprehensive product detail for storefront"""
        # Basic product info
        product_data = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'description': product.description,
            'short_description': product.short_description,
            'price': float(product.price),
            'compare_at_price': float(product.compare_at_price) if product.compare_at_price else None,
            'is_on_sale': product.is_on_sale,
            'sale_percentage': product.sale_percentage,
            'cost_price': float(product.cost_price) if product.cost_price else None,
            'profit_margin': product.profit_margin,
            'profit_amount': float(product.profit_amount) if product.profit_amount else None,
            'featured_image': product.featured_image,
            'images': product.images,
            'sku': product.sku,
            'barcode': product.barcode,
            'brand': product.brand,
            'has_variants': product.has_variants,
            'stock_quantity': product.stock_quantity,
            'track_inventory': product.track_inventory,
            'allow_backorders': product.allow_backorders,
            'low_stock_threshold': product.low_stock_threshold,
            'is_in_stock': product.is_in_stock,
            'is_low_stock': product.is_low_stock,
            'stock_status': product.stock_status,
            'total_stock': product.get_total_stock(),
            'weight': float(product.weight) if product.weight else None,
            'length': float(product.length) if product.length else None,
            'width': float(product.width) if product.width else None,
            'height': float(product.height) if product.height else None,
            'has_dimensions': product.has_dimensions,
            'requires_shipping': product.requires_shipping,
            'is_digital': product.is_digital,
            'selling_type': product.selling_type,
            'condition': product.condition,
            'tags': product.tags,
            'views': product.views,
            'inquiries': product.inquiries,
            'orders': product.orders,
            'conversion_rate': product.conversion_rate,
            'category_attributes': product.category_attributes,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None,
            'meta_title': product.meta_title,
            'meta_description': product.meta_description
        }

        # Category information
        if product.category:
            product_data['category'] = {
                'id': product.category.id,
                'name': product.category.name,
                'slug': product.category.slug,
                'description': product.category.description,
                'image': product.category.image,
                'breadcrumb_path': product.category_path
            }

        # Sub-category information
        if product.sub_category:
            product_data['sub_category'] = {
                'id': product.sub_category.id,
                'name': product.sub_category.name,
                'slug': product.sub_category.slug,
                'description': product.sub_category.description
            }

        # Full category hierarchy
        product_data['category_hierarchy'] = product.full_category_hierarchy

        # Variants information
        if product.has_variants:
            product_data['variants'] = ProductDetailService._format_variants(product.variants.all())
            product_data['variant_options'] = ProductDetailService._get_variant_options(product.variants.all())
        else:
            product_data['variants'] = []
            product_data['variant_options'] = {}

        # Cameroon-specific optimizations
        product_data['local_info'] = ProductDetailService._get_local_product_info(product)
        product_data['mobile_money_compatible'] = product.price <= 500000  # 500k FCFA limit

        # Customer-specific data (if customer is provided)
        if customer_id:
            product_data['customer_data'] = ProductDetailService._get_customer_product_data(
                product.id, customer_id
            )

        return {
            'product': product_data,
            'related_products': ProductDetailService._get_related_products(product),
            'breadcrumbs': ProductDetailService._generate_breadcrumbs(product)
        }

    @staticmethod
    def _format_variants(variants) -> List[Dict]:
        """Format product variants with inventory information"""
        formatted_variants = []

        for variant in variants:
            variant_data = {
                'id': variant.id,
                'sku': variant.sku,
                'price': float(variant.price) if variant.price else None,
                'compare_at_price': float(variant.compare_at_price) if variant.compare_at_price else None,
                'cost_price': float(variant.cost_price) if variant.cost_price else None,
                'option1': variant.option1,
                'option2': variant.option2,
                'option3': variant.option3,
                'weight': float(variant.weight) if variant.weight else None,
                'requires_shipping': variant.requires_shipping,
                'taxable': variant.taxable,
                'barcode': variant.barcode,
                'image': variant.image,
                'inventory': []
            }

            # Inventory information
            for inventory in variant.inventory.all():
                variant_data['inventory'].append({
                    'location_id': inventory.location.id,
                    'location_name': inventory.location.name,
                    'quantity': inventory.quantity,
                    'reserved_quantity': inventory.reserved_quantity,
                    'available_quantity': inventory.available_quantity
                })

            # Calculate total available stock
            total_stock = sum(inv.available_quantity for inv in variant.inventory.all())
            variant_data['total_stock'] = total_stock
            variant_data['is_in_stock'] = total_stock > 0 or variant.track_inventory is False

            formatted_variants.append(variant_data)

        return formatted_variants

    @staticmethod
    def _get_variant_options(variants) -> Dict[str, List[str]]:
        """Extract unique variant options for product configuration"""
        options = {
            'option1': [],
            'option2': [],
            'option3': []
        }

        for variant in variants:
            if variant.option1 and variant.option1 not in options['option1']:
                options['option1'].append(variant.option1)
            if variant.option2 and variant.option2 not in options['option2']:
                options['option2'].append(variant.option2)
            if variant.option3 and variant.option3 not in options['option3']:
                options['option3'].append(variant.option3)

        return options

    @staticmethod
    def _get_local_product_info(product: Product) -> Dict[str, Any]:
        """Get Cameroon-specific product information"""
        return {
            'estimated_delivery': '2-5 business days',
            'delivery_regions': ['littoral', 'centre', 'ouest'],  # Major Cameroon regions
            'cash_on_delivery': product.price <= 100000,  # 100k FCFA limit for COD
            'mobile_money_max': 500000,  # 500k FCFA Mobile Money limit
            'local_warranty': product.condition == 'new',  # New products have warranty
            'return_policy': '7 days return policy',
            'customer_support': 'Available via WhatsApp and phone'
        }

    @staticmethod
    def _get_customer_product_data(product_id: str, customer_id: str) -> Dict[str, Any]:
        """Get customer-specific product data (wishlist, recently viewed, etc.)"""
        # This would integrate with customer-specific services
        # For now, return basic structure
        return {
            'in_wishlist': False,
            'recently_viewed': False,
            'purchase_history': False,
            'review_eligible': False
        }

    @staticmethod
    def _get_related_products(product: Product, limit: int = 8) -> List[Dict]:
        """Get related products for the detail page"""
        try:
            from workspace.storefront.services.product_catalog_service import product_catalog_service
            return product_catalog_service.get_related_products(product.id, limit)
        except Exception as e:
            logger.warning(f"Failed to get related products: {str(e)}")
            return []

    @staticmethod
    def _generate_breadcrumbs(product: Product) -> List[Dict]:
        """Generate breadcrumb navigation for the product"""
        breadcrumbs = [
            {'name': 'Home', 'url': '/'},
            {'name': 'Products', 'url': '/products'}
        ]

        # Add category breadcrumbs
        if product.category:
            for crumb in product.category.breadcrumb_path:
                breadcrumbs.append({
                    'name': crumb['name'],
                    'url': f"/categories/{crumb['slug']}"
                })

        # Add current product
        breadcrumbs.append({
            'name': product.name,
            'url': f"/products/{product.slug}",
            'current': True
        })

        return breadcrumbs

    @staticmethod
    def _increment_product_views(product: Product):
        """Increment product view counter"""
        try:
            from django.db.models import F
            Product.objects.filter(id=product.id).update(views=F('views') + 1)

            # Clear product detail cache
            cache_key = f"product_detail_{product.workspace_id}_{product.slug}"
            cache.delete(cache_key)

        except Exception as e:
            logger.warning(f"Failed to increment product views: {str(e)}")

    @staticmethod
    def get_variant_by_options(
        product_id: str,
        option1: str = '',
        option2: str = '',
        option3: str = ''
    ) -> Optional[Dict]:
        """Get specific variant by option combination"""
        try:
            product = Product.objects.get(id=product_id)
            variant = product.get_variant_by_options(option1, option2, option3)

            if variant:
                return {
                    'id': variant.id,
                    'price': float(variant.price) if variant.price else None,
                    'compare_at_price': float(variant.compare_at_price) if variant.compare_at_price else None,
                    'sku': variant.sku,
                    'option1': variant.option1,
                    'option2': variant.option2,
                    'option3': variant.option3,
                    'image': variant.image,
                    'inventory': [
                        {
                            'location_id': inv.location.id,
                            'location_name': inv.location.name,
                            'quantity': inv.quantity,
                            'available_quantity': inv.available_quantity
                        }
                        for inv in variant.inventory.all()
                    ],
                    'total_stock': sum(inv.available_quantity for inv in variant.inventory.all()),
                    'is_in_stock': any(inv.available_quantity > 0 for inv in variant.inventory.all())
                }

            return None

        except Exception as e:
            logger.error(
                "Failed to get variant by options",
                extra={'product_id': product_id, 'error': str(e)},
                exc_info=True
            )
            return None

    @staticmethod
    def clear_product_cache(workspace_id: str, product_slug: str):
        """Clear product detail cache"""
        try:
            cache_key = f"product_detail_{workspace_id}_{product_slug}"
            cache.delete(cache_key)
            logger.debug(f"Cleared product cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to clear product cache: {str(e)}")


# Global instance for easy access
product_detail_service = ProductDetailService()