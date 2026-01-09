"""
Subscription Service - Production-Ready Webhook-Driven Architecture
Core business logic for manual renewal subscription system (Cameroon context)
Event-driven, decoupled, secure, and scalable
"""
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
import logging

from ..models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionHistory,
    SubscriptionEventLog,
    PaymentRecord
)
from ..events import (
    subscription_upgrade_initiated,
    subscription_activated,
    subscription_renewed,
    subscription_expired,
    subscription_downgraded,
    subscription_cancelled,
    subscription_suspended,
    subscription_reactivated,
    grace_period_started,
    grace_period_ended,
    plan_change_scheduled,
    plan_change_applied,
)

logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    Manual renewal subscription workflow for Cameroon market
    No auto-billing - all renewals require user action
    """
    
    @staticmethod
    def initiate_subscription(user, plan_tier, phone_number, pricing_mode, workspace=None, preferred_provider='fapshi',
                             billing_cycle='monthly', idempotency_key=None, client_context=None):
        """
        Initiate subscription creation (webhook-driven pattern)
        Returns PaymentIntent for user to complete payment via USSD

        CRITICAL: User explicitly chooses pricing mode (NO auto-detection)

        Args:
            pricing_mode: 'intro' or 'regular' (REQUIRED, explicit user choice)
            billing_cycle: 'monthly' or 'yearly'
            idempotency_key: Optional UUID for preventing duplicate requests (auto-generated if missing)
            client_context: Optional dict with ip, user_agent, locale for fraud detection

        Raises:
            ValidationError: If intro requested but user ineligible (hard error, no silent downgrade)
        """
        # Auto-generate idempotency key if not provided (dev convenience)
        if not idempotency_key:
            import uuid as uuid_lib
            idempotency_key = str(uuid_lib.uuid4())

        # Check for existing PaymentIntent with this idempotency key
        from payments.models import PaymentIntent
        existing_intent = PaymentIntent.objects.filter(idempotency_key=idempotency_key).first()
        if existing_intent:
            logger.info(f"Idempotency key {idempotency_key} already processed - returning existing PaymentIntent")
            return {
                'success': True,
                'already_processed': True,
                'payment_intent_id': str(existing_intent.id),
                'subscription_id': existing_intent.metadata.get('subscription_id'),
                'amount': float(existing_intent.amount),
            }
        try:
            plan = SubscriptionPlan.objects.get(tier=plan_tier, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise ValidationError(f"Plan '{plan_tier}' not found")

        # Free plan doesn't require payment
        if plan.tier == 'free':
            raise ValidationError("Free plan is auto-assigned at registration. Use upgrade for paid plans.")

        # VALIDATION: Check existing subscription
        if hasattr(user, 'subscription'):
            existing_subscription = user.subscription

            # Pending payment with existing PaymentIntent
            if existing_subscription.status == 'pending_payment' and existing_subscription.payment_intent:
                payment_intent = existing_subscription.payment_intent

                # Check if PaymentIntent expired (30-minute security timeout)
                if payment_intent.is_expired:
                    # Check subscription age for 23-hour grace period
                    subscription_age = timezone.now() - existing_subscription.created_at
                    if subscription_age > timedelta(hours=23):
                        # Expired - allow new subscription
                        existing_subscription.status = 'expired'
                        existing_subscription.save()
                        logger.info(f"Subscription {existing_subscription.id} expired (23hr grace period)")
                    else:
                        # Within grace - require retry
                        time_remaining = timedelta(hours=23) - subscription_age
                        hrs_remaining = time_remaining.total_seconds() / 3600
                        raise ValidationError({
                            'error': f"Payment expired. Retry payment for {existing_subscription.plan.name} or cancel.",
                            'error_code': 'PAYMENT_EXPIRED_RETRY_AVAILABLE',
                            'subscription_id': str(existing_subscription.id),
                            'grace_period_remaining_hours': round(hrs_remaining, 1),
                        })
                else:
                    # Payment session still active - return existing PaymentIntent
                    raise ValidationError({
                        'error': f"Pending payment exists for {existing_subscription.plan.name}. Complete or cancel first.",
                        'error_code': 'PENDING_PAYMENT',
                        'payment_intent_id': str(payment_intent.id),
                        'expires_at': payment_intent.expires_at.isoformat() if payment_intent.expires_at else None,
                    })

            # Active subscription - use upgrade flow
            elif existing_subscription.status == 'active':
                if existing_subscription.plan.tier != 'free':
                    raise ValidationError(f"Active {existing_subscription.plan.name} subscription exists. Use upgrade endpoint.")

                if plan_tier == 'free':
                    raise ValidationError("You already have a free subscription.")

            # REUSE failed/expired/cancelled subscriptions (DON'T DELETE - preserves HostingEnvironment)
            # Subscriptions are OneToOne with user - just reset the existing record
            elif existing_subscription.status in ['failed', 'expired', 'cancelled', 'suspended']:
                logger.info(f"Reusing {existing_subscription.status} subscription {existing_subscription.id} for new plan attempt")
                # Don't delete - will update this record below (lines 143-151 or 156-168)

        # STEP 1: Validate pricing_mode parameter (explicit user choice)
        if pricing_mode not in ['intro', 'regular']:
            raise ValidationError({
                'error': 'Invalid pricing_mode. Must be "intro" or "regular"',
                'error_code': 'INVALID_PRICING_MODE',
                'provided': pricing_mode
            })

        # STEP 2: If user chose intro, validate eligibility (HARD ERROR if invalid)
        if pricing_mode == 'intro':
            if not user.is_intro_pricing_eligible():
                raise ValidationError({
                    'error': 'Intro pricing already used',
                    'error_code': 'INTRO_ALREADY_USED',
                    'used_at': user.intro_pricing_used_at.isoformat() if user.intro_pricing_used_at else None,
                    'tier_used': user.intro_tier_used,
                    'message': 'Intro pricing is a one-time offer. Please select regular pricing.'
                })

            # User chose intro AND is eligible
            billing_phase = 'intro'
            intro_cycles_remaining = 1
            amount_to_charge = plan.intro_price
            cycle_duration_days = plan.intro_duration_days
            logger.info(f"User {user.email} chose intro pricing for {plan_tier}")

        else:  # pricing_mode == 'regular'
            billing_phase = 'regular'
            intro_cycles_remaining = 0
            amount_to_charge = plan.get_price(billing_cycle, 'regular')
            cycle_duration_days = 365 if billing_cycle == 'yearly' else 30

        with transaction.atomic():
            # REUSE existing subscription (OneToOne - user can only have one)
            # Three scenarios:
            # 1. Free → Paid upgrade
            # 2. Failed/Expired/Cancelled/Suspended → Retry with new plan
            # 3. No subscription yet → Create new

            if hasattr(user, 'subscription'):
                subscription = user.subscription
                old_plan = subscription.plan
                old_status = subscription.status

                # Reset subscription for new attempt (preserves HostingEnvironment relationship)
                subscription.plan = plan
                subscription.status = 'pending_payment'
                subscription.billing_cycle = billing_cycle
                subscription.billing_phase = billing_phase
                subscription.intro_cycles_remaining = intro_cycles_remaining
                subscription.currency = 'XAF'  # Default currency for Cameroon
                subscription.primary_workspace = workspace  # Update workspace if provided
                subscription.payment_intent = None  # Clear old payment intent
                subscription.grace_period_ends_at = None  # Clear grace period
                subscription.current_cycle_started_at = None  # Set on activation
                subscription.current_cycle_ends_at = None  # Set on activation
                subscription.save()

                # Determine action for history
                if old_status in ['failed', 'expired', 'cancelled', 'suspended']:
                    action = 'reactivated'
                    notes = f"Reactivating subscription from {old_status} to {plan_tier} ({billing_phase} pricing)"
                elif old_plan.tier == 'free':
                    action = 'upgraded'
                    notes = f"Upgrading from free to {plan_tier} ({billing_phase} pricing)"
                else:
                    action = 'upgraded'
                    notes = f"Upgrading from {old_plan.tier} to {plan_tier} ({billing_phase} pricing)"
            else:
                # No subscription yet - create new (first-time user)
                subscription = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    primary_workspace=workspace,
                    status='pending_payment',
                    billing_cycle=billing_cycle,
                    billing_phase=billing_phase,
                    intro_cycles_remaining=intro_cycles_remaining,
                    currency='XAF',  # Default currency for Cameroon
                    started_at=timezone.now(),
                    expires_at=None,  # Set on payment success
                    current_cycle_started_at=None,  # Set on activation
                    current_cycle_ends_at=None,  # Set on activation
                )

                action = 'created'
                notes = f"Created {plan_tier} subscription ({billing_phase} pricing) - awaiting payment"

            # Create PaymentIntent via payment module
            from payments.services.payment_service import PaymentService

            # Build metadata with action tracking and client context
            payment_metadata = {
                'action': 'create',
                'phone_number': phone_number,
                'plan_tier': plan_tier,
                'subscription_id': str(subscription.id),
                'billing_cycle': billing_cycle,
                'billing_phase': billing_phase,
                'cycle_duration_days': cycle_duration_days,
            }
            if client_context:
                payment_metadata['client_context'] = client_context

            payment_result = PaymentService.create_payment(
                workspace_id=workspace.id if workspace else None,
                user=user,
                amount=int(amount_to_charge),  # XAF has no subdivisions
                currency=subscription.currency,
                purpose='subscription',
                preferred_provider=preferred_provider,
                idempotency_key=idempotency_key,
                metadata=payment_metadata
            )

            if not payment_result['success']:
                raise ValidationError(f"Payment initiation failed: {payment_result.get('error')}")

            # Link PaymentIntent to subscription
            from payments.models import PaymentIntent
            payment_intent = PaymentIntent.objects.get(id=payment_result['payment_intent_id'])
            subscription.payment_intent = payment_intent
            subscription.save()

            # Create history and event log
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action=action,
                new_plan=plan,
                notes=notes
            )

            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='upgrade_initiated',
                description=f"Payment initiated for {plan_tier} subscription",
                metadata={'payment_intent_id': str(payment_intent.id)}
            )

            # Emit signal
            subscription_upgrade_initiated.send(
                sender=SubscriptionService,
                subscription=subscription,
                target_plan=plan,
                user=user
            )

            logger.info(f"Initiated subscription for {user.email} - {plan_tier} - PaymentIntent: {payment_intent.id}")

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'payment_intent_id': str(payment_intent.id),
                'payment_instructions': payment_result.get('instructions'),
                'redirect_url': payment_result.get('redirect_url'),
                'amount': float(amount_to_charge),
                'plan': plan_tier,
                'billing_cycle': billing_cycle,
                'billing_phase': billing_phase,
                'cycle_duration_days': cycle_duration_days,
            }
    
    @staticmethod
    def activate_subscription_from_payment(payment_intent):
        """
        Activate subscription when payment webhook confirms success
        Called by WebhookRouter for purpose='subscription'
        CRITICAL: Idempotent - can be called multiple times safely
        """
        try:
            # Get subscription from payment metadata
            subscription_id = payment_intent.metadata.get('subscription_id')
            if not subscription_id:
                logger.error(f"PaymentIntent {payment_intent.id} missing subscription_id in metadata")
                return {'success': False, 'error': 'Missing subscription_id in payment metadata'}

            subscription = Subscription.objects.select_for_update().get(id=subscription_id)
            user = subscription.user

            # IDEMPOTENCY: Check if this PaymentIntent has already been processed
            # Industry best practice: Track processed payment_intent_id to prevent duplicates
            # Reference: https://hookdeck.com/webhooks/guides/implement-webhook-idempotency
            existing_payment_record = PaymentRecord.objects.filter(payment_intent=payment_intent).first()
            if existing_payment_record:
                logger.info(f"PaymentIntent {payment_intent.id} already processed - idempotent webhook")
                return {
                    'success': True,
                    'already_processed': True,
                    'subscription_id': str(subscription.id),
                    'plan': subscription.plan.tier,
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                }

            with transaction.atomic():
                previous_status = subscription.status
                is_renewal = payment_intent.metadata.get('renewal', False)
                is_upgrade = payment_intent.metadata.get('upgrade', False)

                # Get cycle duration from payment metadata (set during initiate_subscription)
                cycle_days = payment_intent.metadata.get('cycle_duration_days', 30)

                # CRITICAL: Date preservation for early renewals (industry best practice)
                # If user renews in 5-day window, new subscription starts at old expires_at (no lost days)
                if is_renewal and subscription.expires_at and not subscription.is_expired:
                    # Early renewal: Stack cycle_days from current expires_at
                    subscription.current_cycle_started_at = subscription.expires_at
                    subscription.current_cycle_ends_at = subscription.expires_at + timedelta(days=cycle_days)
                    subscription.expires_at = subscription.current_cycle_ends_at
                    logger.info(f"Early renewal detected - stacking {cycle_days} days from current expiry")
                elif is_upgrade and subscription.expires_at and not subscription.is_expired:
                    # Upgrade during active subscription: Keep remaining time + cycle_days
                    # This only happens for free→paid or during renewal window
                    current_plan_metadata = subscription.subscription_metadata.get('pending_upgrade', {})
                    original_tier = current_plan_metadata.get('original_plan_tier', 'free')

                    if original_tier == 'free':
                        # Free → Paid upgrade: Start fresh cycle_days from now
                        subscription.current_cycle_started_at = timezone.now()
                        subscription.current_cycle_ends_at = timezone.now() + timedelta(days=cycle_days)
                        subscription.expires_at = subscription.current_cycle_ends_at
                    else:
                        # Paid → Paid upgrade (only allowed in renewal window): Stack from current expiry
                        subscription.current_cycle_started_at = subscription.expires_at
                        subscription.current_cycle_ends_at = subscription.expires_at + timedelta(days=cycle_days)
                        subscription.expires_at = subscription.current_cycle_ends_at
                        logger.info(f"Paid upgrade in renewal window - stacking {cycle_days} days from current expiry")

                    # Clear pending upgrade metadata
                    subscription.subscription_metadata.pop('pending_upgrade', None)
                else:
                    # New subscription, grace period renewal, or expired renewal: Start fresh
                    subscription.current_cycle_started_at = timezone.now()
                    subscription.current_cycle_ends_at = timezone.now() + timedelta(days=cycle_days)
                    subscription.expires_at = subscription.current_cycle_ends_at

                subscription.status = 'active'
                subscription.started_at = timezone.now()
                subscription.last_manual_renewal = timezone.now()
                subscription.grace_period_ends_at = None  # Clear grace period

                # Decrement intro_cycles_remaining for renewals in intro phase
                if is_renewal and subscription.billing_phase == 'intro' and subscription.intro_cycles_remaining > 0:
                    subscription.intro_cycles_remaining -= 1
                    logger.info(f"Decremented intro cycles - {subscription.intro_cycles_remaining} cycles remaining")

                    # If no intro cycles left, switch to regular phase
                    if subscription.intro_cycles_remaining == 0:
                        subscription.billing_phase = 'regular'
                        logger.info(f"Intro cycles exhausted - switching to regular phase")

                # Mark intro pricing as used (one-time offer)
                # BEST PRACTICE: Burn eligibility only after successful payment, not during initiation
                if subscription.billing_phase == 'intro':
                    # User used intro pricing - burn eligibility
                    user.mark_intro_pricing_used(subscription.plan.tier)
                    logger.info(f"Marked intro pricing as used for {user.email}")
                elif subscription.billing_phase == 'regular' and user.is_intro_pricing_eligible():
                    # User explicitly chose regular pricing on first subscription
                    # Burn eligibility now that payment succeeded (not during initiation)
                    # This follows best practice: eligibility burned only by explicit user intent + successful payment
                    user.mark_intro_pricing_used(subscription.plan.tier)
                    logger.info(f"User {user.email} chose regular pricing on first subscription - intro eligibility burned after successful payment")

                subscription.save()

                # Create PaymentRecord
                # NOTE: momo_operator uses provider_name as fallback for billing profile display
                PaymentRecord.objects.create(
                    user=user,
                    subscription=subscription,
                    payment_intent=payment_intent,
                    amount=payment_intent.amount,
                    reference=payment_intent.provider_intent_id or '',
                    momo_operator=payment_intent.metadata.get('momo_operator') or payment_intent.provider_name or '',
                    momo_phone_used=payment_intent.metadata.get('phone_number', ''),
                    transaction_id=payment_intent.provider_intent_id or '',
                    raw_webhook_payload=payment_intent.metadata,
                    status='success',
                )

                # Update existing history record to 'paid' status
                # Find the pending history record created during initiation
                existing_history = SubscriptionHistory.objects.filter(
                    subscription=subscription,
                    status='unpaid'
                ).order_by('-created_at').first()

                if existing_history:
                    # Update existing record
                    existing_history.status = 'paid'
                    existing_history.amount_paid = payment_intent.amount
                    existing_history.payment_method = payment_intent.provider_name
                    existing_history.notes = f"Activated via {payment_intent.provider_name} payment"
                    existing_history.save()
                else:
                    # Fallback: Create new history record if no pending found
                    SubscriptionHistory.objects.create(
                        subscription=subscription,
                        action='upgraded' if previous_status == 'pending_payment' else 'renewed',
                        new_plan=subscription.plan,
                        amount_paid=payment_intent.amount,
                        payment_method=payment_intent.provider_name,
                        notes=f"Activated via {payment_intent.provider_name} payment",
                        status='paid'
                    )


                # Detect context to emit correct signal (architecturally correct event emission)
                # This ensures receivers get the right signal and queue the right tasks
                old_plan = None
                tier_changed = False

                if is_upgrade:
                    # Check if tier actually changed (could be same-tier renewal)
                    pending_upgrade_metadata = subscription.subscription_metadata.get('pending_upgrade', {})
                    old_tier = pending_upgrade_metadata.get('original_plan_tier')

                    if old_tier and old_tier != subscription.plan.tier:
                        tier_changed = True
                        # Get old plan object for signal emission
                        from subscription.models import Plan
                        try:
                            old_plan = Plan.objects.get(tier=old_tier)
                        except Plan.DoesNotExist:
                            logger.warning(f"Old plan not found for tier {old_tier} - will emit upgrade signal without old_plan")

                # Emit appropriate signals based on context
                if tier_changed and old_plan:
                    # Tier changed (upgrade or downgrade) - emit plan_change_applied
                    from subscription.events import plan_change_applied

                    SubscriptionEventLog.objects.create(
                        subscription=subscription,
                        user=user,
                        event_type='plan_changed',
                        description=f"Plan changed from {old_plan.tier} to {subscription.plan.tier} via payment",
                        metadata={
                            'payment_intent_id': str(payment_intent.id),
                            'provider': payment_intent.provider_name,
                            'amount': float(payment_intent.amount),
                            'old_tier': old_plan.tier,
                            'new_tier': subscription.plan.tier,
                        }
                    )

                    plan_change_applied.send(
                        sender=SubscriptionService,
                        subscription=subscription,
                        old_plan=old_plan,
                        new_plan=subscription.plan,
                        user=user
                    )

                    logger.info(
                        f"Plan changed for {user.email}: {old_plan.tier} → {subscription.plan.tier} "
                        f"(Emitted plan_change_applied signal)"
                    )
                else:
                    # First activation or same-tier renewal - emit subscription_activated
                    SubscriptionEventLog.objects.create(
                        subscription=subscription,
                        user=user,
                        event_type='subscription_activated',
                        description=f"{subscription.plan.name} activated via payment webhook",
                        metadata={
                            'payment_intent_id': str(payment_intent.id),
                            'provider': payment_intent.provider_name,
                            'amount': float(payment_intent.amount),
                        }
                    )

                    subscription_activated.send(
                        sender=SubscriptionService,
                        subscription=subscription,
                        user=user,
                        previous_status=previous_status
                    )

                    logger.info(
                        f"Activated subscription {subscription.id} for {user.email} - {subscription.plan.tier} "
                        f"(Emitted subscription_activated signal)"
                    )

                return {
                    'success': True,
                    'subscription_id': str(subscription.id),
                    'plan': subscription.plan.tier,
                    'expires_at': subscription.expires_at.isoformat(),
                }

        except Subscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found for PaymentIntent {payment_intent.id}")
            return {'success': False, 'error': 'Subscription not found'}
        except Exception as e:
            logger.error(f"Failed to activate subscription from payment: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def handle_payment_failure(payment_intent):
        """
        Handle payment failure for subscription/upgrade/renewal
        Called by WebhookRouter when payment fails

        REVERSION LOGIC (industry best practice - protect user's existing service):
        - If upgrade payment fails:
          1. Check if old plan is still valid (active or in grace period)
          2. If valid: Revert to old plan (preserve user's current access)
          3. If expired: Fall back to free plan
        - If new subscription payment fails: Mark as failed/expired

        IDEMPOTENT: Safe to call multiple times
        """
        try:
            subscription_id = payment_intent.metadata.get('subscription_id')
            if not subscription_id:
                logger.error(f"PaymentIntent {payment_intent.id} missing subscription_id in metadata")
                return {'success': False, 'error': 'Missing subscription_id in payment metadata'}

            subscription = Subscription.objects.select_for_update().get(id=subscription_id)
            user = subscription.user

            # Check if this was an upgrade (has pending_upgrade metadata)
            pending_upgrade = subscription.subscription_metadata.get('pending_upgrade', {})
            is_upgrade = bool(pending_upgrade)

            with transaction.atomic():
                if is_upgrade:
                    # UPGRADE PAYMENT FAILED - Reversion logic
                    original_plan_id = pending_upgrade.get('original_plan_id')
                    original_plan_tier = pending_upgrade.get('original_plan_tier')
                    target_plan_tier = pending_upgrade.get('target_plan_tier')

                    logger.warning(f"Upgrade payment failed: {original_plan_tier} → {target_plan_tier}")

                    try:
                        original_plan = SubscriptionPlan.objects.get(id=original_plan_id)
                    except SubscriptionPlan.DoesNotExist:
                        # Fallback: Get plan by tier
                        original_plan = SubscriptionPlan.objects.get(tier=original_plan_tier, is_active=True)

                    # CRITICAL: Check if old plan is still valid
                    # This prevents user from losing access if they had time remaining
                    old_plan_still_valid = subscription.is_old_plan_still_valid

                    if old_plan_still_valid:
                        # Revert to original plan (preserve current expiry and status)
                        subscription.plan = original_plan
                        # Keep current status (active or grace_period) and expires_at
                        # Just remove pending_upgrade metadata
                        subscription.subscription_metadata.pop('pending_upgrade', None)
                        subscription.payment_intent = None
                        subscription.save()

                        action_taken = f"Reverted to {original_plan_tier} (still valid)"
                        logger.info(f"Reverted subscription {subscription.id} to {original_plan_tier} - plan still valid")
                    else:
                        # Old plan expired - move to RESTRICTED status (keep tier)
                        # Industry standard: Gate actions, not data. Never hard-downgrade.
                        # Auto-downgrade to free only after SUBSCRIPTION_DELINQUENCY_DAYS
                        subscription.plan = original_plan
                        subscription.status = 'restricted'
                        subscription.subscription_metadata.pop('pending_upgrade', None)
                        subscription.subscription_metadata['restricted_at'] = timezone.now().isoformat()
                        subscription.subscription_metadata['restricted_reason'] = 'upgrade_payment_failed_plan_expired'
                        subscription.payment_intent = None
                        subscription.save()

                        action_taken = f"Moved to restricted status on {original_plan_tier} (old plan expired)"
                        logger.info(f"Subscription {subscription.id} moved to restricted - old plan expired")

                    # Create history record
                    SubscriptionHistory.objects.create(
                        subscription=subscription,
                        action='upgraded',  # Attempted upgrade
                        previous_plan=original_plan if old_plan_still_valid else None,
                        new_plan=subscription.plan,
                        notes=f"Upgrade payment failed: {original_plan_tier} → {target_plan_tier}. {action_taken}"
                    )

                else:
                    # NEW SUBSCRIPTION OR RENEWAL PAYMENT FAILED
                    # CRITICAL: Preserve original status before modifying (bug fix)
                    original_status = subscription.status
                    is_renewal = payment_intent.metadata.get('renewal', False)

                    if is_renewal:
                        # Renewal failed - check original status to determine fallback
                        if original_status == 'grace_period' and subscription.is_in_grace_period:
                            # Keep in grace period (don't change subscription)
                            subscription.payment_intent = None
                            action_taken = "Payment failed - subscription remains in grace period"
                        else:
                            # Grace period still valid or expired - move to RESTRICTED
                            # Industry standard: Keep tier, gate actions, allow easy reactivation
                            subscription.status = 'restricted'
                            subscription.subscription_metadata['restricted_at'] = timezone.now().isoformat()
                            subscription.subscription_metadata['restricted_reason'] = 'renewal_payment_failed'
                            subscription.payment_intent = None
                            action_taken = "Renewal payment failed - moved to restricted status"
                    else:
                        # New subscription payment failed
                        subscription.status = 'failed'
                        subscription.payment_intent = None
                        action_taken = "New subscription payment failed - marked as failed"

                    subscription.save()

                    # Create history record
                    SubscriptionHistory.objects.create(
                        subscription=subscription,
                        action='created',
                        new_plan=subscription.plan,
                        notes=f"Payment failed. {action_taken}"
                    )

                # Create event log
                SubscriptionEventLog.objects.create(
                    subscription=subscription,
                    user=user,
                    event_type='payment_failed',
                    description=f"Payment failed for {subscription.plan.name}",
                    metadata={
                        'payment_intent_id': str(payment_intent.id),
                        'is_upgrade': is_upgrade,
                        'provider': payment_intent.provider_name,
                    }
                )

                logger.info(f"Handled payment failure for subscription {subscription.id}")

                return {
                    'success': True,
                    'subscription_id': str(subscription.id),
                    'action_taken': action_taken if 'action_taken' in locals() else 'Payment failure processed',
                }

        except Subscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found for PaymentIntent {payment_intent.id}")
            return {'success': False, 'error': 'Subscription not found'}
        except Exception as e:
            logger.error(f"Failed to handle payment failure: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def initiate_manual_renewal(user, phone_number, preferred_provider='fapshi',
                               idempotency_key=None, client_context=None):
        """
        Initiate manual renewal (webhook-driven pattern)
        Returns PaymentIntent for user to complete payment via USSD

        RENEWAL WINDOWS:
        - 5-day window before expiry (active subscription)
        - Grace period (72 hours after expiry)
        - After grace period: Must create new subscription (cannot renew)

        CONCURRENCY: Uses select_for_update to prevent race conditions

        Args:
            idempotency_key: Optional UUID for preventing duplicate requests (auto-generated if missing)
            client_context: Optional dict with ip, user_agent, locale for fraud detection
        """
        # Auto-generate idempotency key if not provided (dev convenience)
        if not idempotency_key:
            import uuid as uuid_lib
            idempotency_key = str(uuid_lib.uuid4())

        # Check for existing PaymentIntent with this idempotency key
        from payments.models import PaymentIntent
        existing_intent = PaymentIntent.objects.filter(idempotency_key=idempotency_key).first()
        if existing_intent:
            logger.info(f"Idempotency key {idempotency_key} already processed - returning existing PaymentIntent")
            return {
                'success': True,
                'already_processed': True,
                'payment_intent_id': str(existing_intent.id),
                'subscription_id': existing_intent.metadata.get('subscription_id'),
                'amount': float(existing_intent.amount),
            }
        # All operations in single transaction with row lock (production best practice)
        with transaction.atomic():
            # CRITICAL: Lock subscription row FIRST to prevent concurrent renewals
            # This prevents double-clicking or race conditions from creating multiple PaymentIntents
            try:
                subscription = Subscription.objects.select_for_update().get(user=user)
            except Subscription.DoesNotExist:
                raise ValidationError("No active subscription found")

            if subscription.plan.tier == 'free':
                raise ValidationError("Free plans cannot be renewed")

            # CRITICAL: Check for existing pending payment (prevent double USSD prompts)
            # Same protection as create_subscription (lines 92-121)
            if subscription.status == 'pending_payment' and subscription.payment_intent:
                payment_intent = subscription.payment_intent

                # Check if PaymentIntent expired (30-minute security timeout)
                if payment_intent.is_expired:
                    # Allow new renewal attempt (old payment expired)
                    logger.info(f"Previous renewal PaymentIntent {payment_intent.id} expired - allowing new attempt")
                else:
                    # Payment session still active - block duplicate renewal
                    raise ValidationError({
                        'error': f"Pending renewal payment exists. Complete or cancel first.",
                        'error_code': 'PENDING_PAYMENT',
                        'payment_intent_id': str(payment_intent.id),
                        'expires_at': payment_intent.expires_at.isoformat() if payment_intent.expires_at else None,
                    })

            # STRICT: Check renewal eligibility based on subscription state
            if subscription.status == 'active':
                # Active subscription: Check if in 5-day renewal window
                if not subscription.is_in_renewal_window:
                    days_left = subscription.days_until_expiry
                    if days_left is not None and days_left > 5:
                        raise ValidationError({
                            'error': f'Renewals only allowed in 5-day renewal window (you have {days_left} days left)',
                            'error_code': 'RENEWAL_OUTSIDE_WINDOW',
                            'days_until_renewal_window': days_left - 5,
                            'renewal_window_starts': (subscription.expires_at - timezone.timedelta(days=5)).isoformat() if subscription.expires_at else None,
                            'current_expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                            'suggestion': 'Come back during the last 5 days of your subscription to renew'
                        })

            elif subscription.status == 'grace_period':
                # Grace period: Check if grace period is still valid
                if not subscription.is_in_grace_period:
                    raise ValidationError({
                        'error': 'Grace period expired. Please create a new subscription.',
                        'error_code': 'GRACE_PERIOD_EXPIRED',
                        'grace_period_ended': subscription.grace_period_ends_at.isoformat() if subscription.grace_period_ends_at else None,
                        'suggestion': 'Start a new subscription to reactivate your plan'
                    })

            elif subscription.status == 'suspended':
                # Suspended after grace period - allow reactivation via renewal
                # Industry standard: Easy reactivation to same tier
                logger.info(f"Reactivating suspended {subscription.plan.tier} subscription for {user.email}")

            elif subscription.status == 'cancelled':
                # User cancelled but trying to renew - guide to correct action
                # Check if still in paid period (can resume) or expired (must create new)
                if subscription.expires_at and timezone.now() < subscription.expires_at:
                    # Still in paid period - should use resume instead
                    days_remaining = (subscription.expires_at - timezone.now()).days
                    raise ValidationError({
                        'error': 'Your subscription is cancelled but still active. You can resume your current plan instead of renewing.',
                        'error_code': 'USE_RESUME_INSTEAD',
                        'current_status': 'cancelled',
                        'plan_tier': subscription.plan.tier,
                        'expires_at': subscription.expires_at.isoformat(),
                        'days_remaining': days_remaining,
                        'suggestion': 'Use the "Resume Subscription" button to continue your current plan without payment'
                    })
                else:
                    # Paid period expired (already downgraded to free) - must create new subscription
                    raise ValidationError({
                        'error': 'Your cancelled subscription has expired. Please create a new subscription.',
                        'error_code': 'CANCELLED_SUBSCRIPTION_EXPIRED',
                        'current_status': 'cancelled',
                        'suggestion': 'Select a plan to start a new subscription'
                    })

            else:
                # pending_payment, failed, expired, etc.
                raise ValidationError({
                    'error': f"Cannot renew subscription with status: {subscription.status}",
                    'error_code': 'INVALID_STATUS_FOR_RENEWAL',
                    'current_status': subscription.status,
                    'suggestion': 'Please use the plan selection page to choose a new subscription'
                })
            # Calculate renewal price based on intro_cycles_remaining
            # ROBUST LOGIC: Check effective remaining cycles for the NEXT period
            # If current phase is intro, we are consuming one cycle now
            is_currently_consuming_intro = (subscription.billing_phase == 'intro')
            effective_remaining_for_next = subscription.intro_cycles_remaining - (1 if is_currently_consuming_intro else 0)

            if effective_remaining_for_next > 0:
                billing_phase = 'intro'
                renewal_price = subscription.plan.intro_price
                cycle_duration_days = subscription.plan.intro_duration_days
                logger.info(f"Renewal eligible for intro pricing (Effective remaining: {effective_remaining_for_next})")
            else:
                billing_phase = 'regular'
                renewal_price = subscription.plan.get_price(subscription.billing_cycle, 'regular')
                cycle_duration_days = 365 if subscription.billing_cycle == 'yearly' else 30
                logger.info(f"Renewal switching to regular pricing (Effective remaining: {effective_remaining_for_next})")

            # Create PaymentIntent via payment module
            from payments.services.payment_service import PaymentService

            # Build metadata with action tracking and client context
            payment_metadata = {
                'action': 'renew',
                'phone_number': phone_number,
                'plan_tier': subscription.plan.tier,
                'subscription_id': str(subscription.id),
                'renewal': True,
                'billing_cycle': subscription.billing_cycle,
                'billing_phase': billing_phase,  # Use calculated phase (intro if cycles remain, else regular)
                'cycle_duration_days': cycle_duration_days,
            }
            if client_context:
                payment_metadata['client_context'] = client_context

            payment_result = PaymentService.create_payment(
                workspace_id=subscription.primary_workspace.id if subscription.primary_workspace else None,
                user=user,
                amount=int(renewal_price),  # XAF has no subdivisions
                currency=subscription.currency,
                purpose='subscription',
                preferred_provider=preferred_provider,
                idempotency_key=idempotency_key,
                metadata=payment_metadata
            )

            if not payment_result['success']:
                raise ValidationError(f"Payment initiation failed: {payment_result.get('error')}")

            # Link PaymentIntent to subscription
            from payments.models import PaymentIntent
            payment_intent = PaymentIntent.objects.get(id=payment_result['payment_intent_id'])
            subscription.payment_intent = payment_intent
            subscription.save()

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='subscription_renewed',
                description=f"Manual renewal payment initiated for {subscription.plan.name}",
                metadata={'payment_intent_id': str(payment_intent.id)}
            )

            logger.info(f"Initiated renewal for {user.email} - PaymentIntent: {payment_intent.id}")

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'payment_intent_id': str(payment_intent.id),
                'payment_instructions': payment_result.get('instructions'),
                'redirect_url': payment_result.get('redirect_url'),
                'amount': float(renewal_price),
                'billing_cycle': subscription.billing_cycle,
                'cycle_duration_days': cycle_duration_days,
            }

    @staticmethod
    def handle_subscription_expiry(subscription):
        """
        Handle subscription expiry with 72-hour grace period
        Called by Celery task checking expires_at

        Industry standard: 72-hour grace period for manual renewal systems
        """
        if subscription.status in ['expired', 'grace_period', 'cancelled']:
            return  # Already handled

        with transaction.atomic():
            # Start grace period (72 hours = 3 days)
            subscription.start_grace_period(hours=72)

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='suspended',
                notes="Started 72-hour grace period after expiry"
            )

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=subscription.user,
                event_type='grace_period_started',
                description=f"72-hour grace period started for {subscription.plan.name}",
                metadata={'grace_period_ends_at': subscription.grace_period_ends_at.isoformat()}
            )

            # Emit signal
            grace_period_started.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=subscription.user,
                grace_period_ends_at=subscription.grace_period_ends_at
            )

            logger.info(f"Started grace period for {subscription.user.email} - ends {subscription.grace_period_ends_at}")

    @staticmethod
    def handle_grace_period_end(subscription):
        """
        Handle end of grace period - move to RESTRICTED status (KEEP tier for easy reactivation)
        Called by Celery task checking grace_period_ends_at

        Industry Standard (gem.md):
        - Keep user on same plan tier
        - Mark as RESTRICTED (gate actions, not data)
        - User can reactivate via payment
        - Auto-downgrade to free only after SUBSCRIPTION_DELINQUENCY_DAYS (90 days)

        Note: 'suspended' status is reserved for fraud/abuse cases
        """
        if subscription.status == 'restricted':
            return  # Already processed

        with transaction.atomic():
            old_status = subscription.status

            # CRITICAL: Keep plan tier (don't downgrade to free)
            # Move to restricted status - gate actions, preserve data
            subscription.status = 'restricted'
            subscription.subscription_metadata['restricted_at'] = timezone.now().isoformat()
            subscription.subscription_metadata['restricted_reason'] = 'grace_period_expired'
            subscription.grace_period_ends_at = None
            subscription.save()

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='suspended',  # Keep action type for history consistency
                notes=f"{subscription.plan.tier} subscription restricted after grace period - user can reactivate via payment"
            )

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=subscription.user,
                event_type='status_changed',
                description=f"{subscription.plan.tier} subscription moved to restricted after grace period",
                metadata={'old_status': old_status, 'new_status': 'restricted', 'plan_tier': subscription.plan.tier}
            )

            # Emit signals
            grace_period_ended.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=subscription.user
            )

            subscription_suspended.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=subscription.user,
                reason='grace_period_expired'
            )

            logger.info(f"Grace period ended for {subscription.user.email} - {subscription.plan.tier} subscription restricted (can reactivate)")

    @staticmethod
    def handle_cancelled_subscription_expiry(subscription):
        """
        Handle cancelled subscription reaching expires_at
        Downgrades to free plan (honors paid period - industry standard)

        Called by Celery task for subscriptions with status='cancelled'

        TODO: Add Celery periodic task to check for cancelled subscriptions:
        @periodic_task(run_every=crontab(minute='*/30'))  # Every 30 minutes
        def process_cancelled_subscription_expiry():
            cancelled_subs = Subscription.objects.filter(
                status='cancelled',
                expires_at__lte=timezone.now()
            )
            for sub in cancelled_subs:
                SubscriptionService.handle_cancelled_subscription_expiry(sub)
        """
        if subscription.status != 'cancelled':
            return  # Not a cancelled subscription

        if subscription.expires_at and timezone.now() < subscription.expires_at:
            return  # Hasn't expired yet

        with transaction.atomic():
            old_plan = subscription.plan

            # Get free plan
            free_plan = SubscriptionPlan.objects.get(tier='free', is_active=True)

            # Downgrade to free (access period honored)
            subscription.plan = free_plan
            subscription.status = 'active'
            subscription.expires_at = None  # Free plans don't expire
            subscription.save()

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='downgraded',
                previous_plan=old_plan,
                new_plan=free_plan,
                notes=f"Auto-downgraded from {old_plan.tier} to free after cancelled subscription expired"
            )

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=subscription.user,
                event_type='downgrade_to_free',
                description=f"Cancelled {old_plan.tier} subscription expired - downgraded to free",
                metadata={'old_plan': old_plan.tier, 'reason': 'cancelled_subscription_expired'}
            )

            # Emit signal
            subscription_expired.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=subscription.user
            )

            logger.info(f"Cancelled subscription expired for {subscription.user.email} - downgraded from {old_plan.tier} to free")

    @staticmethod
    def handle_cycle_end(subscription):
        """
        Handle end of billing cycle - transition from intro to regular pricing
        Called by Celery task checking current_cycle_ends_at

        FLOW:
        - Intro cycle ends → Transition to regular pricing, mark for manual renewal
        - Regular cycle ends → Same as existing expiry handling (grace period)
        """
        if not subscription.current_cycle_ends_at:
            logger.warning(f"Subscription {subscription.id} has no current_cycle_ends_at")
            return

        now = timezone.now()
        if now < subscription.current_cycle_ends_at:
            return  # Cycle hasn't ended yet

        with transaction.atomic():
            if subscription.billing_phase == 'intro' and subscription.intro_cycles_remaining > 0:
                # INTRO CYCLE ENDED - Transition to regular pricing
                subscription.intro_cycles_remaining -= 1

                if subscription.intro_cycles_remaining == 0:
                    # Transition complete: intro → regular
                    subscription.billing_phase = 'regular'

                    # Set expiry at end of intro cycle (user must renew manually)
                    subscription.expires_at = subscription.current_cycle_ends_at
                    subscription.current_cycle_started_at = None
                    subscription.current_cycle_ends_at = None

                    subscription.save()

                    # Create event log
                    SubscriptionEventLog.objects.create(
                        subscription=subscription,
                        user=subscription.user,
                        event_type='plan_changed',
                        description=f"Intro pricing ended - transitioned to regular pricing for {subscription.plan.name}",
                        metadata={
                            'billing_phase': 'regular',
                            'expires_at': subscription.expires_at.isoformat(),
                            'must_renew': True
                        }
                    )

                    logger.info(f"Intro cycle ended for {subscription.user.email} - transitioned to regular pricing. Must renew manually.")

            elif subscription.billing_phase == 'regular':
                # Regular cycle ended - treat as subscription expiry
                # Delegate to existing expiry handling
                SubscriptionService.handle_subscription_expiry(subscription)
                logger.info(f"Regular cycle ended for {subscription.user.email} - handled as expiry")

    @staticmethod
    def handle_long_delinquency():
        """
        Handle subscriptions in restricted status past delinquency threshold.
        Auto-downgrade to free plan after SUBSCRIPTION_DELINQUENCY_DAYS (default: 90).

        Called by periodic Celery task (daily at 2:30 AM).

        Industry Standard (gem.md):
        - Only downgrade after long inactivity (60-90 days unpaid)
        - Never delete data, just lock features beyond lower plan limits

        Returns:
            Dict with count of processed subscriptions and any errors
        """
        from django.conf import settings
        from datetime import timedelta

        delinquency_days = getattr(settings, 'SUBSCRIPTION_DELINQUENCY_DAYS', 90)
        cutoff_date = timezone.now() - timedelta(days=delinquency_days)

        # Get IDs first without locking (select_for_update must be inside transaction)
        # Then lock each row individually in the processing loop
        delinquent_subscription_ids = list(Subscription.objects.filter(
            status='restricted',
            plan__tier__in=['beginning', 'pro', 'enterprise']
        ).values_list('id', flat=True))

        processed_count = 0
        error_count = 0
        processed_ids = []

        for subscription_id in delinquent_subscription_ids:
            try:
                with transaction.atomic():
                    # Lock and fetch subscription inside transaction
                    try:
                        subscription = Subscription.objects.select_for_update(
                            skip_locked=True
                        ).select_related('user', 'plan').get(id=subscription_id)
                    except Subscription.DoesNotExist:
                        continue  # Already processed or deleted

                    # Check restricted_at timestamp from metadata
                    restricted_at_str = subscription.subscription_metadata.get('restricted_at')
                    if not restricted_at_str:
                        # No timestamp - skip (edge case, shouldn't happen)
                        logger.warning(f"Subscription {subscription.id} in restricted status but missing restricted_at")
                        continue

                    # Parse ISO timestamp
                    from django.utils.dateparse import parse_datetime
                    restricted_at = parse_datetime(restricted_at_str)
                    if not restricted_at:
                        logger.warning(f"Subscription {subscription.id} has invalid restricted_at: {restricted_at_str}")
                        continue

                    # Check if past delinquency threshold
                    if restricted_at > cutoff_date:
                        # Not yet past threshold - skip
                        continue

                    old_plan = subscription.plan
                    free_plan = SubscriptionPlan.objects.get(tier='free', is_active=True)

                    # Downgrade to free (finally, after 90 days)
                    subscription.plan = free_plan
                    subscription.status = 'active'
                    subscription.expires_at = None  # Free plans don't expire
                    subscription.grace_period_ends_at = None
                    subscription.subscription_metadata['delinquency_downgrade_at'] = timezone.now().isoformat()
                    subscription.subscription_metadata['days_in_restricted'] = delinquency_days
                    subscription.save()

                    # Create history record
                    SubscriptionHistory.objects.create(
                        subscription=subscription,
                        action='downgraded',
                        previous_plan=old_plan,
                        new_plan=free_plan,
                        notes=f"Auto-downgraded from {old_plan.tier} to free after {delinquency_days} days in restricted status"
                    )

                    # Create event log
                    SubscriptionEventLog.objects.create(
                        subscription=subscription,
                        user=subscription.user,
                        event_type='downgrade_to_free',
                        description=f"Auto-downgraded from {old_plan.tier} to free after {delinquency_days}-day delinquency",
                        metadata={
                            'old_plan': old_plan.tier,
                            'delinquency_days': delinquency_days,
                            'restricted_at': restricted_at_str,
                            'reason': 'long_delinquency'
                        }
                    )

                    # Emit signal for downstream handling (de-provisioning, etc.)
                    subscription_downgraded.send(
                        sender=SubscriptionService,
                        subscription=subscription,
                        old_plan=old_plan,
                        new_plan=free_plan,
                        user=subscription.user
                    )

                    processed_count += 1
                    processed_ids.append(str(subscription.id))
                    logger.info(
                        f"Delinquency downgrade: {subscription.user.email} "
                        f"{old_plan.tier} -> free after {delinquency_days} days"
                    )

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing delinquency for subscription {subscription.id}: {e}")

        logger.info(f"Long delinquency processing complete: {processed_count} downgraded, {error_count} errors")

        return {
            'processed_count': processed_count,
            'error_count': error_count,
            'processed_ids': processed_ids,
            'delinquency_days': delinquency_days
        }

    @staticmethod
    def initiate_upgrade(user, new_plan_tier, phone_number, preferred_provider='fapshi',
                        idempotency_key=None, client_context=None):
        """
        Initiate subscription upgrade (webhook-driven pattern)
        Returns PaymentIntent for user to complete payment via USSD

        STRICT RULES:
        - Free → Paid: Anytime (immediate activation)
        - Paid → Higher Paid: Only in 5-day renewal window (prevents user from losing money)

        CONCURRENCY: Uses select_for_update to prevent race conditions

        Args:
            idempotency_key: Optional UUID for preventing duplicate requests (auto-generated if missing)
            client_context: Optional dict with ip, user_agent, locale for fraud detection
        """
        # Auto-generate idempotency key if not provided (dev convenience)
        if not idempotency_key:
            import uuid as uuid_lib
            idempotency_key = str(uuid_lib.uuid4())

        # Check for existing PaymentIntent with this idempotency key
        from payments.models import PaymentIntent
        existing_intent = PaymentIntent.objects.filter(idempotency_key=idempotency_key).first()
        if existing_intent:
            logger.info(f"Idempotency key {idempotency_key} already processed - returning existing PaymentIntent")
            return {
                'success': True,
                'already_processed': True,
                'payment_intent_id': str(existing_intent.id),
                'subscription_id': existing_intent.metadata.get('subscription_id'),
                'amount': float(existing_intent.amount),
            }
        # All operations in single transaction with row lock (production best practice)
        with transaction.atomic():
            # CRITICAL: Lock subscription row FIRST to prevent concurrent upgrades
            # This prevents double-clicking or race conditions from creating multiple PaymentIntents
            try:
                subscription = Subscription.objects.select_for_update().get(user=user)
                new_plan = SubscriptionPlan.objects.get(tier=new_plan_tier, is_active=True)
            except (Subscription.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
                raise ValidationError(str(e))

            # Validations
            if subscription.status not in ['active', 'grace_period']:
                raise ValidationError(f"Can only upgrade active subscriptions (current status: {subscription.status})")

            if new_plan.price_fcfa <= subscription.plan.price_fcfa:
                raise ValidationError("Cannot upgrade to lower or same tier. Use downgrade endpoint.")

            # CRITICAL: Paid → Paid upgrade restriction (industry best practice - no refunds)
            current_plan_is_paid = subscription.plan.tier != 'free'
            new_plan_is_paid = new_plan.tier != 'free'

            if current_plan_is_paid and new_plan_is_paid:
                # Paid → Higher Paid: Only allowed in renewal window or grace period
                if not subscription.can_renew_or_upgrade:
                    days_left = subscription.days_until_expiry

                    if subscription.status == 'active' and days_left is not None and days_left > 5:
                        raise ValidationError({
                            'error': f'Paid plan upgrades only allowed in 5-day renewal window (you have {days_left} days left)',
                            'error_code': 'UPGRADE_OUTSIDE_RENEWAL_WINDOW',
                            'days_until_renewal_window': days_left - 5,
                            'renewal_window_starts': (subscription.expires_at - timezone.timedelta(days=5)).isoformat() if subscription.expires_at else None,
                            'current_plan': subscription.plan.tier,
                            'current_expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                            'suggestion': 'You can upgrade during the last 5 days of your subscription, or after it expires during grace period'
                        })
                    elif subscription.status == 'expired':
                        raise ValidationError({
                            'error': 'Subscription expired. Please start a new subscription.',
                            'error_code': 'SUBSCRIPTION_EXPIRED',
                            'suggestion': 'Create a new subscription to activate a paid plan'
                        })
                    else:
                        raise ValidationError({
                            'error': 'Cannot upgrade at this time',
                            'error_code': 'UPGRADE_NOT_ALLOWED',
                            'current_status': subscription.status
                        })
            old_plan = subscription.plan

            # Calculate upgrade price (always regular pricing - no intro for upgrades)
            upgrade_price = new_plan.get_price(subscription.billing_cycle, 'regular')
            cycle_duration_days = 365 if subscription.billing_cycle == 'yearly' else 30

            # Store original plan for rollback if payment fails
            subscription.subscription_metadata['pending_upgrade'] = {
                'original_plan_id': str(old_plan.id),
                'original_plan_tier': old_plan.tier,
                'target_plan_id': str(new_plan.id),
                'target_plan_tier': new_plan.tier,
                'upgrade_amount': float(upgrade_price),
                'billing_cycle': subscription.billing_cycle,
                'initiated_at': timezone.now().isoformat()
            }

            # Update to new plan (not active until payment confirmed)
            subscription.plan = new_plan
            subscription.status = 'pending_payment'
            subscription.billing_phase = 'regular'  # Upgrades always use regular pricing
            subscription.intro_cycles_remaining = 0  # No intro cycles for upgrades
            subscription.save()

            # Create PaymentIntent via payment module
            from payments.services.payment_service import PaymentService

            # Build metadata with action tracking and client context
            payment_metadata = {
                'action': 'upgrade',
                'phone_number': phone_number,
                'plan_tier': new_plan.tier,
                'subscription_id': str(subscription.id),
                'upgrade': True,
                'previous_tier': old_plan.tier,
                'billing_cycle': subscription.billing_cycle,
                'billing_phase': 'regular',  # Upgrades always use regular pricing
                'cycle_duration_days': cycle_duration_days,
            }
            if client_context:
                payment_metadata['client_context'] = client_context

            payment_result = PaymentService.create_payment(
                workspace_id=subscription.primary_workspace.id if subscription.primary_workspace else None,
                user=user,
                amount=int(upgrade_price),  # XAF has no subdivisions
                currency=subscription.currency,
                purpose='subscription',
                preferred_provider=preferred_provider,
                idempotency_key=idempotency_key,
                metadata=payment_metadata
            )

            if not payment_result['success']:
                # Rollback plan change
                subscription.plan = old_plan
                subscription.status = 'active'
                subscription.subscription_metadata.pop('pending_upgrade', None)
                subscription.save()
                raise ValidationError(f"Payment initiation failed: {payment_result.get('error')}")

            # Link PaymentIntent to subscription
            from payments.models import PaymentIntent
            payment_intent = PaymentIntent.objects.get(id=payment_result['payment_intent_id'])
            subscription.payment_intent = payment_intent
            subscription.save()

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='upgraded',
                previous_plan=old_plan,
                new_plan=new_plan,
                notes=f"Upgrade from {old_plan.tier} to {new_plan.tier} - awaiting payment"
            )

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='upgrade_initiated',
                description=f"Upgrade from {old_plan.tier} to {new_plan.tier} initiated",
                metadata={'payment_intent_id': str(payment_intent.id)}
            )

            # Emit signal
            subscription_upgrade_initiated.send(
                sender=SubscriptionService,
                subscription=subscription,
                target_plan=new_plan,
                user=user
            )

            logger.info(f"Initiated upgrade for {user.email} from {old_plan.tier} to {new_plan.tier}")

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'payment_intent_id': str(payment_intent.id),
                'payment_instructions': payment_result.get('instructions'),
                'redirect_url': payment_result.get('redirect_url'),
                'amount': float(upgrade_price),
                'from_plan': old_plan.tier,
                'to_plan': new_plan.tier,
                'billing_cycle': subscription.billing_cycle,
                'billing_phase': 'regular',
                'cycle_duration_days': cycle_duration_days,
            }


    
    @staticmethod
    def schedule_downgrade(user, new_plan_tier, effective_date=None):
        """
        Schedule downgrade for next billing cycle
        Immediate downgrade not allowed - must wait for current period to end

        INDUSTRY PATTERN: Netflix, Spotify, GitHub - preserve paid access until renewal

        CONCURRENCY: Uses select_for_update to prevent race conditions
        VALIDATION: Checks for existing schedules, grace period, effective date
        """
        # All operations in single transaction with row lock
        with transaction.atomic():
            # CRITICAL: Lock subscription row to prevent concurrent schedule attempts
            try:
                subscription = Subscription.objects.select_for_update().get(user=user)
                new_plan = SubscriptionPlan.objects.get(tier=new_plan_tier, is_active=True)
            except Subscription.DoesNotExist:
                raise ValidationError("No active subscription found")
            except SubscriptionPlan.DoesNotExist:
                raise ValidationError({
                    'error': f"Plan '{new_plan_tier}' not found or inactive",
                    'error_code': 'PLAN_NOT_FOUND',
                    'requested_plan': new_plan_tier
                })

            # VALIDATION 1: Only active subscriptions
            if subscription.status == 'grace_period':
                raise ValidationError({
                    'error': 'Renew your subscription before scheduling a downgrade',
                    'error_code': 'GRACE_PERIOD_ACTIVE',
                    'current_status': 'grace_period',
                    'grace_period_ends_at': subscription.grace_period_ends_at.isoformat() if subscription.grace_period_ends_at else None,
                    'suggestion': 'Renew your subscription first, then schedule downgrade'
                })

            if subscription.status != 'active':
                raise ValidationError({
                    'error': f'Can only schedule downgrades for active subscriptions (current status: {subscription.status})',
                    'error_code': 'INVALID_STATUS_FOR_DOWNGRADE',
                    'current_status': subscription.status
                })

            # VALIDATION 2: No downgrade to Free (use cancel endpoint instead)
            if new_plan.tier == 'free':
                raise ValidationError({
                    'error': 'To downgrade to free plan, use the cancel subscription endpoint',
                    'error_code': 'USE_CANCEL_ENDPOINT',
                    'current_plan': subscription.plan.tier,
                    'suggestion': 'Use POST /subscriptions/cancel/ to cancel and downgrade to free immediately'
                })

            # VALIDATION 3: Must be actual downgrade
            if new_plan.price_fcfa >= subscription.plan.price_fcfa:
                raise ValidationError({
                    'error': 'Cannot downgrade to higher or same tier. Use upgrade endpoint.',
                    'error_code': 'NOT_A_DOWNGRADE',
                    'current_plan': subscription.plan.tier,
                    'current_price': float(subscription.plan.price_fcfa),
                    'new_plan': new_plan.tier,
                    'new_price': float(new_plan.price_fcfa),
                    'suggestion': 'Use POST /subscriptions/upgrade/ for plan upgrades'
                })

            # VALIDATION 4: Check for existing scheduled downgrade
            if subscription.pending_plan_change:
                raise ValidationError({
                    'error': f'Downgrade already scheduled to {subscription.pending_plan_change.tier} on {subscription.plan_change_effective_date.date()}',
                    'error_code': 'DOWNGRADE_ALREADY_SCHEDULED',
                    'current_plan': subscription.plan.tier,
                    'scheduled_plan': subscription.pending_plan_change.tier,
                    'scheduled_date': subscription.plan_change_effective_date.isoformat() if subscription.plan_change_effective_date else None,
                    'suggestion': 'Wait for scheduled downgrade to apply, or contact support to modify'
                })

            # VALIDATION 5: Parse and validate effective_date
            if effective_date:
                # Parse if string
                if isinstance(effective_date, str):
                    from django.utils.dateparse import parse_datetime
                    effective_date = parse_datetime(effective_date)
                    if not effective_date:
                        raise ValidationError({
                            'error': 'Invalid effective_date format. Use ISO 8601 format.',
                            'error_code': 'INVALID_DATE_FORMAT',
                            'suggestion': 'Use format: YYYY-MM-DDTHH:MM:SSZ (e.g., 2025-01-31T23:59:59Z)'
                        })

                # Validate not in past
                if effective_date < timezone.now():
                    raise ValidationError({
                        'error': 'Effective date cannot be in the past',
                        'error_code': 'PAST_EFFECTIVE_DATE',
                        'provided_date': effective_date.isoformat(),
                        'current_time': timezone.now().isoformat()
                    })

                # Validate not before current expiry (user would lose paid days)
                if subscription.expires_at and effective_date < subscription.expires_at:
                    raise ValidationError({
                        'error': 'Effective date cannot be before your current subscription expiry',
                        'error_code': 'EARLY_EFFECTIVE_DATE',
                        'current_expires_at': subscription.expires_at.isoformat(),
                        'provided_date': effective_date.isoformat(),
                        'suggestion': f'Your subscription expires on {subscription.expires_at.date()}. Downgrade will apply then automatically.'
                    })
            else:
                # Default: Schedule for current expiry
                effective_date = subscription.expires_at

            # VALIDATION 6: Free plans don't have expiry
            if not effective_date:
                raise ValidationError({
                    'error': 'Cannot schedule downgrade - subscription has no expiry date (free plan?)',
                    'error_code': 'NO_EXPIRY_DATE',
                    'current_plan': subscription.plan.tier
                })

            old_plan = subscription.plan

            subscription.schedule_plan_change(new_plan, effective_date)

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='downgraded',
                previous_plan=old_plan,
                new_plan=new_plan,
                notes=f"Downgrade scheduled from {old_plan.tier} to {new_plan.tier} on {effective_date.date()}"
            )

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='subscription_downgraded',
                description=f"Downgrade scheduled from {old_plan.tier} to {new_plan.tier}",
                metadata={
                    'effective_date': effective_date.isoformat(),
                    'current_plan': old_plan.tier,
                    'new_plan': new_plan.tier
                }
            )

            # Emit signal
            plan_change_scheduled.send(
                sender=SubscriptionService,
                subscription=subscription,
                current_plan=old_plan,
                pending_plan=new_plan,
                effective_date=effective_date,
                user=user
            )

            logger.info(f"Scheduled downgrade for {user.email} from {old_plan.tier} to {new_plan.tier} on {effective_date}")

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'from_plan': old_plan.tier,
                'to_plan': new_plan.tier,
                'effective_date': effective_date.isoformat(),
                'message': f"Downgrade scheduled for {effective_date.date()}"
            }
    
    @staticmethod
    def apply_pending_plan_changes():
        """
        Apply scheduled plan changes at billing cycle
        Called by Celery periodic task
        """
        subscriptions_with_changes = Subscription.objects.filter(
            pending_plan_change__isnull=False,
            plan_change_effective_date__lte=timezone.now()
        ).select_related('user', 'plan', 'pending_plan_change')

        applied_count = 0

        for subscription in subscriptions_with_changes:
            try:
                with transaction.atomic():
                    old_plan = subscription.plan
                    new_plan = subscription.pending_plan_change

                    if subscription.apply_pending_plan_change():
                        # Create history record
                        SubscriptionHistory.objects.create(
                            subscription=subscription,
                            action='downgraded',
                            previous_plan=old_plan,
                            new_plan=new_plan,
                            notes=f"Scheduled downgrade from {old_plan.tier} to {new_plan.tier} applied"
                        )

                        # Create event log
                        SubscriptionEventLog.objects.create(
                            subscription=subscription,
                            user=subscription.user,
                            event_type='plan_changed',
                            description=f"Plan changed from {old_plan.tier} to {new_plan.tier}",
                            metadata={'old_plan': old_plan.tier, 'new_plan': new_plan.tier}
                        )

                        # Emit signal
                        plan_change_applied.send(
                            sender=SubscriptionService,
                            subscription=subscription,
                            old_plan=old_plan,
                            new_plan=new_plan,
                            user=subscription.user
                        )

                        subscription_downgraded.send(
                            sender=SubscriptionService,
                            subscription=subscription,
                            old_plan=old_plan,
                            new_plan=new_plan,
                            user=subscription.user
                        )

                        applied_count += 1
                        logger.info(f"Applied plan change for {subscription.user.email} from {old_plan.tier} to {new_plan.tier}")

            except Exception as e:
                logger.error(f"Failed to apply plan change for subscription {subscription.id}: {str(e)}", exc_info=True)
                continue

        return {'applied_count': applied_count}
    
    @staticmethod
    def cancel_subscription(user, reason='user_requested'):
        """
        Cancel subscription - Industry standard approach (Shopify/Stripe pattern)

        Honors paid period:
        - User keeps access until expires_at (already paid for)
        - Sets status='cancelled' (semantic correctness)
        - Keeps tier (Pro/Enterprise) until expiry
        - Celery task downgrades to free at expires_at

        No refunds for Cameroon manual payment context
        """
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            raise ValidationError("No subscription found")

        if subscription.plan.tier == 'free':
            raise ValidationError("Cannot cancel free subscription")

        if subscription.status in ['cancelled', 'suspended']:
            raise ValidationError(f"Subscription already {subscription.status}")

        with transaction.atomic():
            old_plan = subscription.plan
            old_status = subscription.status

            # TWO CANCELLATION SCENARIOS:
            # A) Cancelled BEFORE payment (pending_payment) - Downgrade immediately
            # B) Cancelled AFTER payment (active/grace) - Honor paid period

            if old_status == 'pending_payment':
                # SCENARIO A: Cancel during pending payment
                # Two sub-cases:
                # A1) Upgrade/downgrade cancelled - revert to original plan
                # A2) New subscription cancelled - downgrade to free

                from subscription.models import SubscriptionPlan

                # Void pending payment (prevent double payment)
                if subscription.payment_intent:
                    from payments.services.payment_service import PaymentService
                    try:
                        PaymentService.void_payment(subscription.payment_intent.id)
                        logger.info(f"Voided pending payment {subscription.payment_intent.id} during cancellation")
                    except Exception as e:
                        logger.warning(f"Failed to void pending payment: {str(e)}")

                # Check if this was an upgrade/downgrade attempt
                pending_upgrade = subscription.subscription_metadata.get('pending_upgrade', {})

                if pending_upgrade:
                    # A1) Upgrade/downgrade cancelled - revert to original plan
                    original_plan_id = pending_upgrade.get('original_plan_id')
                    original_plan_tier = pending_upgrade.get('original_plan_tier')
                    original_status = pending_upgrade.get('original_status', 'active')
                    original_expires_at = pending_upgrade.get('original_expires_at')

                    logger.info(f"Cancelling upgrade attempt: {original_plan_tier} → {old_plan.tier}")

                    try:
                        original_plan = SubscriptionPlan.objects.get(id=original_plan_id)
                    except SubscriptionPlan.DoesNotExist:
                        # Fallback: Get plan by tier
                        original_plan = SubscriptionPlan.objects.get(tier=original_plan_tier, is_active=True)

                    # Revert to original plan (preserve user's existing paid access)
                    subscription.plan = original_plan
                    subscription.status = original_status  # Restore original status (active/grace_period)

                    # Restore original expires_at
                    if original_expires_at:
                        from datetime import datetime
                        subscription.expires_at = datetime.fromisoformat(original_expires_at)

                    subscription.payment_intent = None
                    subscription.subscription_metadata.pop('pending_upgrade', None)
                    subscription.subscription_metadata['cancellation_reason'] = reason
                    subscription.subscription_metadata['cancelled_at'] = timezone.now().isoformat()
                    subscription.subscription_metadata['upgrade_cancelled'] = True
                    subscription.save()

                    action_message = f"Cancelled upgrade from {original_plan_tier} to {old_plan.tier} - reverted to {original_plan_tier}"

                else:
                    # A2) New subscription cancelled (user was on free) - stay on free
                    free_plan = SubscriptionPlan.objects.get(tier='free', is_active=True)

                    subscription.plan = free_plan
                    subscription.status = 'cancelled'
                    subscription.expires_at = None  # Free plan doesn't expire
                    subscription.grace_period_ends_at = None
                    subscription.payment_intent = None
                    subscription.subscription_metadata['cancellation_reason'] = reason
                    subscription.subscription_metadata['cancelled_at'] = timezone.now().isoformat()
                    subscription.subscription_metadata['downgraded_immediately'] = True
                    subscription.subscription_metadata['never_paid'] = True
                    subscription.save()

                    action_message = f"Cancelled {old_plan.tier} subscription (never paid) - downgraded to free immediately"

            else:
                # SCENARIO B: Was active - honor paid period (Shopify/Stripe pattern)
                subscription.status = 'cancelled'
                # subscription.plan = KEEP (honor paid period)
                # subscription.expires_at = KEEP (access until paid period ends)
                subscription.grace_period_ends_at = None  # No grace period for cancelled subs
                subscription.payment_intent = None  # Clear payment intent
                subscription.subscription_metadata['cancellation_reason'] = reason
                subscription.subscription_metadata['cancelled_at'] = timezone.now().isoformat()
                subscription.subscription_metadata['will_downgrade_at'] = subscription.expires_at.isoformat() if subscription.expires_at else None
                subscription.save()

                action_message = f"Cancelled {old_plan.tier} subscription - access until {subscription.expires_at.isoformat() if subscription.expires_at else 'N/A'} - reason: {reason}"

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='cancelled',
                notes=action_message
            )

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='subscription_cancelled',
                description=f"{old_plan.tier} subscription cancelled - access until expiry",
                metadata={
                    'reason': reason,
                    'plan_tier': old_plan.tier,
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                    'will_downgrade_to_free': True
                }
            )

            # Emit signal
            subscription_cancelled.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=user,
                reason=reason
            )

            logger.info(f"Cancelled subscription for {user.email} - {action_message}")

            if old_status == 'pending_payment':
                # Check if upgrade was cancelled or new subscription
                if subscription.subscription_metadata.get('upgrade_cancelled'):
                    # Upgrade cancelled - reverted to original plan
                    return {
                        'success': True,
                        'subscription_id': str(subscription.id),
                        'previous_plan': old_plan.tier,
                        'current_plan': subscription.plan.tier,
                        'status': subscription.status,
                        'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                        'upgrade_cancelled': True,
                        'message': f'Upgrade cancelled. Payment was pending and has been voided. You remain on your current {subscription.plan.tier} plan.'
                    }
                else:
                    # New subscription cancelled - downgraded to free
                    return {
                        'success': True,
                        'subscription_id': str(subscription.id),
                        'previous_plan': old_plan.tier,
                        'current_plan': 'free',
                        'status': 'cancelled',
                        'expires_at': None,
                        'downgraded_immediately': True,
                        'message': f'Subscription cancelled. Payment was pending and has been voided. You are now on the Free plan.'
                    }
            else:
                # Was active - keeping access until expires_at
                return {
                    'success': True,
                    'subscription_id': str(subscription.id),
                    'previous_plan': old_plan.tier,
                    'current_plan': subscription.plan.tier,
                    'status': 'cancelled',
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                    'message': f'Subscription cancelled. You will keep {subscription.plan.tier} access until {subscription.expires_at.strftime("%B %d, %Y") if subscription.expires_at else "expiry"}.'
                }

    @staticmethod
    def resume_cancelled_subscription(user):
        """
        Resume cancelled subscription before it expires (Industry standard - Shopify/Stripe)

        Allows users to change their mind after cancellation.

        SECURITY:
        - Row-level locking (prevents race conditions)
        - Strict status validation
        - Expiry time verification
        - Idempotent operation (safe to call multiple times)

        BUSINESS RULES:
        - Only 'cancelled' subscriptions can be resumed
        - Must be before expires_at (honors paid period semantics)
        - Reverts to 'active' status (continues current cycle)
        - No payment required (already paid for this period)
        - After expiry: Must create new subscription instead

        CONCURRENCY: Uses select_for_update to prevent race conditions
        """
        # All operations in single transaction with row lock (production best practice)
        with transaction.atomic():
            # CRITICAL: Lock subscription row FIRST to prevent concurrent operations
            try:
                subscription = Subscription.objects.select_for_update().get(user=user)
            except Subscription.DoesNotExist:
                raise ValidationError("No subscription found")

            # VALIDATION 1: Must be cancelled status
            if subscription.status != 'cancelled':
                raise ValidationError({
                    'error': f"Cannot resume subscription with status: {subscription.status}",
                    'error_code': 'INVALID_STATUS_FOR_RESUME',
                    'current_status': subscription.status,
                    'suggestion': 'Only cancelled subscriptions can be resumed' if subscription.status == 'suspended' else None
                })

            # VALIDATION 2: Must have expires_at (sanity check)
            if not subscription.expires_at:
                raise ValidationError({
                    'error': 'Cancelled subscription has no expiry date',
                    'error_code': 'MISSING_EXPIRY_DATE',
                    'suggestion': 'Please contact support'
                })

            # VALIDATION 3: Must be before expires_at (core business rule)
            now = timezone.now()
            if now >= subscription.expires_at:
                days_expired = (now - subscription.expires_at).days
                raise ValidationError({
                    'error': 'Cancellation period has expired. Your subscription ended and you were downgraded to free.',
                    'error_code': 'CANCELLATION_EXPIRED',
                    'expired_at': subscription.expires_at.isoformat(),
                    'days_expired': days_expired,
                    'suggestion': 'Please create a new subscription to reactivate your plan'
                })

            # VALIDATION 4: Cannot resume free tier (edge case prevention)
            if subscription.plan.tier == 'free':
                raise ValidationError({
                    'error': 'Cannot resume free subscription',
                    'error_code': 'CANNOT_RESUME_FREE',
                    'suggestion': 'Please upgrade to a paid plan'
                })

            # IDEMPOTENCY CHECK: If status is somehow already active with same metadata
            # (e.g., double-click or retry), return success without error
            if subscription.status == 'active' and 'cancelled_at' not in subscription.subscription_metadata:
                logger.info(f"Resume called on already active subscription {subscription.id} - idempotent return")
                return {
                    'success': True,
                    'already_active': True,
                    'subscription_id': str(subscription.id),
                    'plan': subscription.plan.tier,
                    'expires_at': subscription.expires_at.isoformat(),
                    'message': 'Subscription is already active'
                }

            # Calculate remaining days for user message
            days_remaining = (subscription.expires_at - now).days

            # RESUME: Revert cancellation (no payment needed - already paid)
            old_status = subscription.status
            subscription.status = 'active'

            # Clear cancellation metadata (cleanup)
            cancellation_reason = subscription.subscription_metadata.pop('cancellation_reason', None)
            cancelled_at = subscription.subscription_metadata.pop('cancelled_at', None)
            subscription.subscription_metadata.pop('will_downgrade_at', None)

            # Track resume action (audit trail)
            subscription.subscription_metadata['resumed_at'] = now.isoformat()
            subscription.subscription_metadata['resumed_from_cancellation'] = True
            if cancelled_at:
                subscription.subscription_metadata['was_cancelled_at'] = cancelled_at

            subscription.save()

            # Create history record (audit trail)
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='reactivated',
                notes=f"User resumed {subscription.plan.tier} subscription before expiry ({days_remaining} days remaining)"
            )

            # Create event log (audit trail)
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='subscription_resumed',
                description=f"{subscription.plan.tier} subscription resumed after cancellation",
                metadata={
                    'previous_status': old_status,
                    'new_status': 'active',
                    'plan_tier': subscription.plan.tier,
                    'expires_at': subscription.expires_at.isoformat(),
                    'days_remaining': days_remaining,
                    'original_cancellation_reason': cancellation_reason
                }
            )

            # Emit signal (triggers any necessary infrastructure updates)
            subscription_reactivated.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=user
            )

            logger.info(f"User {user.email} resumed cancelled {subscription.plan.tier} subscription ({days_remaining} days remaining)")

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'plan': subscription.plan.tier,
                'status': 'active',
                'expires_at': subscription.expires_at.isoformat(),
                'days_remaining': days_remaining,
                'message': f'Subscription resumed successfully! You have {days_remaining} days remaining on your {subscription.plan.tier} plan.'
            }

    @staticmethod
    def suspend_subscription(user, reason='payment_failure'):
        """
        Suspend subscription for fraud/abuse/non-payment
        Admin action - preserves data but blocks access
        """
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            raise ValidationError("No subscription found")

        if subscription.status == 'suspended':
            raise ValidationError("Subscription already suspended")

        with transaction.atomic():
            subscription.suspend_subscription(reason=reason)

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='status_changed',
                description=f"Subscription suspended - reason: {reason}",
                metadata={'reason': reason, 'previous_status': 'active'}
            )

            # Emit signal
            subscription_suspended.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=user,
                reason=reason
            )

            logger.warning(f"Suspended subscription for {user.email} - reason: {reason}")

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'status': 'suspended',
                'reason': reason
            }

    @staticmethod
    def reactivate_suspended_subscription(user):
        """
        Reactivate suspended subscription
        Admin action after resolving suspension reason
        """
        try:
            subscription = user.subscription
        except Subscription.DoesNotExist:
            raise ValidationError("No subscription found")

        if subscription.status != 'suspended':
            raise ValidationError(f"Cannot reactivate subscription with status: {subscription.status}")

        with transaction.atomic():
            subscription.reactivate_subscription()

            # Create event log
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='status_changed',
                description="Subscription reactivated from suspended state",
                metadata={'previous_status': 'suspended'}
            )

            # Emit signal
            subscription_reactivated.send(
                sender=SubscriptionService,
                subscription=subscription,
                user=user
            )

            logger.info(f"Reactivated suspended subscription for {user.email}")

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'status': 'active',
                'message': 'Subscription reactivated successfully'
            }
    
    @staticmethod
    def get_subscription_status(user):
        """Get subscription status following SaaS best practices"""
        try:
            subscription = user.subscription

            # Determine user's current access level and required actions
            if subscription.status == 'pending_payment':
                # Check if this is an upgrade (has original plan in metadata)
                pending_upgrade = subscription.subscription_metadata.get('pending_upgrade', {})
                original_plan_tier = pending_upgrade.get('original_plan_tier', 'free')

                return {
                    'status': 'pending_payment',
                    'message': f'Payment required to activate {subscription.plan.name} plan',
                    'current_plan': original_plan_tier,
                    'target_plan': subscription.plan.tier,
                    'access_level': original_plan_tier,
                    'action_required': 'complete_payment',
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None
                }
            elif subscription.status == 'active':
                return {
                    'status': 'active',
                    'message': f'{subscription.plan.name} plan is active',
                    'current_plan': subscription.plan.tier,
                    'access_level': subscription.plan.tier,
                    'action_required': None,
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                    'days_remaining': subscription.days_until_expiry
                }
            elif subscription.status == 'expired':
                return {
                    'status': 'expired',
                    'message': 'Subscription expired. Renew to restore access',
                    'current_plan': 'free',
                    'previous_plan': subscription.plan.tier,
                    'access_level': 'free',
                    'action_required': 'renew_subscription',
                    'expired_at': subscription.expires_at.isoformat() if subscription.expires_at else None
                }

        except Subscription.DoesNotExist:
            return {
                'status': 'no_subscription',
                'message': 'No active subscription',
                'current_plan': 'free',
                'access_level': 'free',
                'action_required': None
            }

    @staticmethod
    def retry_pending_payment(user, phone_number, preferred_provider='fapshi',
                             idempotency_key=None, client_context=None):
        """
        Retry payment for a pending_payment subscription

        This method handles the case where a user has a subscription stuck in
        pending_payment status (due to expired/failed PaymentIntent).

        Logic:
        1. If active PaymentIntent exists (not expired) -> return it (idempotent)
        2. If PaymentIntent expired/failed -> create new PaymentIntent
        3. Link new PaymentIntent to subscription
        4. DOES NOT recreate subscription (preserves business intent)

        Follows key principle: "Subscription = intent, PaymentIntent = effort"

        Args:
            user: Django User instance
            phone_number: Mobile money number for payment
            preferred_provider: Payment provider (default: 'fapshi')
            idempotency_key: Optional UUID for preventing duplicate requests
            client_context: Optional dict with ip, user_agent, locale

        Returns:
            Dict with payment retry result

        Raises:
            ValidationError: If no pending subscription exists
        """
        # Auto-generate idempotency key if not provided
        if not idempotency_key:
            import uuid as uuid_lib
            idempotency_key = str(uuid_lib.uuid4())

        # Check for existing PaymentIntent with this idempotency key
        from payments.models import PaymentIntent
        existing_intent = PaymentIntent.objects.filter(idempotency_key=idempotency_key).first()
        if existing_intent:
            logger.info(f"Idempotency key {idempotency_key} already processed - returning existing PaymentIntent")
            return {
                'success': True,
                'already_processed': True,
                'payment_intent_id': str(existing_intent.id),
                'subscription_id': existing_intent.metadata.get('subscription_id'),
                'amount': float(existing_intent.amount),
            }

        with transaction.atomic():
            # Lock subscription row to prevent race conditions
            try:
                subscription = Subscription.objects.select_for_update().get(user=user)
            except Subscription.DoesNotExist:
                raise ValidationError({
                    'error': 'No subscription found',
                    'error_code': 'NO_SUBSCRIPTION',
                    'suggestion': 'Please select a plan to create a new subscription'
                })

            # Validate subscription is in pending_payment status
            if subscription.status != 'pending_payment':
                raise ValidationError({
                    'error': f'Subscription is not pending payment (status: {subscription.status})',
                    'error_code': 'NOT_PENDING_PAYMENT',
                    'current_status': subscription.status,
                    'suggestion': 'This endpoint is only for retrying pending payments'
                })

            # Check if subscription has an active PaymentIntent
            if subscription.payment_intent:
                payment_intent = subscription.payment_intent

                # If PaymentIntent is still valid (not expired, not in final state), return it
                if not payment_intent.is_expired and not payment_intent.is_final_state:
                    logger.info(f"Returning existing valid PaymentIntent: {payment_intent.id}")
                    return {
                        'success': True,
                        'existing_payment': True,
                        'subscription_id': str(subscription.id),
                        'payment_intent_id': str(payment_intent.id),
                        'status': payment_intent.status,
                        'amount': float(payment_intent.amount),
                        'expires_at': payment_intent.expires_at.isoformat(),
                        'message': 'Existing payment session still active. Complete the USSD prompt.'
                    }

                # PaymentIntent is expired or failed - we will create a new one
                logger.info(f"PaymentIntent {payment_intent.id} is {payment_intent.status}/expired - creating new one")

            # Determine pricing based on subscription state
            plan = subscription.plan
            billing_cycle = subscription.billing_cycle
            billing_phase = subscription.billing_phase

            if billing_phase == 'intro' and subscription.intro_cycles_remaining > 0:
                amount_to_charge = plan.intro_price
                cycle_duration_days = plan.intro_duration_days
            else:
                billing_phase = 'regular'
                amount_to_charge = plan.get_price(billing_cycle, 'regular')
                cycle_duration_days = 365 if billing_cycle == 'yearly' else 30

            # Create new PaymentIntent with retry tracking
            from payments.services.payment_service import PaymentService

            # Build metadata with action tracking
            payment_metadata = {
                'action': 'retry',
                'phone_number': phone_number,
                'plan_tier': plan.tier,
                'subscription_id': str(subscription.id),
                'billing_cycle': billing_cycle,
                'billing_phase': billing_phase,
                'cycle_duration_days': cycle_duration_days,
            }
            if client_context:
                payment_metadata['client_context'] = client_context

            # Track original payment intent for retry analytics
            original_intent_id = None
            if subscription.payment_intent:
                original_intent_id = subscription.payment_intent.original_payment_intent_id or subscription.payment_intent.id

            payment_result = PaymentService.create_payment(
                workspace_id=subscription.primary_workspace.id if subscription.primary_workspace else None,
                user=user,
                amount=int(amount_to_charge),
                currency=subscription.currency,
                purpose='subscription',
                preferred_provider=preferred_provider,
                idempotency_key=idempotency_key,
                metadata=payment_metadata
            )

            if not payment_result['success']:
                raise ValidationError(f"Payment initiation failed: {payment_result.get('error')}")

            # Link new PaymentIntent to subscription
            new_payment_intent = PaymentIntent.objects.get(id=payment_result['payment_intent_id'])

            # Track retry chain for analytics
            if original_intent_id:
                new_payment_intent.original_payment_intent_id = original_intent_id
                new_payment_intent.retry_count = (subscription.payment_intent.retry_count + 1) if subscription.payment_intent else 1
                new_payment_intent.save(update_fields=['original_payment_intent_id', 'retry_count'])

            subscription.payment_intent = new_payment_intent
            subscription.save(update_fields=['payment_intent', 'updated_at'])

            # Log event
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='payment_retry',
                description=f"Payment retry initiated for {plan.name} subscription",
                metadata={
                    'payment_intent_id': str(new_payment_intent.id),
                    'retry_count': new_payment_intent.retry_count,
                    'original_intent_id': str(original_intent_id) if original_intent_id else None
                }
            )

            logger.info(
                f"Retry payment created for {user.email} - "
                f"PaymentIntent: {new_payment_intent.id} (retry #{new_payment_intent.retry_count})"
            )

            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'payment_intent_id': str(new_payment_intent.id),
                'payment_instructions': payment_result.get('instructions'),
                'redirect_url': payment_result.get('redirect_url'),
                'amount': float(amount_to_charge),
                'plan': plan.tier,
                'billing_cycle': billing_cycle,
                'billing_phase': billing_phase,
                'cycle_duration_days': cycle_duration_days,
                'retry_count': new_payment_intent.retry_count,
                'message': 'New payment session created. Complete the USSD prompt.'
            }