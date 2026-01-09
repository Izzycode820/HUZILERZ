"""
Subscription GraphQL Schema

Combines public plan browsing and authenticated subscription management
Routes:
- PUBLIC: Browse plans, trial pricing (no auth required)
- AUTHENTICATED: Billing overview, payment records, profile (requires JWT + workspace)
- MUTATIONS: Checkout preparation (requires auth, no workspace)
"""

import graphene
from .queries.plan_showcase_queries import PlanShowcaseQueries
from .queries.subscription_management_queries import SubscriptionManagementQueries
from .mutations.subscription_mutations import SubscriptionMutations


class Query(
    PlanShowcaseQueries,
    SubscriptionManagementQueries,
    graphene.ObjectType
):
    """
    Combined subscription queries

    Public queries (no auth):
    - plans: Browse available subscription plans
    - planDetails: View single plan details
    - trialPricing: Get trial pricing info

    Authenticated queries (requires workspace):
    - billingOverview: Billing page data (upcoming bill + past bills)
    - paymentRecords: Charges table (payment history)
    - billingProfile: Billing profile page (payment methods + user info)
    - currentPlan: Current subscription/plan details
    - myTrial: Trial status (eligibility check)
    """
    pass


class Mutation(
    SubscriptionMutations,
    graphene.ObjectType
):
    """
    Subscription mutations

    Platform-level mutations (auth required, no workspace):
    - prepareSubscriptionCheckout: Get authoritative pricing for checkout
    """
    pass


# Schema instance (queries + mutations)
schema = graphene.Schema(query=Query, mutation=Mutation)
