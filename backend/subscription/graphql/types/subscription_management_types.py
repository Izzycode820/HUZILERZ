"""
Subscription Management GraphQL Types - AUTHENTICATED ACCESS

Types for user's subscription management (billing page, charges, profile)
Requires authentication and workspace ownership
"""

import graphene
from graphene_django import DjangoObjectType
from subscription.models import (
    Subscription,
    SubscriptionPlan,
    PaymentRecord,
    SubscriptionHistory
)


class SubscriptionPlanType(DjangoObjectType):
    """
    Plan type for authenticated subscription context
    """
    id = graphene.ID(required=True)
    is_free = graphene.Boolean()
    is_paid = graphene.Boolean()

    # Pricing fields
    intro_price = graphene.Float()
    intro_duration_days = graphene.Int()
    regular_price_monthly = graphene.Float()
    regular_price_yearly = graphene.Float()

    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'tier', 'description', 'intro_price', 'intro_duration_days', 'regular_price_monthly', 'regular_price_yearly')

    def resolve_id(self, info):
        return str(self.id)

    def resolve_is_free(self, info):
        return self.tier == 'free'

    def resolve_is_paid(self, info):
        return self.tier != 'free'

    def resolve_intro_price(self, info):
        return float(self.intro_price) if self.intro_price else 0.0

    def resolve_intro_duration_days(self, info):
        return self.intro_duration_days

    def resolve_regular_price_monthly(self, info):
        return float(self.regular_price_monthly) if self.regular_price_monthly else 0.0

    def resolve_regular_price_yearly(self, info):
        return float(self.regular_price_yearly) if self.regular_price_yearly else 0.0


class SubscriptionType(DjangoObjectType):
    """
    User's subscription type for current plan page
    """
    plan = graphene.Field(SubscriptionPlanType)

    # Intro pricing state
    is_on_intro_pricing = graphene.Boolean()
    intro_ends_at = graphene.DateTime()
    billing_cycle = graphene.String()

    class Meta:
        model = Subscription
        fields = ('id', 'plan', 'status', 'expires_at', 'billing_cycle')

    def resolve_plan(self, info):
        return self.plan

    def resolve_is_on_intro_pricing(self, info):
        """Check if user is currently on intro pricing"""
        return self.billing_phase == 'intro' and self.intro_cycles_remaining > 0

    def resolve_intro_ends_at(self, info):
        """Return when intro period ends (current_cycle_ends_at if on intro)"""
        if self.billing_phase == 'intro' and self.intro_cycles_remaining > 0:
            return self.current_cycle_ends_at
        return None

    def resolve_billing_cycle(self, info):
        return self.billing_cycle


class ChargesType(DjangoObjectType):
    """
    Charges table type
    Matches Shopify billing-charging table page
    Fields: bill number (reference), date, charge type, amount
    """
    class Meta:
        model = PaymentRecord
        fields = ('reference', 'created_at', 'charge_type', 'amount')


class SubscriptionHistoryType(DjangoObjectType):
    """
    Subscription history type for past bills
    Matches Shopify billing page past bills section
    """
    class Meta:
        model = SubscriptionHistory
        fields = (
            'bill_number', 'created_at', 'action',
            'amount_paid', 'status'
        )


class BillingOverviewType(graphene.ObjectType):
    """
    Billing overview type for billing page
    Matches Shopify billing page structure - upcoming bill section only
    """
    # Upcoming bill section
    upcoming_bill_amount = graphene.Float()
    next_bill_date = graphene.DateTime()
    days_until_bill = graphene.Int()
    last_payment_method = graphene.String()  # MTN, Orange, Fapshi
    last_payment_phone_number = graphene.String()


class BillingProfileType(graphene.ObjectType):
    """
    Billing profile type for billing profile page
    Matches Shopify billing-profile page
    Fields: primary payment method, payment number
    """
    primary_payment_method = graphene.String()
    user_phone = graphene.String()
