"""
Hosting Management GraphQL Schema

Domain management and resource usage tracking
Routes: ALL AUTHENTICATED (no public endpoints)
"""

import graphene
from .queries.domain_queries import DomainManagementQueries
from .queries.usage_queries import UsageQueries
from .queries.storefront_settings_queries import StorefrontSettingsQueries
from .mutations.domain_mutations import DomainManagementMutations
from .mutations.storefront_password_mutation import SetStorefrontPassword
from .mutations.seo_mutations import SEOMutations


class Query(
    DomainManagementQueries,
    UsageQueries,
    StorefrontSettingsQueries,
    graphene.ObjectType
):
    """
    Hosting management queries (all require authentication)

    Domain Management (Clean - matches UI flows):
    - domains: Get all domains for workspace (default + custom)
    - validateSubdomain: Check subdomain availability (for change modal)
    - customDomain: Get domain detail with DNS/TLS status (for polling)
    - searchDomains: Search domains with pagination (for buy flow)
    - purchaseStatus: Track purchase progress
    - renewalStatus: Track renewal progress

    Storefront Settings:
    - storefrontSettings: Get preview data (password, title, domain) for UI forms

    Resource Usage:
    - myHostingEnvironment: Get resource quotas and limits
    - myUsageSummary: Get current usage with percentages
    - myUsageHistory: Get usage history for charts (30 days)
    - myOverageCost: Calculate overage costs for billing
    - myUsageLogs: Get detailed usage logs
    - checkUploadEligibility: Pre-flight check for file uploads
    - checkDeploymentEligibility: Pre-flight check for deployments
    """
    pass


class Mutation(
    DomainManagementMutations,
    SEOMutations,
    graphene.ObjectType
):
    """
    Hosting management mutations (all require authentication + workspace)

    Domain Management:
    - changeSubdomain: Change workspace subdomain
    - connectCustomDomain: Connect externally-owned domain
    - verifyCustomDomain: Manually trigger domain verification
    - purchaseDomain: Initiate domain purchase (mobile money flow)
    - renewDomain: Initiate domain renewal (mobile money flow)

    Storefront Management (Concern #2):
    - setStorefrontPassword: Enable/disable/change storefront password protection

    SEO Management (Phase 4):
    - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
    """
    set_storefront_password = SetStorefrontPassword.Field()


# Schema instance
schema = graphene.Schema(query=Query, mutation=Mutation)
