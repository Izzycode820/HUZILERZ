# Cart service for reusable cart operations
# IMPORTANT: Business logic separated from GraphQL mutations

from django.db import transaction
from workspace.storefront.models import Cart, CartItem
from workspace.store.models import Product
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class CartService:
    """
    Service class for cart operations

    Reusable business logic for cart management
    Used by GraphQL mutations and potentially other consumers
    """

    @staticmethod
    @transaction.atomic
    def add_item(cart, product, quantity=1, variant=None, session_id=None):
        """
        Add item to cart with atomic operations

        Performance: Uses select_for_update for stock consistency
        Security: Validates stock availability
        Analytics: Tracks add_to_cart event if session_id provided

        Args:
            cart: Cart instance
            product: Product instance
            quantity: Quantity to add (default: 1)
            variant: Optional ProductVariant instance
            session_id: Optional session ID for analytics tracking (string or UUID)
        """
        from workspace.store.models import ProductVariant

        # Lock product/variant for stock check
        if variant:
            variant = ProductVariant.objects.select_for_update().get(id=variant.id)
            # Variants inherit product inventory or would need separate inventory tracking
            # For now, we'll use product inventory for variants
            stock_quantity = product.inventory_quantity
            item_price = variant.price or product.price
        else:
            product = Product.objects.select_for_update().get(id=product.id)
            stock_quantity = product.inventory_quantity
            item_price = product.price

        # Check stock availability
        if product.track_inventory and stock_quantity < quantity:
            if not product.allow_backorders:
                raise ValueError(f"Insufficient stock for {product.name}")

        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={
                'quantity': quantity,
                'price_snapshot': item_price
            }
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Recalculate totals
        cart.calculate_totals()

        # Recalculate discount if applied (amounts may change with new items)
        if cart.applied_discount:
            CartService._recalculate_cart_discount(cart)

        logger.info(
            "Item added to cart via service",
            extra={
                'cart_id': cart.id,
                'product_id': product.id,
                'variant_id': variant.id if variant else None,
                'quantity': quantity,
                'item_created': created  # Renamed from 'created' to avoid LogRecord.created conflict
            }
        )

        # Track analytics event (graceful failure - never blocks cart operations)
        if session_id:
            CartService._track_add_to_cart(cart, product, quantity, variant, session_id)

        return cart_item

    @staticmethod
    @transaction.atomic
    def update_item_quantity(cart, product_id, quantity, variant_id=None, session_id=None):
        """
        Update cart item quantity

        Performance: Atomic operation for consistency
        Analytics: Tracks cart updates if session_id provided

        Args:
            cart: Cart instance
            product_id: Product ID to update
            quantity: New quantity (0 removes item)
            variant_id: Optional variant ID
            session_id: Optional session ID for analytics tracking
        """
        from workspace.store.models import ProductVariant

        if quantity <= 0:
            return CartService.remove_item(cart, product_id, variant_id, session_id)

        # Lock product for stock check (avoid N+1)
        product = Product.objects.select_for_update().get(id=product_id)

        # Lock variant if needed
        variant = None
        if variant_id:
            from workspace.store.models import ProductVariant
            variant = ProductVariant.objects.select_for_update().get(id=variant_id)

        # Variants inherit product inventory
        stock_quantity = product.inventory_quantity

        # Check stock availability
        if product.track_inventory and stock_quantity < quantity:
            if not product.allow_backorders:
                raise ValueError(f"Insufficient stock for {product.name}")

        # Find cart item with variant support
        if variant_id:
            cart_item = cart.items.get(product_id=product_id, variant_id=variant_id)
        else:
            cart_item = cart.items.get(product_id=product_id)

        cart_item.quantity = quantity
        cart_item.save()

        # Recalculate totals
        cart.calculate_totals()

        # Recalculate discount if applied (amounts may change with quantity)
        if cart.applied_discount:
            CartService._recalculate_cart_discount(cart)

        logger.info(
            "Cart item quantity updated via service",
            extra={
                'cart_id': cart.id,
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': quantity
            }
        )

        return cart_item

    @staticmethod
    def remove_item(cart, product_id, variant_id=None, session_id=None):
        """
        Remove item from cart

        Args:
            cart: Cart instance
            product_id: Product ID to remove
            variant_id: Optional variant ID
            session_id: Optional session ID for analytics tracking
        """
        try:
            if variant_id:
                cart_item = cart.items.get(product_id=product_id, variant_id=variant_id)
            else:
                cart_item = cart.items.get(product_id=product_id)

            cart_item.delete()
            cart.calculate_totals()

            # Recalculate discount if applied (amounts may change with removed items)
            if cart.applied_discount:
                CartService._recalculate_cart_discount(cart)

            logger.info(
                "Item removed from cart via service",
                extra={
                    'cart_id': cart.id,
                    'product_id': product_id,
                    'variant_id': variant_id
                }
            )

            return True
        except CartItem.DoesNotExist:
            logger.warning(
                "Item not found in cart",
                extra={
                    'cart_id': cart.id,
                    'product_id': product_id,
                    'variant_id': variant_id
                }
            )
            return False

    @staticmethod
    def clear_cart(cart):
        """
        Clear all items from cart
        """
        item_count = cart.items.count()
        cart.items.all().delete()
        cart.subtotal = 0
        cart.save(update_fields=['subtotal'])

        logger.info(
            "Cart cleared via service",
            extra={
                'cart_id': cart.id,
                'item_count': item_count
            }
        )

    @staticmethod
    def get_cart_summary(cart):
        """
        Get cart summary for display

        Performance: Optimized query for summary data
        """
        cart_with_items = Cart.objects.select_related('workspace').prefetch_related(
            'items__product',
            'items__variant'
        ).get(id=cart.id)

        summary = {
            'id': cart_with_items.id,
            'item_count': cart_with_items.item_count,
            'subtotal': cart_with_items.subtotal,
            'is_empty': cart_with_items.is_empty,
            'items': []
        }

        for item in cart_with_items.items.all():
            item_data = {
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': item.price_snapshot,
                'total_price': item.total_price
            }

            # Add variant information if available
            if item.variant:
                item_data['variant_id'] = item.variant.id
                item_data['variant_options'] = {
                    'option1': item.variant.option1,
                    'option2': item.variant.option2,
                    'option3': item.variant.option3
                }
                item_data['variant_sku'] = item.variant.sku

            summary['items'].append(item_data)

        return summary

    @staticmethod
    def validate_cart_for_checkout(cart):
        """
        Validate cart before checkout

        Business logic: Check stock, prices, etc.
        Performance: Optimized query with select_related to avoid N+1
        """
        if cart.is_empty:
            raise ValueError("Cart is empty")

        # Check stock for all items (prefetch products to avoid N+1)
        cart_items = cart.items.select_related('product', 'variant').all()
        for item in cart_items:
            if item.product.track_inventory:
                # Check variant stock if variant exists
                if item.variant:
                    # Variants inherit product inventory
                    stock_quantity = item.product.inventory_quantity
                else:
                    stock_quantity = item.product.inventory_quantity

                if stock_quantity < item.quantity:
                    if not item.product.allow_backorders:
                        item_name = f"{item.product.name} ({item.variant.option1})" if item.variant else item.product.name
                        raise ValueError(f"Insufficient stock for {item_name}")

        # Check if prices are still valid (optional)
        # This could compare price_snapshot with current product.price

        logger.info(
            "Cart validated for checkout",
            extra={
                'cart_id': cart.id,
                'item_count': cart.item_count,
                'subtotal': cart.subtotal
            }
        )

        return True

    # ============================================================================
    # DISCOUNT INTEGRATION
    # ============================================================================

    @staticmethod
    @transaction.atomic
    def apply_discount(cart, discount_code, customer=None):
        """
        Apply discount code to cart

        Args:
            cart: Cart instance
            discount_code: Discount code to apply
            customer: Optional customer instance

        Returns:
            Dict with success status and discount details

        Performance: Atomic transaction with proper locking
        Security: Validates discount before application
        """
        from workspace.storefront.services.discount_service import storefront_discount_service

        try:
            result = storefront_discount_service.validate_and_apply_discount(
                workspace=cart.workspace,
                cart=cart,
                discount_code=discount_code,
                customer=customer
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to apply discount to cart",
                extra={
                    'cart_id': cart.id,
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
    @transaction.atomic
    def remove_discount(cart):
        """
        Remove discount from cart

        Args:
            cart: Cart instance

        Returns:
            Dict with success status
        """
        from workspace.storefront.services.discount_service import storefront_discount_service

        try:
            result = storefront_discount_service.remove_discount_from_cart(cart)
            return result

        except Exception as e:
            logger.error(
                "Failed to remove discount from cart",
                extra={
                    'cart_id': cart.id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': f'Failed to remove discount: {str(e)}'
            }

    @staticmethod
    @transaction.atomic
    def apply_automatic_discounts(cart, customer=None):
        """
        Apply best automatic discount to cart

        Args:
            cart: Cart instance
            customer: Optional customer instance

        Returns:
            Dict with success status and applied discount
        """
        from workspace.storefront.services.discount_service import storefront_discount_service

        try:
            result = storefront_discount_service.apply_automatic_discounts(
                workspace=cart.workspace,
                cart=cart,
                customer=customer
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to apply automatic discounts to cart",
                extra={
                    'cart_id': cart.id,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': f'Failed to apply automatic discounts: {str(e)}'
            }

    @staticmethod
    def _recalculate_cart_discount(cart):
        """
        Recalculate discount after cart changes (internal helper)

        Args:
            cart: Cart instance (already locked by parent transaction)

        Note: Called by add_item, update_item_quantity, remove_item
        """
        from workspace.storefront.services.discount_service import storefront_discount_service

        try:
            result = storefront_discount_service.recalculate_cart_discount(cart)

            if not result['success']:
                logger.warning(
                    "Discount recalculation failed",
                    extra={
                        'cart_id': cart.id,
                        'error': result.get('error')
                    }
                )

        except Exception as e:
            # Log but don't crash cart operations
            logger.warning(
                "Failed to recalculate discount",
                extra={
                    'cart_id': cart.id,
                    'error': str(e)
                }
            )

    # ============================================================================
    # ANALYTICS TRACKING (Internal Helpers)
    # ============================================================================

    @staticmethod
    def _track_add_to_cart(cart, product, quantity, variant, session_id):
        """
        Track add_to_cart analytics event (internal helper)

        Reliability: Never raises exceptions - graceful failure
        Performance: Non-blocking, logs errors only

        Args:
            cart: Cart instance
            product: Product instance
            quantity: Quantity added
            variant: Optional ProductVariant instance
            session_id: Session ID (string or UUID)
        """
        try:
            from workspace.analytics.services.event_tracking_service import EventTrackingService

            # Convert session_id to UUID if string (validate format)
            try:
                if isinstance(session_id, str):
                    session_uuid = UUID(session_id)
                else:
                    session_uuid = session_id
            except (ValueError, AttributeError) as e:
                logger.warning(
                    "Invalid session_id format for analytics",
                    extra={'session_id': session_id, 'error': str(e)}
                )
                return

            # Initialize tracker
            tracker = EventTrackingService(cart.workspace)

            # Track event (plan gating happens inside EventTrackingService)
            tracker.track_add_to_cart(
                session_id=session_uuid,
                product_id=product.id,
                quantity=quantity,
                variant_id=variant.id if variant else None
            )

        except Exception as e:
            # Log but never crash cart operations
            logger.warning(
                "Analytics tracking failed for add_to_cart",
                extra={
                    'cart_id': cart.id,
                    'product_id': product.id,
                    'error': str(e)
                }
            )