# Order Tracking Service - Customer order tracking and management
# Optimized for Cameroon market with phone-first approach

from typing import Dict, List, Optional, Any
from django.db import models
from django.core.cache import cache
from workspace.store.models.order_model import Order, OrderItem
from workspace.core.models.customer_model import Customer
import logging

logger = logging.getLogger('workspace.storefront.order_tracking')


class OrderTrackingService:
    """
    Order tracking service for customer order management

    Performance: < 100ms order tracking operations
    Scalability: Optimized order queries with caching
    Reliability: Comprehensive order status tracking
    Security: Customer-specific order access

    Cameroon Market Optimizations:
    - Phone-based order lookup
    - Mobile-friendly order tracking
    - Local delivery status updates
    - WhatsApp order notifications
    """

    # Cache configuration
    CACHE_TIMEOUT = 300  # 5 minutes
    ORDER_CACHE_PREFIX = 'customer_order_'

    @staticmethod
    def get_customer_orders(
        workspace_id: str,
        customer_identifier: str,
        identifier_type: str = 'phone',
        status_filter: Optional[str] = None,
        limit: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get customer orders by phone or email

        Cameroon Market: Phone-first order lookup
        Performance: Cached order listings
        """
        try:
            # Generate cache key
            cache_key = f"{OrderTrackingService.ORDER_CACHE_PREFIX}{workspace_id}_{customer_identifier}_{identifier_type}_{status_filter}_{limit}_{page}"

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for customer orders: {cache_key}")
                return cached_result

            # Build base queryset
            if identifier_type == 'phone':
                queryset = Order.objects.filter(
                    workspace_id=workspace_id,
                    customer_phone=customer_identifier
                )
            elif identifier_type == 'email':
                queryset = Order.objects.filter(
                    workspace_id=workspace_id,
                    customer_email=customer_identifier
                )
            else:
                return {
                    'success': False,
                    'error': 'Invalid identifier type. Use "phone" or "email"'
                }

            # Apply status filter
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # Get total count
            total_count = queryset.count()

            # Apply pagination
            offset = (page - 1) * limit
            orders = queryset.select_related('workspace').prefetch_related(
                models.Prefetch(
                    'items',
                    queryset=OrderItem.objects.select_related('product', 'variant')
                )
            ).order_by('-created_at')[offset:offset + limit]

            # Format response
            result = {
                'success': True,
                'orders': [OrderTrackingService._format_order_for_customer(order) for order in orders],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_count': total_count,
                    'total_pages': (total_count + limit - 1) // limit,
                    'has_next': offset + limit < total_count,
                    'has_previous': page > 1
                },
                'filters': {
                    'identifier_type': identifier_type,
                    'status_filter': status_filter
                }
            }

            # Cache the result
            cache.set(cache_key, result, OrderTrackingService.CACHE_TIMEOUT)

            logger.info(
                "Customer orders fetched",
                extra={
                    'workspace_id': workspace_id,
                    'customer_identifier': customer_identifier,
                    'identifier_type': identifier_type,
                    'total_orders': total_count,
                    'page': page
                }
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to fetch customer orders",
                extra={
                    'workspace_id': workspace_id,
                    'customer_identifier': customer_identifier,
                    'identifier_type': identifier_type,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load orders'
            }

    @staticmethod
    def get_order_by_number(
        workspace_id: str,
        order_number: str,
        customer_identifier: Optional[str] = None,
        identifier_type: str = 'phone'
    ) -> Dict[str, Any]:
        """
        Get specific order by order number with customer validation

        Cameroon Market: Secure order lookup with phone validation
        Security: Customer-specific order access
        """
        try:
            cache_key = f"{OrderTrackingService.ORDER_CACHE_PREFIX}detail_{workspace_id}_{order_number}"

            # Try cache first
            cached_order = cache.get(cache_key)
            if cached_order:
                return {
                    'success': True,
                    'order': cached_order
                }

            # Get order
            order = Order.objects.select_related('workspace').prefetch_related(
                models.Prefetch(
                    'items',
                    queryset=OrderItem.objects.select_related('product', 'variant')
                )
            ).get(
                workspace_id=workspace_id,
                order_number=order_number
            )

            # Validate customer access
            if customer_identifier:
                if identifier_type == 'phone':
                    if order.customer_phone != customer_identifier:
                        return {
                            'success': False,
                            'error': 'Order not found for this customer'
                        }
                elif identifier_type == 'email':
                    if order.customer_email != customer_identifier:
                        return {
                            'success': False,
                            'error': 'Order not found for this customer'
                        }

            formatted_order = OrderTrackingService._format_order_for_customer(order, include_full_details=True)

            # Cache the order
            cache.set(cache_key, formatted_order, OrderTrackingService.CACHE_TIMEOUT)

            logger.info(
                "Order details fetched",
                extra={
                    'workspace_id': workspace_id,
                    'order_number': order_number,
                    'customer_identifier': customer_identifier
                }
            )

            return {
                'success': True,
                'order': formatted_order
            }

        except Order.DoesNotExist:
            return {
                'success': False,
                'error': 'Order not found'
            }
        except Exception as e:
            logger.error(
                "Failed to fetch order details",
                extra={
                    'workspace_id': workspace_id,
                    'order_number': order_number,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load order details'
            }

    @staticmethod
    def get_order_status_timeline(
        workspace_id: str,
        order_number: str
    ) -> Dict[str, Any]:
        """
        Get order status timeline with estimated delivery

        Cameroon Market: Local delivery estimates
        Performance: Cached status timeline
        """
        try:
            cache_key = f"{OrderTrackingService.ORDER_CACHE_PREFIX}timeline_{workspace_id}_{order_number}"

            # Try cache first
            cached_timeline = cache.get(cache_key)
            if cached_timeline:
                return {
                    'success': True,
                    'timeline': cached_timeline
                }

            # Get order
            order = Order.objects.get(
                workspace_id=workspace_id,
                order_number=order_number
            )

            # Build timeline
            timeline = []

            # Order created
            timeline.append({
                'status': 'order_created',
                'title': 'Order Placed',
                'description': 'Your order has been received',
                'timestamp': order.created_at.isoformat(),
                'completed': True,
                'current': False
            })

            # Order confirmed
            if order.confirmed_at:
                timeline.append({
                    'status': 'order_confirmed',
                    'title': 'Order Confirmed',
                    'description': 'Your order has been confirmed',
                    'timestamp': order.confirmed_at.isoformat(),
                    'completed': True,
                    'current': False
                })

            # Payment status
            payment_status = 'payment_pending'
            if order.payment_status == 'paid':
                payment_status = 'payment_completed'
            elif order.payment_status == 'failed':
                payment_status = 'payment_failed'

            timeline.append({
                'status': payment_status,
                'title': 'Payment' if order.payment_status == 'pending' else 'Payment Completed',
                'description': OrderTrackingService._get_payment_description(order.payment_status),
                'timestamp': order.confirmed_at.isoformat() if order.confirmed_at else order.created_at.isoformat(),
                'completed': order.payment_status == 'paid',
                'current': order.payment_status == 'pending'
            })

            # Processing
            if order.status in ['processing', 'shipped', 'delivered']:
                timeline.append({
                    'status': 'processing',
                    'title': 'Processing',
                    'description': 'Your order is being prepared for shipment',
                    'timestamp': order.confirmed_at.isoformat() if order.confirmed_at else order.created_at.isoformat(),
                    'completed': order.status in ['shipped', 'delivered'],
                    'current': order.status == 'processing'
                })

            # Shipped
            if order.shipped_at:
                timeline.append({
                    'status': 'shipped',
                    'title': 'Shipped',
                    'description': f'Your order has been shipped. Tracking: {order.tracking_number or "Not available"}',
                    'timestamp': order.shipped_at.isoformat(),
                    'completed': order.status in ['delivered'],
                    'current': order.status == 'shipped'
                })

            # Delivered
            if order.delivered_at:
                timeline.append({
                    'status': 'delivered',
                    'title': 'Delivered',
                    'description': 'Your order has been delivered',
                    'timestamp': order.delivered_at.isoformat(),
                    'completed': True,
                    'current': False
                })

            # Add estimated delivery for Cameroon regions
            if order.status in ['processing', 'shipped']:
                estimated_delivery = OrderTrackingService._get_estimated_delivery(order)
                timeline.append({
                    'status': 'estimated_delivery',
                    'title': 'Estimated Delivery',
                    'description': estimated_delivery,
                    'timestamp': None,
                    'completed': False,
                    'current': order.status == 'shipped',
                    'estimated': True
                })

            # Cache the timeline
            cache.set(cache_key, timeline, OrderTrackingService.CACHE_TIMEOUT)

            return {
                'success': True,
                'timeline': timeline
            }

        except Order.DoesNotExist:
            return {
                'success': False,
                'error': 'Order not found'
            }
        except Exception as e:
            logger.error(
                "Failed to fetch order timeline",
                extra={
                    'workspace_id': workspace_id,
                    'order_number': order_number,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load order timeline'
            }

    @staticmethod
    def get_order_statistics(
        workspace_id: str,
        customer_identifier: str,
        identifier_type: str = 'phone'
    ) -> Dict[str, Any]:
        """Get customer order statistics"""
        try:
            cache_key = f"{OrderTrackingService.ORDER_CACHE_PREFIX}stats_{workspace_id}_{customer_identifier}_{identifier_type}"

            # Try cache first
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return {
                    'success': True,
                    'statistics': cached_stats
                }

            # Build base queryset
            if identifier_type == 'phone':
                queryset = Order.objects.filter(
                    workspace_id=workspace_id,
                    customer_phone=customer_identifier
                )
            else:
                queryset = Order.objects.filter(
                    workspace_id=workspace_id,
                    customer_email=customer_identifier
                )

            # Calculate statistics
            total_orders = queryset.count()
            total_spent = sum(order.total_amount for order in queryset.filter(payment_status='paid'))

            status_counts = queryset.values('status').annotate(
                count=models.Count('id')
            )

            recent_orders = queryset.order_by('-created_at')[:5]

            stats = {
                'total_orders': total_orders,
                'total_spent': float(total_spent) if total_spent else 0,
                'status_breakdown': {item['status']: item['count'] for item in status_counts},
                'recent_orders': [
                    {
                        'order_number': order.order_number,
                        'status': order.status,
                        'total_amount': float(order.total_amount),
                        'created_at': order.created_at.isoformat()
                    }
                    for order in recent_orders
                ]
            }

            # Cache the statistics
            cache.set(cache_key, stats, OrderTrackingService.CACHE_TIMEOUT)

            return {
                'success': True,
                'statistics': stats
            }

        except Exception as e:
            logger.error(
                "Failed to fetch order statistics",
                extra={
                    'workspace_id': workspace_id,
                    'customer_identifier': customer_identifier,
                    'identifier_type': identifier_type,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Failed to load order statistics'
            }

    # Helper methods

    @staticmethod
    def _format_order_for_customer(order: Order, include_full_details: bool = False) -> Dict[str, Any]:
        """Format order for customer response"""
        formatted_order = {
            'order_number': order.order_number,
            'status': order.status,
            'payment_status': order.payment_status,
            'subtotal': float(order.subtotal),
            'shipping_cost': float(order.shipping_cost),
            'tax_amount': float(order.tax_amount),
            'discount_amount': float(order.discount_amount),
            'total_amount': float(order.total_amount),
            'currency': order.currency,
            'item_count': order.item_count,
            'created_at': order.created_at.isoformat(),
            'confirmed_at': order.confirmed_at.isoformat() if order.confirmed_at else None,
            'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
            'tracking_number': order.tracking_number,
            'payment_method': order.payment_method,
            'order_source': order.order_source,
            'shipping_region': order.shipping_region,
            'items': [
                {
                    'product_name': item.product_name,
                    'product_sku': item.product_sku,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                    'product_id': item.product_id,
                    'variant_id': item.variant_id
                }
                for item in order.items.all()
            ]
        }

        if include_full_details:
            formatted_order.update({
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'shipping_address': order.shipping_address,
                'billing_address': order.billing_address,
                'notes': order.notes,
                'workspace_slug': order.workspace.slug if order.workspace else None,
                'tracking_url': order.get_absolute_url()
            })

        return formatted_order

    @staticmethod
    def _get_payment_description(payment_status: str) -> str:
        """Get payment status description"""
        descriptions = {
            'pending': 'Payment is pending',
            'paid': 'Payment has been completed',
            'failed': 'Payment failed',
            'refunded': 'Payment has been refunded'
        }
        return descriptions.get(payment_status, 'Payment status unknown')

    @staticmethod
    def _get_estimated_delivery(order: Order) -> str:
        """Get estimated delivery for Cameroon regions"""
        # Cameroon delivery estimates based on region
        region_estimates = {
            'littoral': '1-2 business days',
            'centre': '2-3 business days',
            'west': '3-4 business days',
            'northwest': '4-5 business days',
            'southwest': '4-5 business days',
            'adamawa': '5-6 business days',
            'east': '5-6 business days',
            'far_north': '6-7 business days',
            'north': '5-6 business days',
            'south': '4-5 business days'
        }

        estimate = region_estimates.get(order.shipping_region, '3-5 business days')

        if order.shipped_at:
            return f"Estimated delivery: {estimate}"
        else:
            return f"Estimated delivery after shipping: {estimate}"

    @staticmethod
    def clear_order_cache(workspace_id: str, order_number: str):
        """Clear order-related caches"""
        try:
            cache.delete_many([
                f"{OrderTrackingService.ORDER_CACHE_PREFIX}detail_{workspace_id}_{order_number}",
                f"{OrderTrackingService.ORDER_CACHE_PREFIX}timeline_{workspace_id}_{order_number}",
                f"{OrderTrackingService.ORDER_CACHE_PREFIX}{workspace_id}_*"
            ])
        except Exception as e:
            logger.warning(f"Failed to clear order cache: {str(e)}")


# Global instance for easy access
order_tracking_service = OrderTrackingService()