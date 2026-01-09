"""
Domain Management GraphQL Input Types - For Mutations

Input types used by domain management mutations
Follows Shopify/Stripe pattern for input validation
"""

import graphene


class PurchaseDomainInput(graphene.InputObjectType):
    """
    Input for purchasing a domain

    Used by purchaseDomain mutation
    Requires contact info for WHOIS registration (ICANN requirement)
    """
    workspace_id = graphene.ID(required=True, description="Workspace to associate domain with")
    domain = graphene.String(required=True, description="Domain to purchase")
    registration_period_years = graphene.Int(default_value=1, description="Registration period (1-10 years)")

    # Contact information for WHOIS (registrar requirement)
    phone = graphene.String(required=True, description="Phone number (e.g., '+237670000000')")
    address = graphene.String(required=True, description="Street address")
    city = graphene.String(required=True, description="City")
    state = graphene.String(required=True, description="State/Region")
    postal_code = graphene.String(required=True, description="Postal/ZIP code")
    country = graphene.String(default_value='CM', description="Country code (ISO 2-letter, default: CM for Cameroon)")


class RenewDomainInput(graphene.InputObjectType):
    """
    Input for renewing a domain

    Used by renewDomain mutation
    """
    domain_id = graphene.ID(required=True, description="CustomDomain ID to renew")
    renewal_period_years = graphene.Int(default_value=1, description="Renewal period (1-10 years)")


class ChangeSubdomainInput(graphene.InputObjectType):
    """
    Input for changing workspace subdomain

    Used by changeSubdomain mutation
    """
    workspace_id = graphene.ID(required=True, description="Workspace to update")
    subdomain = graphene.String(required=True, description="New subdomain (e.g., 'mystore' for mystore.huzilerz.com)")


class ConnectCustomDomainInput(graphene.InputObjectType):
    """
    Input for connecting an externally-owned custom domain

    Used by connectCustomDomain mutation
    """
    workspace_id = graphene.ID(required=True, description="Workspace to connect domain to")
    domain = graphene.String(required=True, description="Domain to connect (must be owned externally)")


class SuggestSubdomainsInput(graphene.InputObjectType):
    """
    Input for getting subdomain suggestions

    Used by suggestSubdomains query
    """
    base_name = graphene.String(required=True, description="Base name for suggestions (e.g., 'mystore')")
    limit = graphene.Int(default_value=5, description="Number of suggestions to return")
