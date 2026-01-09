"""
Storefront Discount Service - Customer-facing discount operations for CARTS

SEPARATION OF CONCERNS:
- This service handles CART discount operations (customer-facing)
- Store discount_service handles admin CRUD and ORDER payment confirmation
- Shared: Both use store/models/discount_model.py

Production-Ready Principles (CLAUDE.md):
- Performance: < 100ms cart discount operations
- Scalability: Atomic transactions, proper locking
- Reliability: Comprehensive error handling, rollback safety
- Security: Workspace scoping, customer validation
- Maintainability: Clear separation, structured logging
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.db import transaction
from django.core.cache import cache
import logging

from workspace.store.models.discount_model import Discount, DiscountUsage
from workspace.store.services.discount_service import DiscountService
from workspace.storefront.models.cart_model import Cart
from workspace.core.models.customer_model import Customer

logger = logging.getLogger('workspace.storefront.discounts')


class StorefrontDiscountService:
    """
    Customer-facing discount service for cart operations

    Scope: CART ONLY (not orders)
    - Validate discount codes for carts
    - Apply/remove discounts to/from carts
    - Calculate cart totals with discounts
    - Get automatic discounts

    Performance: < 100ms for cart operations
    Reliability: Atomic transactions with proper error handling
    Security: Workspace scoping and customer validation
    """

    # Cache configuration
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_PREFIX = 'storefront_cart_discount_'

    @staticmethod
    def validate_and_apply_discount(
        workspace,
        cart: Cart,
        discount_code: str,
        customer: Optional[Customer] = None
    ) -> Dict[str, Any]:
        """
        Validate and apply discount code to cart

        Args:
            workspace: Workspace instance
            cart: Cart instance
            discount_code: Discount code to apply
            customer: Optional customer instance

        Returns:
            Dict with success status, discount details, and updated cart

        Performance: Single atomic transaction with proper locking
        Security: Comprehensive validation before application
        Reliability: Rollback on any error
        """
        try:
            with transaction.atomic():
                # Lock cart for atomic update
                cart = Cart.objects.select_for_update().get(id=cart.id)

                # Validate discount code using store service
                validation = DiscountService.validate_discount_code(
                    workspace=workspace,
                    code=discount_code,
                    customer=customer,
                    cart=cart
                )

                if not validation['valid']:
                    return {
                        'success': False,
                        'error': validation['error']
                    }

                discount = validation['discount']

                # Calculate discount amount using store service
                calculation = DiscountService.calculate_cart_discount(
                    discount=discount,
                    cart=cart,
                    customer=customer
                )

                if not calculation['success']:
                    return {
                        'success': False,
                        'error': calculation['error']
                    }

                # Apply discount to cart
                cart.discount_code = discount.code
                cart.discount_amount = calculation['discount_amount']
                cart.applied_discount = discount
                cart.save(update_fields=['discount_code', 'discount_amount', 'applied_discount'])

                # Clear cache for this cart
                StorefrontDiscountService._clear_cart_cache(cart.id)

                logger.info(
                    "Discount applied to cart",
                    extra={
                        'workspace_id': str(workspace.id),
                        'cart_id': str(cart.id),
                        'discount_code': discount.code,
                        'discount_amount': float(calculation['discount_amount']),
                        'customer_id': str(customer.id) if customer else None
                    }
                )

                return {
                    'success': True,
                    'discount': {
                        'code': discount.code,
                        'name': discount.name,
                        'discount_type': discount.discount_type,
                        'discount_amount': float(calculation['discount_amount']),
                        'item_discounts': calculation.get('item_discounts', [])
                    },
                    'cart': {
                        'subtotal': float(cart.subtotal),
                        'discount_amount': float(cart.discount_amount),
                        'total': float(cart.subtotal - cart.discount_amount)
                    },
                    'message': f'Discount {discount.code} applied successfully'
                }

        except Cart.DoesNotExist:
            logger.warning(f"Cart {cart.id} not found")
            return {
                'success': False,
                'error': 'Cart not found'
            }
        except Exception as e:
            logger.error(
                "Failed to apply discount to cart",
                extra={
                    'cart_id': str(cart.id),
                    'discount_code': discount_code,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': f'Failed to apply discount: {str(e)}'
            }

    @staticmethod
    def remove_discount_from_cart(cart: Cart) -> Dict[str, Any]:
        """
        Remove discount from cart

        Args:
            cart: Cart instance

        Returns:
            Dict with success status and updated cart

        Performance: Atomic cart update
        Reliability: Rollback safety
        """
        try:
            with transaction.atomic():
                # Lock cart for atomic update
                cart = Cart.objects.select_for_update().get(id=cart.id)

                discount_code = cart.discount_code

                # Remove discount
                cart.discount_code = ''
                cart.discount_amount = Decimal('0.00')
                cart.applied_discount = None
                cart.save(update_fields=['discount_code', 'discount_amount', 'applied_discount'])

                # Clear cache
                StorefrontDiscountService._clear_cart_cache(cart.id)

                logger.info(
                    "Discount removed from cart",
                    extra={
                        'cart_id': str(cart.id),
                        'discount_code': discount_code
                    }
                )

                return {
                    'success': True,
                    'cart': {
                        'subtotal': float(cart.subtotal),
                        'discount_amount': 0.0,
                        'total': float(cart.subtotal)
                    },
                    'message': 'Discount removed successfully'
                }

        except Cart.DoesNotExist:
            logger.warning(f"Cart {cart.id} not found")
            return {
                'success': False,
                'error': 'Cart not found'
            }
        except Exception as e:
            logger.error(
                "Failed to remove discount from cart",
                extra={
                    'cart_id': str(cart.id),
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': f'Failed to remove discount: {str(e)}'
            }

    @staticmethod
    def apply_automatic_discounts(
        workspace,
        cart: Cart,
        customer: Optional[Customer] = None
    ) -> Dict[str, Any]:
        """
        Apply best automatic discount to cart

        Args:
            workspace: Workspace instance
            cart: Cart instance
            customer: Optional customer instance

        Returns:
            Dict with success status and applied discount (if any)

        Performance: Cached automatic discount lookup
        Reliability: Applies best discount automatically
        """
        try:
            # Get applicable automatic discounts using store service
            automatic_discounts = DiscountService.get_automatic_discounts(
                workspace=workspace,
                cart=cart,
                customer=customer
            )

            if not automatic_discounts:
                return {
                    'success': True,
                    'message': 'No automatic discounts available',
                    'discount_applied': False
                }

            # Calculate discount for each and pick the best one
            best_discount = None
            best_discount_amount = Decimal('0.00')
            best_calculation = None

            for discount in automatic_discounts:
                calculation = DiscountService.calculate_cart_discount(
                    discount=discount,
                    cart=cart,
                    customer=customer
                )

                if calculation['success'] and calculation['discount_amount'] > best_discount_amount:
                    best_discount = discount
                    best_discount_amount = calculation['discount_amount']
                    best_calculation = calculation

            if not best_discount:
                return {
                    'success': True,
                    'message': 'No applicable automatic discounts',
                    'discount_applied': False
                }

            # Apply best discount using atomic transaction
            with transaction.atomic():
                cart = Cart.objects.select_for_update().get(id=cart.id)

                cart.discount_code = best_discount.code
                cart.discount_amount = best_discount_amount
                cart.applied_discount = best_discount
                cart.save(update_fields=['discount_code', 'discount_amount', 'applied_discount'])

                # Clear cache
                StorefrontDiscountService._clear_cart_cache(cart.id)

                logger.info(
                    "Automatic discount applied to cart",
                    extra={
                        'workspace_id': str(workspace.id),
                        'cart_id': str(cart.id),
                        'discount_code': best_discount.code,
                        'discount_amount': float(best_discount_amount)
                    }
                )

                return {
                    'success': True,
                    'discount_applied': True,
                    'discount': {
                        'code': best_discount.code,
                        'name': best_discount.name,
                        'discount_type': best_discount.discount_type,
                        'discount_amount': float(best_discount_amount),
                        'item_discounts': best_calculation.get('item_discounts', [])
                    },
                    'cart': {
                        'subtotal': float(cart.subtotal),
                        'discount_amount': float(cart.discount_amount),
                        'total': float(cart.subtotal - cart.discount_amount)
                    },
                    'message': f'Automatic discount {best_discount.code} applied'
                }

        except Exception as e:
            logger.error(
                "Failed to apply automatic discounts",
                extra={
                    'cart_id': str(cart.id),
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': f'Failed to apply automatic discounts: {str(e)}'
            }

    @staticmethod
    def recalculate_cart_discount(cart: Cart, customer: Optional[Customer] = None) -> Dict[str, Any]:
        """
        Recalculate discount for cart (useful after cart items change)

        Args:
            cart: Cart instance
            customer: Optional customer instance

        Returns:
            Dict with success status and updated discount amount

        Use Case: Called after cart item quantity changes or items added/removed
        """
        try:
            # If no discount applied, nothing to recalculate
            if not cart.applied_discount:
                return {
                    'success': True,
                    'message': 'No discount to recalculate',
                    'discount_amount': 0.0
                }

            with transaction.atomic():
                cart = Cart.objects.select_for_update().get(id=cart.id)
                discount = cart.applied_discount

                # Re-validate discount (might no longer be valid)
                validation = DiscountService.validate_discount_code(
                    workspace=cart.workspace,
                    code=discount.code,
                    customer=customer,
                    cart=cart
                )

                if not validation['valid']:
                    # Discount no longer valid, remove it
                    cart.discount_code = ''
                    cart.discount_amount = Decimal('0.00')
                    cart.applied_discount = None
                    cart.save(update_fields=['discount_code', 'discount_amount', 'applied_discount'])

                    return {
                        'success': True,
                        'discount_removed': True,
                        'message': f'Discount {discount.code} is no longer valid and was removed',
                        'discount_amount': 0.0
                    }

                # Recalculate discount amount
                calculation = DiscountService.calculate_cart_discount(
                    discount=discount,
                    cart=cart,
                    customer=customer
                )

                if not calculation['success']:
                    # Remove discount if calculation fails
                    cart.discount_code = ''
                    cart.discount_amount = Decimal('0.00')
                    cart.applied_discount = None
                    cart.save(update_fields=['discount_code', 'discount_amount', 'applied_discount'])

                    return {
                        'success': True,
                        'discount_removed': True,
                        'message': f'Discount {discount.code} could not be recalculated and was removed',
                        'discount_amount': 0.0
                    }

                # Update cart with new discount amount
                cart.discount_amount = calculation['discount_amount']
                cart.save(update_fields=['discount_amount'])

                # Clear cache
                StorefrontDiscountService._clear_cart_cache(cart.id)

                logger.info(
                    "Cart discount recalculated",
                    extra={
                        'cart_id': str(cart.id),
                        'discount_code': discount.code,
                        'new_discount_amount': float(calculation['discount_amount'])
                    }
                )

                return {
                    'success': True,
                    'discount_recalculated': True,
                    'discount_amount': float(calculation['discount_amount']),
                    'message': 'Discount recalculated successfully'
                }

        except Cart.DoesNotExist:
            logger.warning(f"Cart {cart.id} not found")
            return {
                'success': False,
                'error': 'Cart not found'
            }
        except Exception as e:
            logger.error(
                "Failed to recalculate cart discount",
                extra={
                    'cart_id': str(cart.id),
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': f'Failed to recalculate discount: {str(e)}'
            }

    @staticmethod
    def get_cart_summary_with_discount(cart: Cart) -> Dict[str, Any]:
        """
        Get cart summary with discount breakdown

        Args:
            cart: Cart instance

        Returns:
            Dict with cart totals and discount details

        Performance: Single query with select_related
        """
        try:
            # Get cart with discount relationship
            cart = Cart.objects.select_related('applied_discount').get(id=cart.id)

            summary = {
                'subtotal': float(cart.subtotal),
                'discount_amount': float(cart.discount_amount or 0),
                'total': float(cart.subtotal - (cart.discount_amount or Decimal('0.00'))),
                'item_count': cart.item_count,
                'has_discount': bool(cart.applied_discount)
            }

            if cart.applied_discount:
                summary['discount'] = {
                    'code': cart.discount_code,
                    'name': cart.applied_discount.name,
                    'discount_type': cart.applied_discount.discount_type,
                }

            return {
                'success': True,
                'cart_summary': summary
            }

        except Cart.DoesNotExist:
            logger.warning(f"Cart {cart.id} not found")
            return {
                'success': False,
                'error': 'Cart not found'
            }
        except Exception as e:
            logger.error(
                "Failed to get cart summary",
                extra={
                    'cart_id': str(cart.id),
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': f'Failed to get cart summary: {str(e)}'
            }

    # Helper methods

    @staticmethod
    def _clear_cart_cache(cart_id: str):
        """Clear cart-related discount caches"""
        try:
            cache_key = f"{StorefrontDiscountService.CACHE_PREFIX}cart_{cart_id}"
            cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to clear cart cache: {str(e)}")


# Global instance for easy access
storefront_discount_service = StorefrontDiscountService()
