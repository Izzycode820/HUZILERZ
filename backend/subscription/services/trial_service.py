"""
Trial Service - Production-Ready Webhook-Driven Architecture
Handles trial lifecycle with strict mutual exclusivity and payment decoupling
Follows same patterns as SubscriptionService
"""
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta
import logging

from ..models.trial import Trial
from ..models.subscription import SubscriptionPlan
from ..events import (
    trial_initiated,
    trial_activated,
    trial_expired,
    trial_converted,
    trial_cancelled,
)

logger = logging.getLogger(__name__)


class TrialService:
    """
    Manual payment trial workflow (Cameroon context)
    Webhook-driven, decoupled, strict validation
    """

    @staticmethod
    def initiate_trial(user, plan_tier, phone_number, workspace=None, preferred_provider='fapshi'):
        """
        Initiate trial creation (webhook-driven pattern)
        Returns PaymentIntent for user to complete payment via USSD

        STRICT RULES:
        - No trial if user has active paid subscription (mutual exclusivity)
        - One trial per tier per lifetime
        - Trial must complete before subscription activation
        """
        try:
            plan = SubscriptionPlan.objects.get(tier=plan_tier, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise ValidationError(f"Plan '{plan_tier}' not found")

        # Free plan doesn't have trials
        if plan.tier == 'free':
            raise ValidationError("Free plan doesn't offer trial period")

        # VALIDATION 1: Strict mutual exclusivity - no trial if paid subscription active
        if hasattr(user, 'subscription'):
            subscription = user.subscription

            # Active paid subscription blocks trial eligibility
            if subscription.status == 'active' and subscription.plan.tier != 'free':
                raise ValidationError({
                    'error': 'Cannot start trial while you have an active paid subscription',
                    'error_code': 'PAID_SUBSCRIPTION_ACTIVE',
                    'current_plan': subscription.plan.tier,
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None
                })

            # Pending payment for subscription blocks trial
            if subscription.status == 'pending_payment' and subscription.plan.tier != 'free':
                raise ValidationError({
                    'error': 'Complete or cancel pending subscription payment first',
                    'error_code': 'PENDING_SUBSCRIPTION_PAYMENT',
                    'pending_plan': subscription.plan.tier
                })

        # VALIDATION 2: Check trial eligibility (ONE trial per user lifetime - any tier)
        if user.trial_used_at is not None:
            raise ValidationError({
                'error': f'Trial already used. You tried {user.trial_tier_used} on {user.trial_used_at.strftime("%Y-%m-%d")}',
                'error_code': 'TRIAL_ALREADY_USED',
                'tier_used': user.trial_tier_used,
                'used_at': user.trial_used_at.isoformat(),
                'message': 'One trial per user lifetime. Choose your subscription plan.'
            })

        # VALIDATION 3: Check for existing active trial (shouldn't exist, but defensive)
        existing_trial = Trial.objects.filter(user=user, status='active').first()
        if existing_trial:
            raise ValidationError({
                'error': 'You already have an active trial. Complete it first.',
                'error_code': 'ACTIVE_TRIAL_EXISTS',
                'current_trial_tier': existing_trial.tier,
                'expires_at': existing_trial.expires_at.isoformat() if existing_trial.expires_at else None,
                'days_remaining': existing_trial.days_remaining
            })

        # VALIDATION 4: Check for pending trial payment
        pending_trial = Trial.objects.filter(user=user, status='pending_payment').first()
        if pending_trial:
            # Check if PaymentIntent expired
            if pending_trial.payment_intent and pending_trial.payment_intent.is_expired:
                # Cleanup expired trial
                pending_trial.status = 'expired'
                pending_trial.save()
            else:
                raise ValidationError({
                    'error': 'Complete or cancel pending trial payment first',
                    'error_code': 'PENDING_TRIAL_PAYMENT',
                    'trial_tier': pending_trial.tier,
                    'payment_intent_id': str(pending_trial.payment_intent.id) if pending_trial.payment_intent else None
                })

        # Get trial pricing from model
        from ..models.trial import TRIAL_PRICES

        trial_price = float(TRIAL_PRICES.get(plan_tier, TRIAL_PRICES['beginning']))
        trial_duration_days = 28

        with transaction.atomic():
            # Create trial record (pending payment)
            trial = Trial.objects.create(
                user=user,
                tier=plan_tier,
                status='pending_payment',
                payment_status='pending',
                trial_duration_days=trial_duration_days,
                trial_amount_paid=trial_price,
                started_at=None,  # Set on payment success
                expires_at=None   # Set on payment success
            )

            # Create PaymentIntent via payment module
            from payments.services.payment_service import PaymentService

            payment_result = PaymentService.create_payment(
                workspace_id=workspace.id if workspace else None,
                user=user,
                amount=int(trial_price * 100),  # Convert to centimes
                currency='XAF',
                purpose='trial',
                preferred_provider=preferred_provider,
                metadata={
                    'phone_number': phone_number,
                    'trial_tier': plan_tier,
                    'trial_id': str(trial.id),
                    'trial_duration_days': trial_duration_days
                }
            )

            if not payment_result['success']:
                raise ValidationError(f"Payment initiation failed: {payment_result.get('error')}")

            # Link PaymentIntent to trial
            from payments.models import PaymentIntent
            payment_intent = PaymentIntent.objects.get(id=payment_result['payment_intent_id'])
            trial.payment_intent = payment_intent
            trial.save()

            # Emit signal
            trial_initiated.send(
                sender=TrialService,
                trial=trial,
                user=user,
                tier=plan_tier
            )

            logger.info(f"Initiated trial for {user.email} - {plan_tier} - PaymentIntent: {payment_intent.id}")

            return {
                'success': True,
                'trial_id': str(trial.id),
                'payment_intent_id': str(payment_intent.id),
                'payment_instructions': payment_result.get('instructions'),
                'redirect_url': payment_result.get('redirect_url'),
                'amount': float(trial_price),
                'tier': plan_tier,
                'duration_days': trial_duration_days
            }

    @staticmethod
    def activate_trial_from_payment(payment_intent):
        """
        Activate trial when payment webhook confirms success
        Called by WebhookRouter for purpose='trial'
        CRITICAL: Idempotent - can be called multiple times safely
        """
        try:
            # Get trial from payment metadata
            trial_id = payment_intent.metadata.get('trial_id')
            if not trial_id:
                logger.error(f"PaymentIntent {payment_intent.id} missing trial_id in metadata")
                return {'success': False, 'error': 'Missing trial_id in payment metadata'}

            trial = Trial.objects.select_for_update().get(id=trial_id)
            user = trial.user

            # IDEMPOTENCY: If already active, don't re-activate
            if trial.status == 'active' and trial.expires_at:
                logger.info(f"Trial {trial.id} already active - idempotent webhook")
                return {'success': True, 'already_active': True}

            with transaction.atomic():
                # Set expiry (7 days for trials)
                trial_duration = trial.trial_duration_days or 7
                trial.started_at = timezone.now()
                trial.expires_at = timezone.now() + timedelta(days=trial_duration)
                trial.status = 'active'
                trial.payment_status = 'completed'
                trial.save()

                # Mark trial as used on user record (one-time flag)
                user.trial_used_at = timezone.now()
                user.trial_tier_used = trial.tier
                user.save(update_fields=['trial_used_at', 'trial_tier_used'])

                # Emit signal (triggers provisioning tasks)
                trial_activated.send(
                    sender=TrialService,
                    trial=trial,
                    user=user,
                    tier=trial.tier
                )

                logger.info(f"Activated trial {trial.id} for {user.email} - {trial.tier}")

                return {
                    'success': True,
                    'trial_id': str(trial.id),
                    'tier': trial.tier,
                    'expires_at': trial.expires_at.isoformat(),
                    'days_remaining': trial.days_remaining
                }

        except Trial.DoesNotExist:
            logger.error(f"Trial {trial_id} not found for PaymentIntent {payment_intent.id}")
            return {'success': False, 'error': 'Trial not found'}
        except Exception as e:
            logger.error(f"Failed to activate trial from payment: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def handle_trial_expiry(trial):
        """
        Handle trial expiry - mark as expired
        Called by Celery task checking expires_at
        """
        if trial.status in ['expired', 'converted', 'cancelled']:
            return  # Already handled

        with transaction.atomic():
            trial.status = 'expired'
            trial.save()

            # Emit signal
            trial_expired.send(
                sender=TrialService,
                trial=trial,
                user=trial.user,
                tier=trial.tier
            )

            logger.info(f"Trial expired for {trial.user.email} - {trial.tier}")

    @staticmethod
    def convert_trial_to_subscription(user, trial_id, target_tier, phone_number, preferred_provider='fapshi'):
        """
        Convert trial to paid subscription
        User can choose ANY tier - even lower than trial (their choice, their money)
        """
        try:
            trial = Trial.objects.get(id=trial_id, user=user)
        except Trial.DoesNotExist:
            raise ValidationError("Trial not found")

        # VALIDATION: Trial must be active or recently expired
        if trial.status not in ['active', 'expired']:
            raise ValidationError({
                'error': f'Cannot convert trial with status: {trial.status}',
                'error_code': 'INVALID_TRIAL_STATUS',
                'current_status': trial.status
            })

        # VALIDATION: Trial must be near expiry or expired (last 3 days or after)
        if trial.status == 'active' and trial.days_remaining > 3:
            raise ValidationError({
                'error': 'Trial conversion available in last 3 days or after expiry',
                'error_code': 'TRIAL_NOT_READY_FOR_CONVERSION',
                'days_remaining': trial.days_remaining,
                'available_in': trial.days_remaining - 3
            })

        # Log if downgrade (analytics - not blocking)
        if target_tier != trial.tier:
            logger.info(f"Trial tier mismatch - User {user.email}: trial={trial.tier}, choosing={target_tier}")

        try:
            with transaction.atomic():
                # Use subscription service to initiate subscription for chosen tier
                from .subscription_service import SubscriptionService

                subscription_result = SubscriptionService.initiate_subscription(
                    user=user,
                    plan_tier=target_tier,
                    phone_number=phone_number,
                    workspace=None,
                    preferred_provider=preferred_provider
                )

                if subscription_result['success']:
                    # Mark trial as converted
                    trial.status = 'converted'
                    trial.conversion_metadata = {
                        'payment_intent_id': subscription_result['payment_intent_id'],
                        'target_tier': target_tier,
                        'trial_tier': trial.tier,
                        'converted_at': timezone.now().isoformat()
                    }
                    trial.save()

                    # Emit signal
                    trial_converted.send(
                        sender=TrialService,
                        trial=trial,
                        user=user,
                        target_tier=target_tier
                    )

                    logger.info(f"Trial {trial.id} ({trial.tier}) converted to {target_tier} subscription for {user.email}")

                    return {
                        'success': True,
                        'trial_id': str(trial.id),
                        'subscription_payment_intent_id': subscription_result['payment_intent_id'],
                        'payment_instructions': subscription_result.get('payment_instructions'),
                        'redirect_url': subscription_result.get('redirect_url'),
                        'amount': subscription_result['amount'],
                        'trial_tier': trial.tier,
                        'subscription_tier': target_tier,
                        'message': f'Complete payment to activate {target_tier} subscription'
                    }
                else:
                    return subscription_result

        except Exception as e:
            logger.error(f"Trial conversion failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to convert trial: {str(e)}")

    @staticmethod
    def cancel_trial(user, trial_id, reason='user_requested'):
        """
        Cancel active trial immediately
        """
        try:
            trial = Trial.objects.get(id=trial_id, user=user)
        except Trial.DoesNotExist:
            raise ValidationError("Trial not found")

        if trial.status == 'cancelled':
            raise ValidationError("Trial already cancelled")

        if trial.status not in ['active', 'pending_payment']:
            raise ValidationError(f"Cannot cancel trial with status: {trial.status}")

        with transaction.atomic():
            trial.status = 'cancelled'
            trial.cancellation_metadata = {
                'reason': reason,
                'cancelled_at': timezone.now().isoformat()
            }
            trial.save()

            # Emit signal
            trial_cancelled.send(
                sender=TrialService,
                trial=trial,
                user=user,
                reason=reason
            )

            logger.info(f"Trial cancelled for {user.email} - {trial.tier} - reason: {reason}")

            return {
                'success': True,
                'trial_id': str(trial.id),
                'status': 'cancelled',
                'reason': reason
            }

    @staticmethod
    def get_user_trial_status(user):
        """
        Get user's trial status and eligibility (simplified - one trial per user lifetime)
        """
        try:
            # Get active trial
            active_trial = Trial.objects.filter(user=user, status='active').first()

            if active_trial:
                return {
                    'has_active_trial': True,
                    'trial': {
                        'id': str(active_trial.id),
                        'tier': active_trial.tier,
                        'status': active_trial.status,
                        'started_at': active_trial.started_at.isoformat(),
                        'expires_at': active_trial.expires_at.isoformat() if active_trial.expires_at else None,
                        'days_remaining': active_trial.days_remaining,
                        'can_convert': active_trial.days_remaining <= 3
                    }
                }

            # Simple eligibility: Check if trial already used OR paid subscription exists
            trial_blocked_by_subscription = False
            if hasattr(user, 'subscription'):
                sub = user.subscription
                if sub.status == 'active' and sub.plan.tier != 'free':
                    trial_blocked_by_subscription = True

            trial_already_used = user.trial_used_at is not None

            return {
                'has_active_trial': False,
                'trial_used': trial_already_used,
                'trial_tier_used': user.trial_tier_used,
                'trial_used_at': user.trial_used_at.isoformat() if user.trial_used_at else None,
                'eligible_for_trial': not trial_blocked_by_subscription and not trial_already_used,
                'blocked_reason': 'paid_subscription_active' if trial_blocked_by_subscription else ('trial_already_used' if trial_already_used else None)
            }

        except Exception as e:
            logger.error(f"Failed to get trial status for user {user.id}: {str(e)}")
            return {
                'has_active_trial': False,
                'trial_used': False,
                'eligible_for_trial': True
            }
