"""
GraphQL types for checkout operations
Follows codebase patterns for consistency
"""

import graphene


class ShippingRegionType(graphene.ObjectType):
    """
    Shipping region with pricing information

    Used by frontend to display shipping options dropdown
    Each region shows total shipping cost and estimated delivery
    """
    name = graphene.String(description="Region name (e.g., 'buea', 'yaounde')")
    price = graphene.Decimal(description="Total shipping cost for this region in XAF")
    estimated_days = graphene.String(description="Estimated delivery time (e.g., '2-3', '3-5 days')")


class AvailableShippingRegions(graphene.ObjectType):
    """
    Available shipping regions query result

    Returns list of regions with calculated shipping costs
    for current cart products
    """
    success = graphene.Boolean()
    regions = graphene.List(ShippingRegionType)
    message = graphene.String()
    error = graphene.String()


class OrderTrackingType(graphene.ObjectType):
    """
    Order tracking information for customers

    Security: Limited fields exposed for public tracking
    """
    order_number = graphene.String()
    status = graphene.String()
    total_amount = graphene.Decimal()
    created_at = graphene.DateTime()
    tracking_number = graphene.String()
    estimated_delivery_days = graphene.String()


class CreateOrderResult(graphene.ObjectType):
    """
    Standard result type for order creation mutations

    Returns order ID and relevant metadata for frontend redirect
    """
    success = graphene.Boolean()
    order_id = graphene.ID()
    order_number = graphene.String()
    message = graphene.String()
    error = graphene.String()


class WhatsAppOrderResult(graphene.ObjectType):
    """
    WhatsApp order creation result

    Includes WhatsApp link for customer communication
    """
    success = graphene.Boolean()
    order_id = graphene.ID()
    order_number = graphene.String()
    whatsapp_link = graphene.String()
    message = graphene.String()
    error = graphene.String()


class PaymentOrderResult(graphene.ObjectType):
    """
    Payment order creation result

    Includes payment URL for redirect (Fapshi, etc)
    """
    success = graphene.Boolean()
    order_id = graphene.ID()
    order_number = graphene.String()
    payment_url = graphene.String()
    message = graphene.String()
    error = graphene.String()
