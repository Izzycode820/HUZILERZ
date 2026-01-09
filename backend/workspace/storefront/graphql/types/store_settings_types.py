"""
GraphQL types for store settings (public storefront)
Follows codebase patterns for consistency

Exposes only public store information needed by storefront:
- Store name and description
- Contact info (WhatsApp, phone, email)
- Currency (for formatting)
"""

import graphene


class StoreSettingsType(graphene.ObjectType):
    """
    Public store settings for storefront display

    Security: Only exposes customer-facing settings
    Usage: Header, footer, checkout, contact pages
    """
    store_name = graphene.String(description="Display name of the store")
    store_description = graphene.String(description="Store tagline or description")
    
    # Contact information
    whatsapp_number = graphene.String(description="WhatsApp number for orders (e.g., 237699999999)")
    phone_number = graphene.String(description="Store phone number")
    support_email = graphene.String(description="Customer support email")
    
    # Display settings
    currency = graphene.String(description="Store currency code (e.g., XAF)")
