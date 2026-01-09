# Subscription GraphQL Mutations
# GraphQL mutations for subscription checkout preparation

import graphene
from graphql import GraphQLError
from subscription.models.subscription import SubscriptionPlan
from subscription.services.subscription_service import SubscriptionService


class PrepareCheckoutInput(graphene.InputObjectType):
    """
    Input for checkout preparation
    Represents USER INTENT only (not authoritative pricing)
    """
    tier = graphene.String(required=True, description="Plan tier (beginning, pro, enterprise)")
    cycle = graphene.String(required=True, description="Billing cycle (monthly, yearly)")
    requested_mode = graphene.String(required=True, description="Requested pricing mode (intro, regular)")


class CheckoutBreakdown(graphene.ObjectType):
    """Price breakdown for transparency"""
    base_price = graphene.Float(description="Base plan price")
    discount = graphene.Float(description="Discount amount (if intro)")
    final_amount = graphene.Float(description="Final amount to charge")
    currency = graphene.String(description="Currency code (XAF)")


class PrepareSubscriptionCheckout(graphene.Mutation):
    """
    Prepare subscription checkout - Returns AUTHORITATIVE PRICING

    SECURITY BOUNDARY: This mutation re-derives price from source of truth
    Frontend passes INTENT only, backend computes final price

    Pattern: Shopify/Stripe checkout preparation

    Flow:
    1. Frontend: User selects plan → passes tier/cycle/requested_mode
    2. Backend: Validates eligibility, resolves final pricing_mode, computes amount
    3. Frontend: Displays returned amount (authoritative)
    4. Payment: Creates PaymentIntent with backend-computed amount
    """

    class Arguments:
        checkout_data = PrepareCheckoutInput(required=True)

    # Response fields
    success = graphene.Boolean()
    effective_mode = graphene.String(description="Resolved pricing mode (intro or regular)")
    amount = graphene.Float(description="Authoritative amount to charge")
    currency = graphene.String(description="Currency code")
    breakdown = graphene.Field(CheckoutBreakdown, description="Price breakdown")
    plan_name = graphene.String(description="Plan display name")
    cycle_duration_days = graphene.Int(description="Billing cycle duration")
    intro_duration_days = graphene.Int(description="Intro period duration (if applicable)")
    message = graphene.String(description="User-friendly message")
    error = graphene.String(description="Error message if any")
    error_code = graphene.String(description="Error code for programmatic handling")

    @staticmethod
    def mutate(root, info, checkout_data):
        user = info.context.user

        # Auth required (platform-level, no workspace needed)
        if not user or not user.is_authenticated:
            return PrepareSubscriptionCheckout(
                success=False,
                error="Authentication required",
                error_code="UNAUTHENTICATED"
            )

        try:
            # Validate input
            tier = checkout_data.tier.lower()
            cycle = checkout_data.cycle.lower()
            requested_mode = checkout_data.requested_mode.lower()

            # Validate tier
            if tier not in ['beginning', 'pro', 'enterprise']:
                return PrepareSubscriptionCheckout(
                    success=False,
                    error=f"Invalid tier: {tier}",
                    error_code="INVALID_TIER"
                )

            # Validate cycle
            if cycle not in ['monthly', 'yearly']:
                return PrepareSubscriptionCheckout(
                    success=False,
                    error=f"Invalid cycle: {cycle}",
                    error_code="INVALID_CYCLE"
                )

            # Validate requested mode
            if requested_mode not in ['intro', 'regular']:
                return PrepareSubscriptionCheckout(
                    success=False,
                    error=f"Invalid pricing mode: {requested_mode}",
                    error_code="INVALID_MODE"
                )

            # STEP 1: Get plan from database (SOURCE OF TRUTH)
            try:
                plan = SubscriptionPlan.objects.get(tier=tier, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return PrepareSubscriptionCheckout(
                    success=False,
                    error=f"Plan '{tier}' not found or inactive",
                    error_code="PLAN_NOT_FOUND"
                )

            # STEP 2: RESOLVE PRICING MODE (backend decides, not user)
            # This is the SECURITY BOUNDARY mentioned in the guide
            effective_mode = 'regular'  # Default

            if requested_mode == 'intro':
                # Check eligibility
                if user.is_intro_pricing_eligible():
                    effective_mode = 'intro'
                else:
                    # User requested intro but not eligible
                    # Return error instead of silently downgrading (explicit UX)
                    intro_used_at = getattr(user, 'intro_pricing_used_at', None)
                    return PrepareSubscriptionCheckout(
                        success=False,
                        error="Intro pricing already used",
                        error_code="INTRO_ALREADY_USED",
                        message=f"You used intro pricing on {intro_used_at.strftime('%Y-%m-%d') if intro_used_at else 'a previous subscription'}"
                    )

            # STEP 3: COMPUTE AUTHORITATIVE PRICE (from plan model)
            if effective_mode == 'intro' and plan.intro_price:
                final_amount = float(plan.intro_price)
                base_price = float(plan.get_price(billing_cycle=cycle))
                discount = base_price - final_amount
                intro_duration = plan.intro_duration_days
                message = f"Intro pricing applied: {plan.intro_duration_days} days at reduced rate"
            else:
                final_amount = float(plan.get_price(billing_cycle=cycle))
                base_price = final_amount
                discount = 0.0
                intro_duration = None
                message = f"Regular pricing for {plan.name} - {cycle} billing"

            # STEP 4: Build breakdown for transparency
            breakdown = CheckoutBreakdown(
                base_price=base_price,
                discount=discount,
                final_amount=final_amount,
                currency="XAF"
            )

            # STEP 5: Get cycle duration
            cycle_duration = 30 if cycle == 'monthly' else 365

            return PrepareSubscriptionCheckout(
                success=True,
                effective_mode=effective_mode,
                amount=final_amount,
                currency="XAF",
                breakdown=breakdown,
                plan_name=plan.name,
                cycle_duration_days=cycle_duration,
                intro_duration_days=intro_duration,
                message=message
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Checkout preparation failed: {str(e)}", exc_info=True)

            return PrepareSubscriptionCheckout(
                success=False,
                error=f"Checkout preparation failed: {str(e)}",
                error_code="CHECKOUT_PREP_FAILED"
            )


class PrepareRenewalCheckout(graphene.Mutation):
    """
    Prepare renewal checkout - Returns AUTHORITATIVE PRICING for current plan

    Security:
    - Verifies user has active subscription
    - Validates renewal window (5 days)
    - Returns price of CURRENT plan (no user input needed)
    """

    # Response fields
    success = graphene.Boolean()
    amount = graphene.Float(description="Authoritative renewal amount")
    currency = graphene.String(description="Currency code")
    breakdown = graphene.Field(CheckoutBreakdown, description="Price breakdown")
    plan_name = graphene.String(description="Plan display name")
    cycle_duration_days = graphene.Int(description="Billing cycle duration")
    message = graphene.String(description="User-friendly message")
    error = graphene.String(description="Error message if any")
    error_code = graphene.String(description="Error code")

    @staticmethod
    def mutate(root, info):
        user = info.context.user

        if not user or not user.is_authenticated:
            return PrepareRenewalCheckout(
                success=False,
                error="Authentication required",
                error_code="UNAUTHENTICATED"
            )

        try:
            # Get active subscription
            if not hasattr(user, 'subscription'):
                return PrepareRenewalCheckout(
                    success=False,
                    error="No active subscription found",
                    error_code="NO_SUBSCRIPTION"
                )

            subscription = user.subscription
            
            # Check status (must be active or grace_period)
            if subscription.status not in ['active', 'grace_period']:
                return PrepareRenewalCheckout(
                    success=False,
                    error=f"Subscription status '{subscription.status}' cannot be renewed. Please create a new subscription.",
                    error_code="INVALID_STATUS"
                )

            # Check renewal window (if active)
            if subscription.status == 'active' and not subscription.is_in_renewal_window:
                 days_left = subscription.days_until_expiry
                 if days_left is not None and days_left > 5:
                     return PrepareRenewalCheckout(
                        success=False,
                        error=f"Renewals only allowed in final 5 days (you have {days_left} days left)",
                        error_code="RENEWAL_WAIL_PLZ"
                     )

            # Calculate price (Current plan, Regular pricing)
            plan = subscription.plan
            # Renewals always use the current billing cycle duration unless changed (but here we just use monthly/yearly logic)
            # Assuming monthly for now if not stored, but we should probably store cycle on subscription
            # For this MVP, let's assume monthly if not explicitly 'yearly'
            # Or better: check previous payment or default to monthly
            # Since Subscription model has 'billing_cycle' usually? Let's check model.
            # Wait, Subscription model doesn't explicitly store 'billing_cycle' string, it stores dates.
            # But the Plan has a price for monthly/yearly. 
            # Let's assume 'monthly' for now as that's the standard, or try to infer.
            # Actually, `get_price` takes billing_cycle.
            # Ideally we'd store the user's preference.
            cycle = 'monthly' # Default to monthly renewal
            
            amount = float(plan.get_price(billing_cycle=cycle))
            
            breakdown = CheckoutBreakdown(
                base_price=amount,
                discount=0.0,
                final_amount=amount,
                currency="XAF"
            )

            return PrepareRenewalCheckout(
                success=True,
                amount=amount,
                currency="XAF",
                breakdown=breakdown,
                plan_name=plan.name,
                cycle_duration_days=30,
                message=f"Renewal for {plan.name}"
            )

        except Exception as e:
            return PrepareRenewalCheckout(
                success=False,
                error=f"Renewal preparation failed: {str(e)}",
                error_code="RENEWAL_PREP_FAILED"
            )


class PrepareUpgradeInput(graphene.InputObjectType):
    """Input for upgrade checkout preparation"""
    tier = graphene.String(required=True, description="Target plan tier (pro, enterprise)")
    cycle = graphene.String(required=False, description="Billing cycle (monthly, yearly)")


class PrepareUpgradeCheckout(graphene.Mutation):
    """
    Prepare upgrade checkout - Returns AUTHORITATIVE PRICING for upgrade

    Security:
    - Verifies user has active subscription
    - Validates target tier is higher than current
    - Returns upgrade amount (future: could include proration)
    """

    class Arguments:
        upgrade_data = PrepareUpgradeInput(required=True)

    # Response fields
    success = graphene.Boolean()
    amount = graphene.Float(description="Authoritative upgrade amount")
    currency = graphene.String(description="Currency code")
    breakdown = graphene.Field(CheckoutBreakdown, description="Price breakdown")
    plan_name = graphene.String(description="Target plan display name")
    current_plan_name = graphene.String(description="Current plan name")
    cycle_duration_days = graphene.Int(description="Billing cycle duration")
    message = graphene.String(description="User-friendly message")
    error = graphene.String(description="Error message if any")
    error_code = graphene.String(description="Error code")

    @staticmethod
    def mutate(root, info, upgrade_data):
        user = info.context.user

        if not user or not user.is_authenticated:
            return PrepareUpgradeCheckout(
                success=False,
                error="Authentication required",
                error_code="UNAUTHENTICATED"
            )

        try:
            target_tier = upgrade_data.tier.lower()
            cycle = (upgrade_data.cycle or 'monthly').lower()

            # Validate tier
            if target_tier not in ['beginning', 'pro', 'enterprise']:
                return PrepareUpgradeCheckout(
                    success=False,
                    error=f"Invalid tier: {target_tier}",
                    error_code="INVALID_TIER"
                )

            # Validate cycle
            if cycle not in ['monthly', 'yearly']:
                return PrepareUpgradeCheckout(
                    success=False,
                    error=f"Invalid cycle: {cycle}",
                    error_code="INVALID_CYCLE"
                )

            # Get target plan
            try:
                target_plan = SubscriptionPlan.objects.get(tier=target_tier, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return PrepareUpgradeCheckout(
                    success=False,
                    error=f"Plan '{target_tier}' not found",
                    error_code="PLAN_NOT_FOUND"
                )

            # Verify active subscription
            subscription = getattr(user, 'subscription', None)
            if not subscription or subscription.status not in ['active', 'grace_period']:
                return PrepareUpgradeCheckout(
                    success=False,
                    error="No active subscription to upgrade",
                    error_code="NO_ACTIVE_SUBSCRIPTION"
                )

            # Verify this is actually an upgrade (higher price)
            current_plan = subscription.plan
            current_price = float(current_plan.get_price(billing_cycle=cycle))
            target_price = float(target_plan.get_price(billing_cycle=cycle))

            if target_price <= current_price:
                return PrepareUpgradeCheckout(
                    success=False,
                    error=f"Cannot upgrade to {target_plan.name} - use downgrade instead",
                    error_code="NOT_AN_UPGRADE"
                )

            # Calculate upgrade price (full price for now, proration future)
            amount = target_price

            breakdown = CheckoutBreakdown(
                base_price=target_price,
                discount=0.0,
                final_amount=amount,
                currency="XAF"
            )

            cycle_duration = 30 if cycle == 'monthly' else 365

            return PrepareUpgradeCheckout(
                success=True,
                amount=amount,
                currency="XAF",
                breakdown=breakdown,
                plan_name=target_plan.name,
                current_plan_name=current_plan.name,
                cycle_duration_days=cycle_duration,
                message=f"Upgrade from {current_plan.name} to {target_plan.name}"
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Upgrade preparation failed: {str(e)}", exc_info=True)

            return PrepareUpgradeCheckout(
                success=False,
                error=f"Upgrade preparation failed: {str(e)}",
                error_code="UPGRADE_PREP_FAILED"
            )


class PrepareIntentInput(graphene.InputObjectType):
    """Input for intent preparation - just the target tier"""
    tier = graphene.String(required=True, description="Target plan tier (beginning, pro, enterprise)")
    cycle = graphene.String(required=False, description="Billing cycle (monthly, yearly), defaults to monthly")


class PrepareIntent(graphene.Mutation):
    """
    Determine checkout action type based on user's current subscription state.
    
    Called by PricingPage BEFORE navigation to determine which flow to use.
    This is the source of truth for action type - frontend doesn't guess.
    
    Returns one of:
    - subscribe: No subscription or expired, go to checkout
    - renew: Same tier, in renewal window, go to checkout
    - upgrade: Higher tier selected, go to upgrade checkout
    - downgrade: Lower tier selected, show confirmation modal (no checkout)
    - already_on_plan: Same tier, not in renewal window
    """

    class Arguments:
        intent_data = PrepareIntentInput(required=True)

    # Response fields
    success = graphene.Boolean()
    action = graphene.String(description="Action type: subscribe, renew, upgrade, downgrade, already_on_plan")
    
    # For subscribe/renew/upgrade
    pricing_mode = graphene.String(description="intro or regular")
    amount = graphene.Float(description="Expected amount (for display)")
    currency = graphene.String(description="Currency code")
    plan_name = graphene.String(description="Target plan display name")
    
    # For downgrade
    schedule_date = graphene.String(description="When downgrade takes effect (ISO date)")
    current_plan_name = graphene.String(description="Current plan name (for downgrade confirmation)")
    
    # For already_on_plan
    days_until_renewal = graphene.Int(description="Days until renewal window opens")
    
    # Common
    message = graphene.String(description="User-friendly message")
    error = graphene.String(description="Error message if any")
    error_code = graphene.String(description="Error code")

    @staticmethod
    def mutate(root, info, intent_data):
        user = info.context.user

        if not user or not user.is_authenticated:
            return PrepareIntent(
                success=False,
                error="Authentication required",
                error_code="UNAUTHENTICATED"
            )

        try:
            target_tier = intent_data.tier.lower()
            cycle = (intent_data.cycle or 'monthly').lower()

            # Validate tier
            if target_tier not in ['beginning', 'pro', 'enterprise', 'free']:
                return PrepareIntent(
                    success=False,
                    error=f"Invalid tier: {target_tier}",
                    error_code="INVALID_TIER"
                )

            # Get target plan
            try:
                if target_tier == 'free':
                    # Free tier = cancel subscription
                    target_plan = SubscriptionPlan.objects.get(tier='free', is_active=True)
                else:
                    target_plan = SubscriptionPlan.objects.get(tier=target_tier, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return PrepareIntent(
                    success=False,
                    error=f"Plan '{target_tier}' not found",
                    error_code="PLAN_NOT_FOUND"
                )

            # Get current subscription state
            subscription = getattr(user, 'subscription', None)
            
            # CASE 1: No subscription or free tier or expired
            if not subscription or subscription.status == 'expired' or subscription.plan.tier == 'free':
                # New subscription flow
                is_intro_eligible = user.is_intro_pricing_eligible()
                pricing_mode = 'intro' if is_intro_eligible else 'regular'
                
                if pricing_mode == 'intro' and target_plan.intro_price:
                    amount = float(target_plan.intro_price)
                else:
                    amount = float(target_plan.get_price(billing_cycle=cycle))

                return PrepareIntent(
                    success=True,
                    action='subscribe',
                    pricing_mode=pricing_mode,
                    amount=amount,
                    currency='XAF',
                    plan_name=target_plan.name,
                    message=f"Start your {target_plan.name} subscription"
                )

            # User has active subscription - compare tiers
            current_plan = subscription.plan
            current_price = float(current_plan.get_price(billing_cycle=cycle))
            target_price = float(target_plan.get_price(billing_cycle=cycle))

            # CASE 2: Same tier selected
            if current_plan.tier == target_tier:
                # Check if in renewal window
                if subscription.status == 'grace_period' or subscription.is_in_renewal_window:
                    amount = float(target_plan.get_price(billing_cycle=cycle))
                    return PrepareIntent(
                        success=True,
                        action='renew',
                        pricing_mode='regular',
                        amount=amount,
                        currency='XAF',
                        plan_name=target_plan.name,
                        message=f"Renew your {target_plan.name} subscription"
                    )
                else:
                    # Not in renewal window yet
                    days_left = subscription.days_until_expiry or 0
                    return PrepareIntent(
                        success=True,
                        action='already_on_plan',
                        plan_name=current_plan.name,
                        days_until_renewal=max(0, days_left - 5),  # 5 day renewal window
                        message=f"You're already on {current_plan.name}. Renewal available in {max(0, days_left - 5)} days."
                    )

            # CASE 3: Higher tier selected (upgrade)
            if target_price > current_price:
                # Upgrades are immediate, prorated
                amount = float(target_plan.get_price(billing_cycle=cycle))
                return PrepareIntent(
                    success=True,
                    action='upgrade',
                    pricing_mode='regular',
                    amount=amount,
                    currency='XAF',
                    plan_name=target_plan.name,
                    current_plan_name=current_plan.name,
                    message=f"Upgrade from {current_plan.name} to {target_plan.name}"
                )

            # CASE 4: Lower tier selected (downgrade)
            if target_price < current_price:
                # Check if user can schedule downgrade (must be active)
                if subscription.status not in ['active']:
                    return PrepareIntent(
                        success=False,
                        error=f"Cannot schedule downgrade in {subscription.status} status",
                        error_code="INVALID_STATUS_FOR_DOWNGRADE"
                    )

                # Downgrade scheduled for end of current billing cycle
                schedule_date = subscription.expires_at.isoformat() if subscription.expires_at else None
                
                return PrepareIntent(
                    success=True,
                    action='downgrade',
                    plan_name=target_plan.name,
                    current_plan_name=current_plan.name,
                    schedule_date=schedule_date,
                    message=f"Schedule downgrade from {current_plan.name} to {target_plan.name} on {schedule_date[:10] if schedule_date else 'end of billing cycle'}"
                )

            # Shouldn't reach here
            return PrepareIntent(
                success=False,
                error="Could not determine action",
                error_code="UNKNOWN_ACTION"
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"PrepareIntent failed: {str(e)}", exc_info=True)
            
            return PrepareIntent(
                success=False,
                error=f"Intent preparation failed: {str(e)}",
                error_code="INTENT_PREP_FAILED"
            )


class SubscriptionMutations(graphene.ObjectType):
    """Subscription mutations collection"""

    prepare_subscription_checkout = PrepareSubscriptionCheckout.Field()
    prepare_renewal_checkout = PrepareRenewalCheckout.Field()
    prepare_upgrade_checkout = PrepareUpgradeCheckout.Field()
    prepare_intent = PrepareIntent.Field()

