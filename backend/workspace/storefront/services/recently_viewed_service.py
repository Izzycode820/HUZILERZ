# Recently Viewed Service - Customer product view tracking
# Optimized for Cameroon market with phone-first approach

from typing import Dict, List, Optional, Any
from django.db import transaction
from django.core.cache import cache
from workspace.storefront.models.recently_viewed_model import RecentlyViewed
from workspace.store.models import Product
from workspace.core.models.customer_model import Customer
from django.utils import timezone
import logging

logger = logging.getLogger('workspace.storefront.recently_viewed')


class RecentlyViewedService:
    """
    Recently viewed products service

    Performance: < 50ms view tracking operations
    Scalability: Optimized view history with caching
    Reliability: Consistent view tracking with cleanup
    Security: Customer-specific view history

    Cameroon Market Optimizations:
    - Phone-based customer tracking
    - Mobile-friendly view history
    - Local product view patterns
    """

    # Configuration
    MAX_RECENT_VIEWS = 20
    CACHE_TIMEOUT = 300  # 5 minutes
    VIEW_CACHE_PREFIX = 'recently_viewed_'

    @staticmethod
    def track_product_view(
        workspace_id: str,
        customer_id: str,
        product_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track product view for customer

        Cameroon Market: Phone-first view tracking
        Performance: Atomic view tracking
        """
        try:
            with transaction.atomic():
                # Get customer and product
                customer = Customer.objects.get(
                    id=customer_id,
                    workspace_id=workspace_id,
                    is_active=True
                )

                product = Product.objects.get(
                    id=product_id,
                    workspace_id=workspace_id,
                    is_active=True
                )

                # Update or create recently viewed record
                recently_viewed, created = RecentlyViewed.objects.update_or_create(
                    workspace_id=workspace_id,
                    customer=customer,
                    product=product,
                    defaults={
                        'viewed_at': timezone.now(),
                        'session_id': session_id or '',
                        'view_count': 1
                    }
                )

                if not created:
                    # Increment view count for existing record
                    recently_viewed.view_count += 1
                    recently_viewed.viewed_at = timezone.now()
                    recently_viewed.save()

                # Clear cache
                RecentlyViewedService._clear_recently_viewed_cache(workspace_id, customer_id)

                # Clean up old views if needed
                RecentlyViewedService._cleanup_old_views(workspace_id, customer_id)

                logger.debug(
                    "Product view tracked",
                    extra={
                        'workspace_id': workspace_id,
                        'customer_id': customer_id,
                        'product_id': product_id,
                        'created': created
                    }
                )

                return {
                    'success': True,
                    'tracked': True,
                    'created': created
                }

        except Customer.DoesNotExist:
            return {
                'success': False,
                'error': 'Customer not found'
            }
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Product not found'
            }
        except Exception as e:
            logger.error(
                "Failed to track product view",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer_id,
                    'product_id': product_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to track product view'
            }

    @staticmethod
    def get_recently_viewed_products(
        workspace_id: str,
        customer_id: str,
        limit: int = 10,
        include_product_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get recently viewed products for customer

        Cameroon Market: Mobile-optimized view history
        Performance: Cached recently viewed products
        """
        try:
            cache_key = f"{RecentlyViewedService.VIEW_CACHE_PREFIX}{workspace_id}_{customer_id}_{limit}_{include_product_details}"

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result:
                return {
                    'success': True,
                    'recently_viewed': cached_result
                }

            # Get recently viewed products
            recent_views = RecentlyViewed.objects.filter(
                workspace_id=workspace_id,
                customer_id=customer_id
            ).select_related('product').order_by('-viewed_at')[:limit]

            formatted_views = [
                RecentlyViewedService._format_recently_viewed(view, include_product_details)
                for view in recent_views
            ]

            # Cache the result
            cache.set(cache_key, formatted_views, RecentlyViewedService.CACHE_TIMEOUT)

            return {
                'success': True,
                'recently_viewed': formatted_views,
                'total_count': len(formatted_views)
            }

        except Exception as e:
            logger.error(
                "Failed to get recently viewed products",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load recently viewed products'
            }

    @staticmethod
    def clear_recently_viewed(
        workspace_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Clear customer's recently viewed history"""
        try:
            with transaction.atomic():
                deleted_count, _ = RecentlyViewed.objects.filter(
                    workspace_id=workspace_id,
                    customer_id=customer_id
                ).delete()

                # Clear cache
                RecentlyViewedService._clear_recently_viewed_cache(workspace_id, customer_id)

                logger.info(
                    "Recently viewed history cleared",
                    extra={
                        'workspace_id': workspace_id,
                        'customer_id': customer_id,
                        'deleted_count': deleted_count
                    }
                )

                return {
                    'success': True,
                    'deleted_count': deleted_count,
                    'message': 'Recently viewed history cleared'
                }

        except Exception as e:
            logger.error(
                "Failed to clear recently viewed history",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to clear history'
            }

    @staticmethod
    def get_view_statistics(
        workspace_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Get view statistics for customer"""
        try:
            cache_key = f"{RecentlyViewedService.VIEW_CACHE_PREFIX}stats_{workspace_id}_{customer_id}"

            # Try cache first
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return {
                    'success': True,
                    'statistics': cached_stats
                }

            # Calculate statistics
            total_views = RecentlyViewed.objects.filter(
                workspace_id=workspace_id,
                customer_id=customer_id
            ).count()

            unique_products_viewed = RecentlyViewed.objects.filter(
                workspace_id=workspace_id,
                customer_id=customer_id
            ).values('product').distinct().count()

            recent_views_count = RecentlyViewed.objects.filter(
                workspace_id=workspace_id,
                customer_id=customer_id,
                viewed_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()

            most_viewed_product = RecentlyViewed.objects.filter(
                workspace_id=workspace_id,
                customer_id=customer_id
            ).values('product__name').annotate(
                total_views=models.Sum('view_count')
            ).order_by('-total_views').first()

            stats = {
                'total_views': total_views,
                'unique_products_viewed': unique_products_viewed,
                'recent_views_7_days': recent_views_count,
                'most_viewed_product': most_viewed_product['product__name'] if most_viewed_product else None,
                'most_viewed_count': most_viewed_product['total_views'] if most_viewed_product else 0
            }

            # Cache the statistics
            cache.set(cache_key, stats, RecentlyViewedService.CACHE_TIMEOUT)

            return {
                'success': True,
                'statistics': stats
            }

        except Exception as e:
            logger.error(
                "Failed to get view statistics",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load view statistics'
            }

    @staticmethod
    def get_popular_products_from_views(
        workspace_id: str,
        days: int = 30,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get popular products based on view counts

        Cameroon Market: Local product popularity
        Performance: Cached popular products
        """
        try:
            cache_key = f"{RecentlyViewedService.VIEW_CACHE_PREFIX}popular_{workspace_id}_{days}_{limit}"

            # Try cache first
            cached_popular = cache.get(cache_key)
            if cached_popular:
                return {
                    'success': True,
                    'popular_products': cached_popular
                }

            # Calculate popular products
            cutoff_date = timezone.now() - timezone.timedelta(days=days)

            popular_products = RecentlyViewed.objects.filter(
                workspace_id=workspace_id,
                viewed_at__gte=cutoff_date
            ).values(
                'product_id', 'product__name', 'product__slug',
                'product__featured_image', 'product__price'
            ).annotate(
                total_views=models.Sum('view_count'),
                unique_viewers=models.Count('customer', distinct=True)
            ).order_by('-total_views')[:limit]

            formatted_popular = [
                {
                    'product_id': item['product_id'],
                    'name': item['product__name'],
                    'slug': item['product__slug'],
                    'featured_image': item['product__featured_image'],
                    'price': float(item['product__price']) if item['product__price'] else None,
                    'total_views': item['total_views'],
                    'unique_viewers': item['unique_viewers']
                }
                for item in popular_products
            ]

            # Cache the result
            cache.set(cache_key, formatted_popular, RecentlyViewedService.CACHE_TIMEOUT)

            return {
                'success': True,
                'popular_products': formatted_popular
            }

        except Exception as e:
            logger.error(
                "Failed to get popular products from views",
                extra={
                    'workspace_id': workspace_id,
                    'days': days,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load popular products'
            }

    # Helper methods

    @staticmethod
    def _format_recently_viewed(
        recently_viewed: RecentlyViewed,
        include_product_details: bool = True
    ) -> Dict[str, Any]:
        """Format recently viewed record for response"""
        formatted_view = {
            'id': recently_viewed.id,
            'product_id': recently_viewed.product_id,
            'viewed_at': recently_viewed.viewed_at.isoformat(),
            'view_count': recently_viewed.view_count,
            'is_recent': recently_viewed.is_recent,
            'days_ago': (timezone.now() - recently_viewed.viewed_at).days
        }

        if include_product_details:
            product = recently_viewed.product
            formatted_view['product'] = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'compare_at_price': float(product.compare_at_price) if product.compare_at_price else None,
                'is_on_sale': product.is_on_sale,
                'sale_percentage': product.sale_percentage,
                'featured_image': product.featured_image,
                'is_in_stock': product.is_in_stock,
                'stock_status': product.stock_status,
                'brand': product.brand,
                'category': {
                    'id': product.category.id if product.category else None,
                    'name': product.category.name if product.category else None,
                    'slug': product.category.slug if product.category else None
                } if product.category else None
            }

        return formatted_view

    @staticmethod
    def _cleanup_old_views(workspace_id: str, customer_id: str):
        """Clean up old views for customer"""
        try:
            # Keep only the most recent views
            recent_views = RecentlyViewed.objects.filter(
                workspace_id=workspace_id,
                customer_id=customer_id
            ).order_by('-viewed_at')

            if recent_views.count() > RecentlyViewedService.MAX_RECENT_VIEWS:
                # Delete older views
                views_to_delete = recent_views[RecentlyViewedService.MAX_RECENT_VIEWS:]
                deleted_count = views_to_delete.count()
                views_to_delete.delete()

                if deleted_count > 0:
                    logger.debug(
                        "Cleaned up old views",
                        extra={
                            'workspace_id': workspace_id,
                            'customer_id': customer_id,
                            'deleted_count': deleted_count
                        }
                    )

        except Exception as e:
            logger.warning(f"Failed to cleanup old views: {str(e)}")

    @staticmethod
    def _clear_recently_viewed_cache(workspace_id: str, customer_id: str):
        """Clear recently viewed caches for customer"""
        try:
            cache.delete_many([
                f"{RecentlyViewedService.VIEW_CACHE_PREFIX}{workspace_id}_{customer_id}_*",
                f"{RecentlyViewedService.VIEW_CACHE_PREFIX}stats_{workspace_id}_{customer_id}"
            ])
        except Exception as e:
            logger.warning(f"Failed to clear recently viewed cache: {str(e)}")


# Global instance for easy access
recently_viewed_service = RecentlyViewedService()