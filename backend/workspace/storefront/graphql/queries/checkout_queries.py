"""
GraphQL queries for checkout operations
Comprehensive queries following codebase patterns
"""

import graphene
import logging

from workspace.storefront.models import GuestSession
from workspace.storefront.services.checkout_service import CheckoutService
from workspace.storefront.graphql.types.checkout_types import (
    AvailableShippingRegions,
    ShippingRegionType,
    OrderTrackingType
)

logger = logging.getLogger(__name__)


class CheckoutQueries(graphene.ObjectType):
    """
    Comprehensive checkout queries for storefront

    All operations needed for checkout flow
    Domain-based workspace identification
    """

    available_shipping_regions = graphene.Field(
        AvailableShippingRegions,
        session_id=graphene.String(required=True),
        description="Get available shipping regions with prices for current cart"
    )

    track_order = graphene.Field(
        OrderTrackingType,
        order_number=graphene.String(required=True),
        description="Track order by order number"
    )

    def resolve_available_shipping_regions(self, info, session_id):
        """
        Get available shipping regions for cart

        Performance: Optimized query with prefetch
        Security: Workspace scoping via middleware
        Reliability: Returns None on error, logs warning
        """
        try:
            workspace = info.context.workspace

            # Get session and cart
            session = GuestSession.objects.select_related('cart').get(
                session_id=session_id,
                workspace=workspace
            )

            if session.is_expired:
                return AvailableShippingRegions(
                    success=False,
                    regions=None,
                    error="Session expired. Please refresh your cart."
                )

            cart = session.cart

            # Get available regions using service
            result = CheckoutService.get_available_shipping_regions(
                workspace=workspace,
                cart=cart
            )

            if not result['success']:
                return AvailableShippingRegions(
                    success=False,
                    regions=None,
                    error=result.get('error', 'Failed to load shipping regions')
                )

            # Convert regions to GraphQL types
            regions = [
                ShippingRegionType(
                    name=region['name'],
                    price=region['price'],
                    estimated_days=region['estimated_days']
                )
                for region in result['regions']
            ]

            return AvailableShippingRegions(
                success=True,
                regions=regions,
                message=result.get('message')
            )

        except GuestSession.DoesNotExist:
            logger.warning(f"Session not found: {session_id}")
            return AvailableShippingRegions(
                success=False,
                regions=None,
                error="Session not found"
            )
        except Exception as e:
            logger.error(
                f"Failed to get shipping regions: {str(e)}",
                exc_info=True
            )
            return AvailableShippingRegions(
                success=False,
                regions=None,
                error="Failed to load shipping regions"
            )

    def resolve_track_order(self, info, order_number):
        """
        Track order by order number

        Security: Public endpoint with limited fields exposed
        """
        try:
            from workspace.store.models import Order
            workspace = info.context.workspace

            order = Order.objects.get(
                order_number=order_number,
                workspace=workspace
            )

            return OrderTrackingType(
                order_number=order.order_number,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
                tracking_number=order.tracking_number if hasattr(order, 'tracking_number') else None,
                estimated_delivery_days=order.estimated_delivery_days if hasattr(order, 'estimated_delivery_days') else None
            )

        except Order.DoesNotExist:
            logger.warning(f"Order not found: {order_number}")
            return None
        except Exception as e:
            logger.error(f"Order tracking failed: {str(e)}", exc_info=True)
            return None
