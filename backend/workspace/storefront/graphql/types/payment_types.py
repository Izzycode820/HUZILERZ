"""
GraphQL types for payment methods (public storefront)
Exposes enabled payment methods to customers for checkout

Only exposes public info needed for checkout:
- Provider name and display name
- Checkout URL for redirect (Fapshi)
"""

import graphene


class AvailablePaymentMethodType(graphene.ObjectType):
    """
    Public payment method info for storefront checkout

    Security: Only exposes public info (no credentials)
    Usage: Payment method selector in checkout
    """
    provider = graphene.String(
        required=True,
        description="Provider identifier (e.g., 'fapshi')"
    )
    display_name = graphene.String(
        required=True,
        description="Human-readable name (e.g., 'Mobile Money (MTN/Orange)')"
    )
    checkout_url = graphene.String(
        description="Merchant's checkout URL for redirect (Fapshi)"
    )
    description = graphene.String(
        description="Brief description of payment method"
    )
