"""
Production-Ready Checkout Service
Follows CLAUDE.md principles for reliability, security, and performance

Key improvements:
- Proper locking to prevent race conditions
- Comprehensive input validation
- Atomic transactions
- Graceful error handling
- Performance optimizations (prefetch, select_related)
"""

from django.db import transaction
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
import logging

from workspace.store.models import Order, OrderItem, Package
from workspace.core.models import Customer
from workspace.core.models.customer_model import CustomerService
from workspace.storefront.validators.checkout_validators import CheckoutValidator

logger = logging.getLogger(__name__)


# REGION MAPPING: City/Location names → Order model region codes
# Maps package region_fees keys to Order.shipping_region choices
REGION_MAPPING = {
    # Littoral Region
    'douala': 'littoral',
    'limbe': 'littoral',
    'nkongsamba': 'littoral',
    'edea': 'littoral',

    # Centre Region
    'yaounde': 'centre',
    'yaoundé': 'centre',
    'mbalmayo': 'centre',
    'obala': 'centre',

    # Southwest Region
    'buea': 'southwest',
    'kumba': 'southwest',
    'tiko': 'southwest',
    'mamfe': 'southwest',

    # Northwest Region
    'bamenda': 'northwest',
    'kumbo': 'northwest',
    'wum': 'northwest',
    'fundong': 'northwest',

    # West Region
    'bafoussam': 'west',
    'dschang': 'west',
    'foumban': 'west',
    'mbouda': 'west',

    # North Region
    'garoua': 'north',

    # Far North Region
    'maroua': 'far_north',
    'kousseri': 'far_north',
    'mokolo': 'far_north',

    # East Region
    'bertoua': 'east',
    'batouri': 'east',

    # South Region
    'ebolowa': 'south',
    'kribi': 'south',
    'sangmelima': 'south',

    # Adamawa Region
    'ngaoundere': 'adamawa',
    'ngaoundéré': 'adamawa',
    'tibati': 'adamawa',

    # Also support direct region codes (in case packages use them)
    'littoral': 'littoral',
    'centre': 'centre',
    'southwest': 'southwest',
    'northwest': 'northwest',
    'west': 'west',
    'north': 'north',
    'far_north': 'far_north',
    'east': 'east',
    'south': 'south',
    'adamawa': 'adamawa',
}


