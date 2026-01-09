"""
Subscription Plan Showcase GraphQL Queries - PUBLIC ACCESS

Browse subscription plans without authentication
Users can view plans before signing up (SaaS pricing page pattern)
"""

import graphene
from graphql import GraphQLError

from ..types.plan_showcase_types import PlanType
from subscription.models import SubscriptionPlan


class PlanShowcaseQueries(graphene.ObjectType):
    """
    Public subscription plan queries

    Security: No authentication required (public pricing page)
    Performance: Cached capabilities from YAML via CapabilityEngine
    Pattern: Matches ThemeShowcaseQueries approach
    """

    plans = graphene.List(
        PlanType,
        description="Browse all available subscription plans (PUBLIC)"
    )

    plan_details = graphene.Field(
        PlanType,
        tier=graphene.String(required=True),
        description="Get detailed plan information by tier (PUBLIC)"
    )

    is_intro_pricing_eligible = graphene.Boolean(
        description="Check if current user is eligible for intro pricing (returns null if not authenticated)"
    )

    def resolve_plans(self, info):
        """
        Resolve all active subscription plans for public browsing

        Flow:
        1. Query SubscriptionPlan table (minimal: id, name, tier, regular_price_monthly)
        2. GraphQL type calls plan.get_capabilities() for each plan
        3. get_capabilities() → CapabilityEngine → YAML (cached)
        4. Returns complete plan data (metadata + features)

        Security: Only shows active plans
        Performance: YAML loaded once and cached (1hr)
        """
        # Get all active plans, ordered by regular monthly price
        queryset = SubscriptionPlan.objects.filter(
            is_active=True
        ).order_by('regular_price_monthly')

        return list(queryset)

    def resolve_plan_details(self, info, tier):
        """
        Resolve detailed plan by tier

        Flow: Same as resolve_plans but for single plan
        Usage: Plan comparison page, plan details modal

        Security: Only shows active plans
        """
        try:
            plan = SubscriptionPlan.objects.get(
                tier=tier,
                is_active=True
            )
            return plan

        except SubscriptionPlan.DoesNotExist:
            raise GraphQLError(f"Plan with tier '{tier}' not found or inactive")

    def resolve_is_intro_pricing_eligible(self, info):
        """
        Resolve intro pricing eligibility for current user

        Returns:
        - True: User is authenticated AND eligible for intro pricing
        - False: User is authenticated BUT has already used intro pricing
        - None: User is not authenticated (public visitor)

        Frontend Logic (per error.md):
        if (!isAuthenticated) {
            showIntroPricing()  // Public visitors see intro pricing
        } else if (isIntroPricingEligible) {
            showIntroPricing()  // Authenticated + eligible = show intro
        } else {
            showRegularPricing()  // Authenticated + not eligible = show regular
        }

        Security: Safe to expose - only returns boolean, no sensitive data
        """
        user = info.context.user

        # Not authenticated - return None (public visitor)
        if not user or not user.is_authenticated:
            return None

        # Authenticated - return eligibility status
        return user.is_intro_pricing_eligible()
