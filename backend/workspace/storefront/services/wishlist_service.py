# Wishlist Service - Customer favorites management
# Optimized for Cameroon market with phone-first approach

from typing import Dict, List, Optional, Any
from django.db import transaction
from django.core.cache import cache
from workspace.storefront.models.wishlist_model import Wishlist, WishlistItem
from workspace.store.models import Product
from workspace.core.models.customer_model import Customer
import logging

logger = logging.getLogger('workspace.storefront.wishlist')


class WishlistService:
    """
    Wishlist service for customer favorites management

    Performance: < 100ms wishlist operations
    Scalability: Optimized wishlist queries with caching
    Reliability: Comprehensive wishlist management
    Security: Customer-specific wishlist access

    Cameroon Market Optimizations:
    - Phone-based customer identification
    - Mobile-friendly wishlist operations
    - Local product favorites tracking
    """

    # Cache configuration
    CACHE_TIMEOUT = 300  # 5 minutes
    WISHLIST_CACHE_PREFIX = 'wishlist_'

    @staticmethod
    def get_or_create_default_wishlist(
        workspace_id: str,
        customer_id: str
    ) -> Wishlist:
        """
        Get or create default wishlist for customer

        Cameroon Market: Phone-first customer wishlist
        Performance: Cached default wishlist
        """
        try:
            cache_key = f"{WishlistService.WISHLIST_CACHE_PREFIX}default_{workspace_id}_{customer_id}"

            # Try cache first
            cached_wishlist = cache.get(cache_key)
            if cached_wishlist:
                return cached_wishlist

            # Get or create default wishlist
            wishlist, created = Wishlist.objects.get_or_create(
                workspace_id=workspace_id,
                customer_id=customer_id,
                is_default=True,
                defaults={
                    'name': 'My Wishlist',
                    'is_public': False
                }
            )

            # Cache the wishlist
            cache.set(cache_key, wishlist, WishlistService.CACHE_TIMEOUT)

            if created:
                logger.info(
                    "Default wishlist created",
                    extra={
                        'workspace_id': workspace_id,
                        'customer_id': customer_id,
                        'wishlist_id': wishlist.id
                    }
                )

            return wishlist

        except Exception as e:
            logger.error(
                "Failed to get/create default wishlist",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer_id,
                    'error': str(e)
                },
                exc_info=True
            )
            raise

    @staticmethod
    def add_to_wishlist(
        workspace_id: str,
        customer_id: str,
        product_id: str,
        wishlist_id: Optional[str] = None,
        notes: str = '',
        priority: int = 1
    ) -> Dict[str, Any]:
        """
        Add product to customer wishlist

        Cameroon Market: Mobile-friendly wishlist addition
        Performance: Atomic wishlist item creation
        """
        try:
            with transaction.atomic():
                # Get or create default wishlist
                if wishlist_id:
                    wishlist = Wishlist.objects.get(
                        id=wishlist_id,
                        workspace_id=workspace_id,
                        customer_id=customer_id
                    )
                else:
                    wishlist = WishlistService.get_or_create_default_wishlist(
                        workspace_id, customer_id
                    )

                # Get product
                product = Product.objects.get(
                    id=product_id,
                    workspace_id=workspace_id,
                    is_active=True
                )

                # Create wishlist item
                wishlist_item, created = WishlistItem.objects.get_or_create(
                    wishlist=wishlist,
                    product=product,
                    defaults={
                        'notes': notes,
                        'priority': priority,
                        'added_at_price': product.price
                    }
                )

                if not created:
                    # Update existing item
                    wishlist_item.notes = notes
                    wishlist_item.priority = priority
                    wishlist_item.save()

                # Clear wishlist cache
                WishlistService._clear_wishlist_cache(workspace_id, customer_id, wishlist.id)

                logger.info(
                    "Product added to wishlist",
                    extra={
                        'workspace_id': workspace_id,
                        'customer_id': customer_id,
                        'product_id': product_id,
                        'wishlist_id': wishlist.id,
                        'created': created
                    }
                )

                return {
                    'success': True,
                    'wishlist_item': WishlistService._format_wishlist_item(wishlist_item),
                    'message': 'Product added to wishlist' if created else 'Wishlist item updated'
                }

        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Product not found'
            }
        except Wishlist.DoesNotExist:
            return {
                'success': False,
                'error': 'Wishlist not found'
            }
        except Exception as e:
            logger.error(
                "Failed to add product to wishlist",
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
                'error': 'Failed to add product to wishlist'
            }

    @staticmethod
    def remove_from_wishlist(
        workspace_id: str,
        customer_id: str,
        product_id: str,
        wishlist_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove product from customer wishlist

        Cameroon Market: Simple wishlist removal
        Performance: Atomic wishlist item deletion
        """
        try:
            with transaction.atomic():
                # Get wishlist
                if wishlist_id:
                    wishlist = Wishlist.objects.get(
                        id=wishlist_id,
                        workspace_id=workspace_id,
                        customer_id=customer_id
                    )
                else:
                    wishlist = WishlistService.get_or_create_default_wishlist(
                        workspace_id, customer_id
                    )

                # Remove wishlist item
                deleted_count, _ = WishlistItem.objects.filter(
                    wishlist=wishlist,
                    product_id=product_id
                ).delete()

                if deleted_count > 0:
                    # Clear wishlist cache
                    WishlistService._clear_wishlist_cache(workspace_id, customer_id, wishlist.id)

                    logger.info(
                        "Product removed from wishlist",
                        extra={
                            'workspace_id': workspace_id,
                            'customer_id': customer_id,
                            'product_id': product_id,
                            'wishlist_id': wishlist.id
                        }
                    )

                    return {
                        'success': True,
                        'message': 'Product removed from wishlist'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Product not found in wishlist'
                    }

        except Wishlist.DoesNotExist:
            return {
                'success': False,
                'error': 'Wishlist not found'
            }
        except Exception as e:
            logger.error(
                "Failed to remove product from wishlist",
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
                'error': 'Failed to remove product from wishlist'
            }

    @staticmethod
    def get_wishlist_items(
        workspace_id: str,
        customer_id: str,
        wishlist_id: Optional[str] = None,
        include_product_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get wishlist items with optional product details

        Cameroon Market: Mobile-optimized wishlist display
        Performance: Optimized queries with caching
        """
        try:
            # Get wishlist
            if wishlist_id:
                wishlist = Wishlist.objects.get(
                    id=wishlist_id,
                    workspace_id=workspace_id,
                    customer_id=customer_id
                )
            else:
                wishlist = WishlistService.get_or_create_default_wishlist(
                    workspace_id, customer_id
                )

            # Generate cache key
            cache_key = f"{WishlistService.WISHLIST_CACHE_PREFIX}items_{wishlist.id}_{include_product_details}"

            # Try cache first
            cached_items = cache.get(cache_key)
            if cached_items:
                return {
                    'success': True,
                    'wishlist': WishlistService._format_wishlist(wishlist),
                    'items': cached_items
                }

            # Get wishlist items
            wishlist_items = WishlistItem.objects.filter(
                wishlist=wishlist
            ).select_related('product')

            if include_product_details:
                wishlist_items = wishlist_items.select_related(
                    'product__category', 'product__sub_category'
                )

            formatted_items = [
                WishlistService._format_wishlist_item(item, include_product_details)
                for item in wishlist_items
            ]

            # Cache the items
            cache.set(cache_key, formatted_items, WishlistService.CACHE_TIMEOUT)

            return {
                'success': True,
                'wishlist': WishlistService._format_wishlist(wishlist),
                'items': formatted_items
            }

        except Wishlist.DoesNotExist:
            return {
                'success': False,
                'error': 'Wishlist not found'
            }
        except Exception as e:
            logger.error(
                "Failed to get wishlist items",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer_id,
                    'wishlist_id': wishlist_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load wishlist items'
            }

    @staticmethod
    def get_customer_wishlists(
        workspace_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Get all wishlists for customer"""
        try:
            cache_key = f"{WishlistService.WISHLIST_CACHE_PREFIX}all_{workspace_id}_{customer_id}"

            # Try cache first
            cached_wishlists = cache.get(cache_key)
            if cached_wishlists:
                return {
                    'success': True,
                    'wishlists': cached_wishlists
                }

            wishlists = Wishlist.objects.filter(
                workspace_id=workspace_id,
                customer_id=customer_id
            ).prefetch_related('items')

            formatted_wishlists = [
                WishlistService._format_wishlist(wishlist)
                for wishlist in wishlists
            ]

            # Cache the wishlists
            cache.set(cache_key, formatted_wishlists, WishlistService.CACHE_TIMEOUT)

            return {
                'success': True,
                'wishlists': formatted_wishlists
            }

        except Exception as e:
            logger.error(
                "Failed to get customer wishlists",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load wishlists'
            }

    @staticmethod
    def is_product_in_wishlist(
        workspace_id: str,
        customer_id: str,
        product_id: str,
        wishlist_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if product is in customer wishlist"""
        try:
            # Get wishlist
            if wishlist_id:
                wishlist = Wishlist.objects.get(
                    id=wishlist_id,
                    workspace_id=workspace_id,
                    customer_id=customer_id
                )
            else:
                wishlist = WishlistService.get_or_create_default_wishlist(
                    workspace_id, customer_id
                )

            exists = WishlistItem.objects.filter(
                wishlist=wishlist,
                product_id=product_id
            ).exists()

            return {
                'success': True,
                'in_wishlist': exists,
                'wishlist_id': wishlist.id
            }

        except Wishlist.DoesNotExist:
            return {
                'success': False,
                'error': 'Wishlist not found'
            }
        except Exception as e:
            logger.error(
                "Failed to check product in wishlist",
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
                'error': 'Failed to check wishlist status'
            }

    # Helper methods

    @staticmethod
    def _format_wishlist(wishlist: Wishlist) -> Dict[str, Any]:
        """Format wishlist for response"""
        return {
            'id': wishlist.id,
            'name': wishlist.name,
            'is_default': wishlist.is_default,
            'is_public': wishlist.is_public,
            'items_count': wishlist.items_count,
            'is_empty': wishlist.is_empty,
            'created_at': wishlist.created_at.isoformat() if wishlist.created_at else None,
            'updated_at': wishlist.updated_at.isoformat() if wishlist.updated_at else None
        }

    @staticmethod
    def _format_wishlist_item(
        wishlist_item: WishlistItem,
        include_product_details: bool = True
    ) -> Dict[str, Any]:
        """Format wishlist item for response"""
        formatted_item = {
            'id': wishlist_item.id,
            'wishlist_id': wishlist_item.wishlist_id,
            'product_id': wishlist_item.product_id,
            'added_at_price': float(wishlist_item.added_at_price) if wishlist_item.added_at_price else None,
            'notes': wishlist_item.notes,
            'priority': wishlist_item.priority,
            'price_changed': wishlist_item.price_changed,
            'price_difference': float(wishlist_item.price_difference) if wishlist_item.price_difference else 0,
            'price_change_percentage': wishlist_item.price_change_percentage,
            'added_at': wishlist_item.created_at.isoformat() if wishlist_item.created_at else None
        }

        if include_product_details:
            product = wishlist_item.product
            formatted_item['product'] = {
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

        return formatted_item

    @staticmethod
    def _clear_wishlist_cache(workspace_id: str, customer_id: str, wishlist_id: str):
        """Clear wishlist-related caches"""
        try:
            cache.delete_many([
                f"{WishlistService.WISHLIST_CACHE_PREFIX}default_{workspace_id}_{customer_id}",
                f"{WishlistService.WISHLIST_CACHE_PREFIX}items_{wishlist_id}_True",
                f"{WishlistService.WISHLIST_CACHE_PREFIX}items_{wishlist_id}_False",
                f"{WishlistService.WISHLIST_CACHE_PREFIX}all_{workspace_id}_{customer_id}"
            ])
        except Exception as e:
            logger.warning(f"Failed to clear wishlist cache: {str(e)}")


# Global instance for easy access
wishlist_service = WishlistService()