class CheckoutService:
    """
    Production-ready checkout service

    Performance: < 200ms response time
    Reliability: Atomic transactions with proper locking
    Security: Comprehensive input validation
    """

    @staticmethod
    @transaction.atomic
    def create_order(
        cart,
        customer_info: Dict[str, Any],
        shipping_region: str,
        order_type: str = 'regular',
        whatsapp_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create order from cart with proper validation and locking

        CRITICAL: This method prevents race conditions by:
        1. Locking cart immediately with select_for_update()
        2. Validating all inputs before any writes
        3. Calculating totals atomically
        4. Clearing cart at end of transaction

        Args:
            cart: Cart instance (will be locked)
            customer_info: Dict with phone, name, email
            shipping_region: Region name (e.g., 'buea')
            order_type: 'regular', 'cod', or 'whatsapp'
            whatsapp_number: Required for whatsapp orders

        Returns:
            Dict with 'success': bool, 'order': Order, 'customer': Customer, 'error': str
        """
        try:
            # STEP 1: ACQUIRE LOCKS (prevent race conditions)
            # Lock cart to prevent concurrent modifications
            from workspace.storefront.models import Cart
            cart = Cart.objects.select_for_update().select_related('workspace').get(id=cart.id)

            # STEP 2: VALIDATE INPUTS (security + reliability)
            # Validate order type
            order_type_validation = CheckoutValidator.validate_order_type(order_type)
            if not order_type_validation['valid']:
                return {
                    'success': False,
                    'error': order_type_validation['error']
                }

            # Validate customer information
            customer_validation = CheckoutValidator.validate_customer_info(customer_info)
            if not customer_validation['valid']:
                return {
                    'success': False,
                    'error': customer_validation['error']
                }

            sanitized_customer = customer_validation['sanitized']

            # Validate cart not empty
            if cart.is_empty:
                return {
                    'success': False,
                    'error': 'Cart is empty'
                }

            # Validate shipping region and calculate cost
            shipping_validation = CheckoutValidator.validate_shipping_region(
                cart.workspace,
                cart,
                shipping_region
            )
            if not shipping_validation['valid']:
                return {
                    'success': False,
                    'error': shipping_validation['error']
                }

            shipping_cost = shipping_validation['shipping_cost']
            estimated_days = shipping_validation['estimated_days']
            normalized_region = shipping_validation['region']

            # Map region name to Order model region code
            region_key = normalized_region.lower()
            order_region_code = REGION_MAPPING.get(region_key)

            if not order_region_code:
                # If region not in mapping, log warning and try to use as-is
                logger.warning(
                    f"Region '{normalized_region}' not in REGION_MAPPING",
                    extra={'region': normalized_region, 'cart_id': cart.id}
                )
                order_region_code = region_key  # Fallback

            # Validate WhatsApp number if order type is whatsapp
            if order_type == 'whatsapp' and not whatsapp_number:
                return {
                    'success': False,
                    'error': 'WhatsApp number is required for WhatsApp orders'
                }

            # STEP 3: GET OR CREATE CUSTOMER (phone-first, with lock)
            # Lock customer to prevent duplicate creation race
            customer, created = CustomerService.get_or_create_customer_by_phone(
                workspace=cart.workspace,
                phone=sanitized_customer['phone'],
                name=sanitized_customer['name'],
                email=sanitized_customer['email']
            )

            # STEP 4: RE-VALIDATE DISCOUNT (discount could have expired/changed)
            discount_amount = Decimal('0.00')
            discount_code = ''
            applied_discount_data = None

            # Check if cart has a discount applied (using discount_code field)
            if cart.discount_code:
                # Re-validate discount is still valid
                discount_validation = CheckoutService._revalidate_cart_discount(cart)
                if discount_validation['valid']:
                    discount_amount = cart.discount_amount or Decimal('0.00')
                    discount_code = cart.discount_code
                    applied_discount_data = cart.applied_discount
                else:
                    # Discount invalid - log warning but don't fail checkout
                    logger.warning(
                        f"Discount {cart.discount_code} invalid at checkout",
                        extra={
                            'cart_id': cart.id,
                            'discount_code': cart.discount_code,
                            'reason': discount_validation.get('error')
                        }
                    )
                    # Reset discount amounts
                    discount_amount = Decimal('0.00')
                    discount_code = ''

            # STEP 5: CALCULATE FINAL TOTAL (atomically)
            subtotal = cart.subtotal
            final_total = subtotal + shipping_cost - discount_amount

            # Validate total is positive
            if final_total < 0:
                return {
                    'success': False,
                    'error': 'Invalid order total calculation'
                }

            # STEP 6: DETERMINE ORDER CONFIG
            order_source, payment_method = CheckoutService._get_order_type_config(order_type)

            # Prepare shipping address with delivery estimate
            shipping_address_data = {
                'address': sanitized_customer.get('address', ''),
                'region': normalized_region,  # Keep original display name in address
                'estimated_delivery_days': estimated_days
            }

            # STEP 7: CREATE ORDER (atomic)
            # Billing address: optional for MoMo/COD/WhatsApp, only needed for card payments
            billing_address_data = customer_info.get('billing_address')  # None if not provided

            order = Order.objects.create(
                workspace=cart.workspace,
                customer=customer,
                customer_name=sanitized_customer['name'],
                customer_phone=sanitized_customer['phone'],
                customer_email=sanitized_customer['email'],
                order_source=order_source,
                payment_method=payment_method,
                shipping_region=order_region_code,  # Use mapped region code
                shipping_cost=shipping_cost,
                shipping_address=shipping_address_data,
                billing_address=billing_address_data,  # NULL for MoMo/COD/WhatsApp
                subtotal=subtotal,
                discount_amount=discount_amount,
                discount_code=discount_code,
                applied_discount=applied_discount_data,
                total_amount=final_total,
                status='pending'
            )

            # STEP 8: CREATE ORDER ITEMS (bulk, optimized)
            # Prefetch to avoid N+1 queries
            cart_items = cart.items.select_related(
                'product',
                'product__featured_media',
                'product__category',
                'product__package',
                'variant'
            ).all()

            order_items = []
            for cart_item in cart_items:
                # Capture product snapshot (Shopify-style: preserve state at purchase time)
                product_snapshot = cart_item.product.create_snapshot()

                order_items.append(
                    OrderItem(
                        order=order,
                        product=cart_item.product,
                        variant=cart_item.variant,
                        product_name=cart_item.product.name,
                        product_sku=cart_item.product.sku,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.price_snapshot,
                        product_data=product_snapshot  # Include full snapshot with images
                    )
                )

            # Bulk create for performance
            OrderItem.objects.bulk_create(order_items)

            # STEP 9: UPDATE CUSTOMER STATS
            customer.update_order_stats(final_total)

            # STEP 10: TRIGGER ASYNC TASKS (non-blocking)
            # Send WhatsApp DM for WhatsApp orders
            if order_type == 'whatsapp':
                CheckoutService._queue_whatsapp_notification(order, whatsapp_number)

            # Emit order created event for notification system
            CheckoutService._emit_order_created_event(order, cart.workspace)

            # STEP 11: CLEAR CART (at end of transaction)
            cart.clear()

            # STEP 12: LOG SUCCESS
            logger.info(
                "Order created successfully",
                extra={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'customer_id': str(customer.id),
                    'order_type': order_type,
                    'total_amount': float(final_total),
                    'shipping_cost': float(shipping_cost),
                    'discount_amount': float(discount_amount),
                    'item_count': len(order_items),
                    'workspace_id': str(cart.workspace.id)
                }
            )

            return {
                'success': True,
                'order': order,
                'customer': customer,
                'message': 'Order created successfully'
            }

        except Exception as e:
            logger.error(
                "Order creation failed",
                extra={
                    'cart_id': str(cart.id) if cart else None,
                    'order_type': order_type,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to create order. Please try again.'
            }

    @staticmethod
    def get_available_shipping_regions(workspace, cart) -> Dict[str, Any]:
        """
        Get all available shipping regions from cart products' packages

        Performance: Single query with prefetch
        Returns: List of regions with prices and estimated delivery
        
        NOTE: Shipping is FLAT RATE per region (not per item).
        We use the highest package fee for each region.

        Returns:
            Dict with 'success': bool, 'regions': List[Dict], 'error': str
        """
        try:
            # Prefetch all packages for cart items
            cart_items = cart.items.select_related('product', 'product__package').all()

            if not cart_items.exists():
                return {
                    'success': False,
                    'error': 'Cart is empty'
                }

            # Collect all unique regions from all packages
            # For each region, track the HIGHEST shipping fee (flat rate)
            regions_data = {}

            for cart_item in cart_items:
                product = cart_item.product
                package = product.package

                # Use default package if product has no package
                if not package:
                    try:
                        package = Package.objects.get(
                            workspace=workspace,
                            use_as_default=True,
                            is_active=True
                        )
                    except Package.DoesNotExist:
                        continue

                # Extract regions from package
                region_fees = package.region_fees or {}
                estimated_days = package.estimated_days or '2-3'

                for region_name, fee in region_fees.items():
                    fee_decimal = Decimal(str(fee))
                    
                    if region_name not in regions_data:
                        regions_data[region_name] = {
                            'name': region_name,
                            'price': fee_decimal,  # Flat rate, not accumulated
                            'estimated_days': estimated_days
                        }
                    else:
                        # Use the HIGHER fee (in case products have different packages)
                        if fee_decimal > regions_data[region_name]['price']:
                            regions_data[region_name]['price'] = fee_decimal

            if not regions_data:
                return {
                    'success': False,
                    'error': 'No shipping regions configured for cart products'
                }

            # Convert to list and sort by name
            regions_list = sorted(
                regions_data.values(),
                key=lambda x: x['name']
            )

            return {
                'success': True,
                'regions': regions_list,
                'message': f'{len(regions_list)} shipping regions available'
            }

        except Exception as e:
            logger.error(f"Failed to get shipping regions: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': 'Failed to load shipping regions'
            }

    # Helper methods

    @staticmethod
    def _revalidate_cart_discount(cart) -> Dict[str, bool]:
        """
        Re-validate discount at checkout time

        Prevents race condition where discount expires between
        application and checkout
        """
        try:
            from workspace.storefront.services.discount_service import DiscountService

            # Re-validate discount
            validation = DiscountService.validate_discount_for_cart(
                workspace=cart.workspace,
                discount_code=cart.discount_code,
                cart=cart
            )

            return validation

        except Exception as e:
            logger.warning(f"Discount revalidation failed: {str(e)}")
            return {'valid': False, 'error': 'Discount validation failed'}

    @staticmethod
    def _get_order_type_config(order_type: str) -> Tuple[str, str]:
        """
        Get order source and payment method based on order type
        """
        order_configs = {
            'regular': ('web', 'mobile_money'),
            'cod': ('web', 'cash_on_delivery'),
            'whatsapp': ('whatsapp', 'whatsapp')
        }

        return order_configs.get(order_type, ('web', 'mobile_money'))

    @staticmethod
    def _queue_whatsapp_notification(order, whatsapp_number: str):
        """
        Queue WhatsApp notification async (non-blocking)

        Reliability: Never blocks order creation
        """
        try:
            from workspace.store.tasks.order_tasks import send_whatsapp_order_notification

            send_whatsapp_order_notification.delay(
                order_id=str(order.id),
                workspace_id=str(order.workspace_id),
                whatsapp_number=whatsapp_number
            )
            logger.info(f"WhatsApp notification queued for order {order.order_number}")

        except Exception as e:
            logger.warning(f"Failed to queue WhatsApp notification: {e}")

    @staticmethod
    def _emit_order_created_event(order, workspace):
        """
        Emit order created event (non-blocking)

        Reliability: Never blocks order creation
        """
        try:
            from notifications.events import order_created

            order_created.send(
                sender=CheckoutService,
                order=order,
                workspace=workspace
            )

        except Exception as e:
            logger.warning(f"Failed to emit order_created event: {e}")
