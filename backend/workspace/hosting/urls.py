"""
Domain Management URLs - GraphQL Endpoint

All domain operations are handled through GraphQL.

Full endpoint: /api/workspaces/hosting/graphql/

Queries (all require auth + workspace):
- workspaceDomains: Get all domains for workspace (purchased + connected)
- customDomain: Get single domain by ID (for polling verification status)
- workspaceInfrastructure: Get workspace subdomain and URLs
- domainPurchaseStatus: Track purchase progress
- domainRenewalStatus: Track renewal progress
- subdomainSuggestions: Get subdomain suggestions
- validateSubdomain: Check subdomain availability

Mutations (all require auth + workspace):
- searchDomain: Check domain availability + pricing
- purchaseDomain: Initiate domain purchase (mobile money flow)
- renewDomain: Initiate domain renewal (mobile money flow)
- changeSubdomain: Change workspace subdomain
- connectCustomDomain: Connect externally-owned domain (Shopify 2-step flow)
- verifyCustomDomain: Manually trigger domain verification

Cameroon Market Features:
- Mobile money payment integration (MTN, Orange, Fapshi, Flutterwave)
- Manual renewals (no auto-renewal)
- Dual currency pricing (USD/FCFA)
- Progressive expiry warnings (30, 15, 7, 3, 1 days)
"""

from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from .graphql.schema import schema
from .graphql.middleware.auth import DomainAuthMiddleware
from . import views

app_name = 'hosting'

urlpatterns = [
    # GraphQL endpoint for all domain operations
    # All operations require authentication (no public queries)
    path('graphql/', csrf_exempt(GraphQLView.as_view(
        graphiql=True,
        schema=schema,
        middleware=[DomainAuthMiddleware()]
    )), name='domain-graphql'),

    # Internal health check endpoint (token-protected)
    # Requires X-Internal-Token header
    path('internal/health/', views.internal_health_check, name='internal-health-check'),

    # Public health check endpoint (for load balancers)
    # No authentication required
    path('health/', views.simple_health_check, name='simple-health-check'),

    # Storefront password unlock endpoint (Concern #2)
    # Handles password form submission from password-protected storefronts
    # No authentication required (public endpoint for storefront visitors)
    path('storefront/unlock/', views.unlock_storefront, name='storefront-unlock'),
]
