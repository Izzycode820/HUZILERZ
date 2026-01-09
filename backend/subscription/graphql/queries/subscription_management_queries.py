"""
Subscription Management GraphQL Queries - AUTHENTICATED + WORKSPACE SCOPED

Manage user's subscription and billing (settings pages)
Requires authentication and workspace ownership
Matches Shopify billing page structure
"""

import graphene
from graphql import GraphQLError
from django.utils import timezone
from decimal import Decimal

from ..types.subscription_management_types import (
    SubscriptionType,
    ChargesType,
    SubscriptionHistoryType,
    BillingOverviewType,
    BillingProfileType,
)
from subscription.models import Subscription, PaymentRecord, SubscriptionHistory


class SubscriptionManagementQueries(graphene.ObjectType):
    """
    User's subscription and billing queries

    Security: All queries automatically scoped to authenticated user
    Pattern: Same as ThemeManagementQueries - user injection via middleware
    """

    # Billing Page - Main overview
    billing_overview = graphene.Field(
        BillingOverviewType,
        description="Get billing overview for main billing page (upcoming bill + past bills)"
    )

    # Charges Page - Charges table
    charges = graphene.List(
        ChargesType,
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        charge_type=graphene.String(description="Filter by charge type"),
        date_from=graphene.DateTime(description="Filter from date"),
        date_to=graphene.DateTime(description="Filter to date"),
        search=graphene.String(description="Search by bill number"),
        description="Get charges for charges table page"
    )

    # Past Bills - Subscription history with filters
    past_bills = graphene.List(
        SubscriptionHistoryType,
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        status=graphene.String(description="Filter by status (all, paid, unpaid)"),
        sort_order=graphene.String(description="Sort by date (newest_first, oldest_first)"),
        search=graphene.String(description="Search by bill number"),
        description="Get past bills with filters and sorting"
    )

    # Billing Profile Page - Payment methods + user info
    billing_profile = graphene.Field(
        BillingProfileType,
        description="Get billing profile (payment methods, currency, address)"
    )

    # Current Plan Page - Active plan details
    current_plan = graphene.Field(
        SubscriptionType,
        description="Get user's current subscription/plan"
    )

    def resolve_billing_overview(self, info):
        """
        Resolve billing overview for main billing page
        Matches Shopify billing page structure - upcoming bill section only

        Returns:
        - Upcoming bill amount and date
        - Last payment method and phone number
        """
        user = info.context.user

        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            return BillingOverviewType(
                upcoming_bill_amount=0.0,
                next_bill_date=None,
                days_until_bill=None,
                last_payment_method=None,
                last_payment_phone_number=None
            )

        # Calculate upcoming bill
        upcoming_bill_amount = 0.0
        next_bill_date = None
        days_until_bill = None

        if subscription.status == 'active' and subscription.plan.tier != 'free':
            # CRITICAL: Calculate NEXT billing amount based on intro_cycles_remaining
            # If intro cycles remain after next payment, use intro price
            # Otherwise, use regular price
            if subscription.intro_cycles_remaining > 1:
                # More than 1 cycle left - next bill will still be intro
                next_billing_phase = 'intro'
                price = subscription.plan.intro_price
            elif subscription.intro_cycles_remaining == 1:
                # Last intro cycle - next bill will be regular
                next_billing_phase = 'regular'
                price = subscription.plan.get_price(
                    billing_cycle=subscription.billing_cycle,
                    billing_phase='regular'
                )
            else:
                # Already in regular phase - next bill stays regular
                next_billing_phase = 'regular'
                price = subscription.plan.get_price(
                    billing_cycle=subscription.billing_cycle,
                    billing_phase='regular'
                )

            upcoming_bill_amount = float(price)
            next_bill_date = subscription.expires_at
            if next_bill_date:
                days_until_bill = subscription.days_until_expiry

        # Get last payment method and phone
        last_payment = PaymentRecord.objects.filter(
            user=user,
            status='success'
        ).order_by('-created_at').first()

        last_payment_method = None
        last_payment_phone_number = None
        if last_payment:
            last_payment_method = last_payment.momo_operator
            last_payment_phone_number = last_payment.momo_phone_used

        return BillingOverviewType(
            upcoming_bill_amount=upcoming_bill_amount,
            next_bill_date=next_bill_date,
            days_until_bill=days_until_bill,
            last_payment_method=last_payment_method,
            last_payment_phone_number=last_payment_phone_number
        )

    def resolve_charges(self, info, limit=50, offset=0, charge_type=None,
                        date_from=None, date_to=None, search=None):
        """
        Resolve charges for charges table
        Matches Shopify billing-charging table page

        Fields: bill number (reference), date, charge type, amount
        Filters: date, bill number, charge type
        """
        user = info.context.user

        # Base query
        queryset = PaymentRecord.objects.filter(user=user)

        # Apply filters
        if charge_type:
            queryset = queryset.filter(charge_type=charge_type)

        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        if search:
            queryset = queryset.filter(reference__icontains=search)

        # Order and paginate
        payment_records = queryset.order_by('-created_at')[offset:offset + limit]

        return list(payment_records)

    def resolve_past_bills(self, info, limit=50, offset=0, status=None,
                           sort_order='newest_first', search=None):
        """
        Resolve past bills with filters and sorting
        Matches Shopify billing page past bills section with filters

        Returns: Paginated and filtered subscription history records
        """
        user = info.context.user

        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            return []

        # Base query
        queryset = SubscriptionHistory.objects.filter(subscription=subscription)

        # Apply status filter
        if status and status != 'all':
            queryset = queryset.filter(status=status)

        # Apply search
        if search:
            queryset = queryset.filter(bill_number__icontains=search)

        # Apply sorting
        if sort_order == 'oldest_first':
            queryset = queryset.order_by('created_at')
        else:  # newest_first (default)
            queryset = queryset.order_by('-created_at')

        # Paginate
        bills = queryset[offset:offset + limit]

        return list(bills)

    def resolve_billing_profile(self, info):
        """
        Resolve billing profile for billing profile page
        Matches Shopify billing-profile page

        Returns:
        - Primary payment method (most recent)
        - Payment number (phone)
        """
        user = info.context.user

        # Get most recent payment method
        latest_payment = PaymentRecord.objects.filter(
            user=user,
            status='success'
        ).order_by('-created_at').first()

        primary_payment_method = None
        if latest_payment and latest_payment.momo_operator:
            primary_payment_method = latest_payment.momo_operator

        return BillingProfileType(
            primary_payment_method=primary_payment_method,
            user_phone=getattr(user, 'phone_number', None)
        )

    def resolve_current_plan(self, info):
        """
        Resolve user's current subscription/plan
        For current plan page in settings

        Security: Returns user's own subscription only
        Returns: Full subscription details with plan info
        """
        user = info.context.user

        try:
            subscription = Subscription.objects.select_related('plan', 'pending_plan_change').get(
                user=user
            )
            return subscription

        except Subscription.DoesNotExist:
            # User has no subscription - should not happen (free plan auto-assigned)
            raise GraphQLError("No subscription found. Please contact support.")
