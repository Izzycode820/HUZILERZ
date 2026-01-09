"""
Subscription Views
Production-grade subscription CRUD operations and manual renewal
Follows security, scalability, maintainability, and best practices principles
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
import logging

from ..models import Subscription, SubscriptionPlan, Trial
from ..services import SubscriptionService

logger = logging.getLogger(__name__)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription(request):
    """
    Initiate subscription creation (webhook-driven pattern)
    Returns PaymentIntent for USSD payment completion

    CRITICAL: User explicitly chooses pricing mode (intro vs regular)

    Required parameters:
    - plan_tier: 'beginner', 'pro', or 'enterprise'
    - phone_number: Mobile money number for payment
    - pricing_mode: 'intro' or 'regular' (EXPLICIT user choice)

    Optional parameters:
    - billing_cycle: 'monthly' or 'yearly' (default: 'monthly')
    - idempotency_key: UUID for preventing duplicate requests
    - workspace_id: Workspace to attach subscription to
    - provider: Payment provider (default: 'fapshi')
    """
    try:
        plan_tier = request.data.get('plan_tier')
        workspace_id = request.data.get('workspace_id')
        phone_number = request.data.get('phone_number')
        preferred_provider = request.data.get('provider', 'fapshi')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        pricing_mode = request.data.get('pricing_mode', 'regular')  # NEW: explicit choice
        idempotency_key = request.data.get('idempotency_key')  # Optional

        if not plan_tier:
            return Response({
                'error': 'plan_tier is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            return Response({
                'error': 'phone_number is required for payment'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate pricing_mode
        if pricing_mode not in ['intro', 'regular']:
            return Response({
                'error': 'pricing_mode must be either "intro" or "regular"',
                'error_code': 'INVALID_PRICING_MODE'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate billing_cycle
        if billing_cycle not in ['monthly', 'yearly']:
            return Response({
                'error': 'billing_cycle must be either "monthly" or "yearly"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get workspace if provided
        workspace = None
        if workspace_id:
            try:
                from workspace.core.models import Workspace
                workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
            except Workspace.DoesNotExist:
                return Response({
                    'error': 'Workspace not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # Extract client context for fraud detection (automatic)
        client_context = {
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'locale': request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-CM'),
        }

        result = SubscriptionService.initiate_subscription(
            user=request.user,
            plan_tier=plan_tier,
            phone_number=phone_number,
            workspace=workspace,
            preferred_provider=preferred_provider,
            billing_cycle=billing_cycle,
            pricing_mode=pricing_mode,  # NEW: Pass explicit pricing choice
            idempotency_key=idempotency_key,
            client_context=client_context
        )

        # Handle idempotency response
        if result.get('already_processed'):
            return Response({
                'success': True,
                'already_processed': True,
                'subscription_id': result['subscription_id'],
                'payment_intent_id': result['payment_intent_id'],
                'amount': result['amount'],
                'message': 'This request was already processed (idempotency key match)'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'payment_intent_id': result['payment_intent_id'],
            'payment_instructions': result.get('payment_instructions'),
            'redirect_url': result.get('redirect_url'),
            'amount': result['amount'],
            'plan': result['plan'],
            'billing_cycle': result['billing_cycle'],
            'billing_phase': result['billing_phase'],  # NEW: intro or regular
            'cycle_duration_days': result['cycle_duration_days'],  # NEW: 28/30/365
            'message': f'Complete USSD payment to activate {plan_tier} subscription'
        }, status=status.HTTP_202_ACCEPTED)

    except ValidationError as e:
        # Handle structured ValidationError (pending payment, trial conflicts)
        error_message = e.message if hasattr(e, 'message') else str(e)

        # Dictionary errors (pending payment with resumption data)
        if isinstance(error_message, dict):
            return Response(error_message, status=status.HTTP_409_CONFLICT)

        # Standard validation error
        return Response({
            'error': error_message
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'create subscription', request.user.id
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def void_pending_payment(request, subscription_id):
    """
    Void pending payment subscription (Stripe PaymentIntent cancel pattern)

    Use cases (Industry standard - 70% cart abandonment):
    - User changed mind on plan selection
    - Entered wrong phone number for payment
    - Want to compare other plans first
    - Need fresh start with different payment method

    Only voids pending_payment/failed/expired subscriptions.
    For active subscriptions, use cancel_active_subscription endpoint.

    References:
    - Stripe PaymentIntent cancellation: https://docs.stripe.com/api/payment_intents/cancel
    - Abandoned checkout best practices (2025): 70% abandonment rate
    """
    try:
        from django.db import transaction
        from ..utils.error_handler import ProductionSafeErrorHandler

        # Security: Input validation
        if not subscription_id or len(subscription_id) > 255:
            return Response({
                'error': 'Invalid subscription ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Security: Verify subscription belongs to user
            try:
                subscription = Subscription.objects.select_for_update().get(
                    id=subscription_id,
                    user=request.user
                )
            except Subscription.DoesNotExist:
                logger.warning(f"Unauthorized subscription cancellation - Subscription: {subscription_id}, User: {request.user.id}")
                return Response({
                    'error': 'Subscription not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Validate subscription can be voided (only pending/failed/expired)
            if subscription.status not in ['pending_payment', 'failed', 'expired']:
                return Response({
                    'error': f'Cannot void {subscription.status} subscription. Use cancel_active_subscription endpoint for active subscriptions.',
                    'current_status': subscription.status,
                    'error_code': 'INVALID_STATUS_FOR_VOID'
                }, status=status.HTTP_409_CONFLICT)

            # Void subscription (Stripe PaymentIntent cancel pattern)
            plan_tier = subscription.plan.tier
            subscription.delete()

            # Clear subscription cache
            cache_key = f"subscription_status_{request.user.id}"
            cache.delete(cache_key)

            logger.info(f"Pending payment voided - Subscription: {subscription_id}, User: {request.user.id}, Tier: {plan_tier}")

            return Response({
                'success': True,
                'message': f'{plan_tier.title()} pending payment voided successfully',
                'subscription_id': subscription_id,
                'status': 'voided'
            }, status=status.HTTP_200_OK)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.safe_error_response(
            e, 'void pending payment', 'Unable to void pending payment'
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_active_subscription(request):
    """
    Cancel active subscription - downgrade to free plan immediately

    Use cases:
    - User no longer wants paid plan
    - Downgrade to free tier
    - Business closure or budget constraints

    Business rule: No refunds for Cameroon manual payment context
    User keeps access until current billing period ends, then downgrades to free.

    Uses SubscriptionService.cancel_subscription() for proper:
    - History tracking
    - Event logging
    - Signal emission
    - Cache invalidation
    """
    try:
        reason = request.data.get('reason', 'user_requested')

        # Validate reason length (prevent abuse)
        if reason and len(reason) > 500:
            return Response({
                'error': 'Cancellation reason too long (max 500 characters)'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = SubscriptionService.cancel_subscription(
            user=request.user,
            reason=reason
        )

        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'previous_plan': result['previous_plan'],
            'current_plan': result['current_plan'],
            'message': result['message']
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        # Handle structured ValidationError (free plan checks, already cancelled)
        error_data = e.message_dict if hasattr(e, 'message_dict') else (
            e.message if hasattr(e, 'message') else str(e)
        )

        # Structured errors with error_code → 409 CONFLICT (business rule violations)
        if isinstance(error_data, dict) and 'error_code' in error_data:
            return Response(error_data, status=status.HTTP_409_CONFLICT)

        # Simple string errors → 400 BAD_REQUEST
        return Response({
            'error': str(error_data)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'cancel active subscription', request.user.id
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renew_subscription(request):
    """
    Initiate manual subscription renewal (webhook-driven pattern)
    Returns PaymentIntent for USSD payment completion

    New parameters:
    - idempotency_key: Optional UUID for preventing duplicate requests
    """
    try:
        phone_number = request.data.get('phone_number')
        preferred_provider = request.data.get('provider', 'fapshi')
        idempotency_key = request.data.get('idempotency_key')  # Optional

        if not phone_number:
            return Response({
                'error': 'phone_number is required for payment'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract client context for fraud detection (automatic)
        client_context = {
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'locale': request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-CM'),
        }

        result = SubscriptionService.initiate_manual_renewal(
            user=request.user,
            phone_number=phone_number,
            preferred_provider=preferred_provider,
            idempotency_key=idempotency_key,
            client_context=client_context
        )

        # Handle idempotency response
        if result.get('already_processed'):
            return Response({
                'success': True,
                'already_processed': True,
                'subscription_id': result['subscription_id'],
                'payment_intent_id': result['payment_intent_id'],
                'amount': result['amount'],
                'message': 'This renewal request was already processed (idempotency key match)'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'payment_intent_id': result['payment_intent_id'],
            'payment_instructions': result.get('payment_instructions'),
            'redirect_url': result.get('redirect_url'),
            'amount': result['amount'],
            'billing_cycle': result.get('billing_cycle'),  # NEW
            'cycle_duration_days': result.get('cycle_duration_days'),  # NEW
            'message': 'Complete USSD payment to renew subscription'
        }, status=status.HTTP_202_ACCEPTED)

    except ValidationError as e:
        # Handle structured ValidationError (renewal window violations, grace period checks)
        error_data = e.message_dict if hasattr(e, 'message_dict') else (
            e.message if hasattr(e, 'message') else str(e)
        )

        # Structured errors with error_code → 409 CONFLICT (business rule violations)
        if isinstance(error_data, dict) and 'error_code' in error_data:
            return Response(error_data, status=status.HTTP_409_CONFLICT)

        # Simple string errors → 400 BAD_REQUEST
        return Response({
            'error': str(error_data)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'renew subscription', request.user.id
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_subscription(request):
    """
    Initiate subscription upgrade (webhook-driven pattern)
    Returns PaymentIntent for USSD payment completion

    New parameters:
    - idempotency_key: Optional UUID for preventing duplicate requests
    """
    try:
        new_plan_tier = request.data.get('new_plan_tier')
        phone_number = request.data.get('phone_number')
        preferred_provider = request.data.get('provider', 'fapshi')
        idempotency_key = request.data.get('idempotency_key')  # Optional

        if not new_plan_tier:
            return Response({
                'error': 'new_plan_tier is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            return Response({
                'error': 'phone_number is required for payment'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract client context for fraud detection (automatic)
        client_context = {
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'locale': request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-CM'),
        }

        result = SubscriptionService.initiate_upgrade(
            user=request.user,
            new_plan_tier=new_plan_tier,
            phone_number=phone_number,
            preferred_provider=preferred_provider,
            idempotency_key=idempotency_key,
            client_context=client_context
        )

        # Handle idempotency response
        if result.get('already_processed'):
            return Response({
                'success': True,
                'already_processed': True,
                'subscription_id': result['subscription_id'],
                'payment_intent_id': result['payment_intent_id'],
                'amount': result['amount'],
                'message': 'This upgrade request was already processed (idempotency key match)'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'payment_intent_id': result['payment_intent_id'],
            'payment_instructions': result.get('payment_instructions'),
            'redirect_url': result.get('redirect_url'),
            'amount': result['amount'],
            'from_plan': result['from_plan'],
            'to_plan': result['to_plan'],
            'billing_cycle': result.get('billing_cycle'),  # NEW
            'billing_phase': result.get('billing_phase'),  # NEW: always 'regular' for upgrades
            'cycle_duration_days': result.get('cycle_duration_days'),  # NEW
            'message': f'Complete USSD payment to upgrade from {result["from_plan"]} to {result["to_plan"]}'
        }, status=status.HTTP_202_ACCEPTED)

    except ValidationError as e:
        # Handle structured ValidationError (upgrade window violations, plan tier checks)
        error_data = e.message_dict if hasattr(e, 'message_dict') else (
            e.message if hasattr(e, 'message') else str(e)
        )

        # Structured errors with error_code → 409 CONFLICT (business rule violations)
        if isinstance(error_data, dict) and 'error_code' in error_data:
            return Response(error_data, status=status.HTTP_409_CONFLICT)

        # Simple string errors → 400 BAD_REQUEST
        return Response({
            'error': str(error_data)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'upgrade subscription', request.user.id
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_downgrade(request):
    """
    Schedule downgrade for next billing cycle
    No immediate payment - change applied at expiry
    """
    try:
        new_plan_tier = request.data.get('new_plan_tier')
        effective_date = request.data.get('effective_date')  # Optional

        if not new_plan_tier:
            return Response({
                'error': 'new_plan_tier is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = SubscriptionService.schedule_downgrade(
            user=request.user,
            new_plan_tier=new_plan_tier,
            effective_date=effective_date
        )

        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'from_plan': result['from_plan'],
            'to_plan': result['to_plan'],
            'effective_date': result['effective_date'],
            'message': result['message']
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        # Handle structured ValidationError (downgrade validation checks)
        error_data = e.message_dict if hasattr(e, 'message_dict') else (
            e.message if hasattr(e, 'message') else str(e)
        )

        # Structured errors with error_code → 409 CONFLICT (business rule violations)
        if isinstance(error_data, dict) and 'error_code' in error_data:
            return Response(error_data, status=status.HTTP_409_CONFLICT)

        # Simple string errors → 400 BAD_REQUEST
        return Response({
            'error': str(error_data)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'schedule downgrade', request.user.id
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resume_cancelled_subscription(request):
    """
    Resume cancelled subscription before expiry (Shopify/Stripe pattern)

    Allows users to change their mind after cancellation.
    No payment required - user already paid for this period.

    Business rules:
    - Only 'cancelled' subscriptions can be resumed
    - Must be before expires_at (honors paid period semantics)
    - Reverts to 'active' status (continues current cycle)
    - After expiry: Must create new subscription instead

    Use cases:
    - User cancelled by mistake
    - Changed mind within paid period
    - Wants to continue using paid features
    """
    try:
        result = SubscriptionService.resume_cancelled_subscription(
            user=request.user
        )

        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'plan': result['plan'],
            'status': result['status'],
            'expires_at': result['expires_at'],
            'days_remaining': result['days_remaining'],
            'message': result['message']
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        # Handle structured ValidationError (status checks, expiry checks)
        error_data = e.message_dict if hasattr(e, 'message_dict') else (
            e.message if hasattr(e, 'message') else str(e)
        )

        # Structured errors with error_code → 409 CONFLICT (business rule violations)
        if isinstance(error_data, dict) and 'error_code' in error_data:
            return Response(error_data, status=status.HTTP_409_CONFLICT)

        # Simple string errors → 400 BAD_REQUEST
        return Response({
            'error': str(error_data)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'resume cancelled subscription', request.user.id
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reactivate_subscription(request):
    """
    Reactivate suspended subscription
    Admin action - no payment required (suspension resolved)
    """
    try:
        result = SubscriptionService.reactivate_suspended_subscription(
            user=request.user
        )

        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'status': result['status'],
            'message': result['message']
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        # Handle structured ValidationError (reactivation validation checks)
        error_data = e.message_dict if hasattr(e, 'message_dict') else (
            e.message if hasattr(e, 'message') else str(e)
        )

        # Structured errors with error_code → 409 CONFLICT (business rule violations)
        if isinstance(error_data, dict) and 'error_code' in error_data:
            return Response(error_data, status=status.HTTP_409_CONFLICT)

        # Simple string errors → 400 BAD_REQUEST
        return Response({
            'error': str(error_data)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'reactivate subscription', request.user.id
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_capabilities(request):
    """
    Get full capabilities for user's current subscription tier

    Industry Standard (Stripe/GitHub/Vercel):
    - JWT contains minimal data (tier + version hash)
    - Capabilities fetched separately via API
    - Frontend caches capabilities and checks version hash

    Workflow:
    1. Frontend checks localStorage for cached capabilities
    2. Compares cached version with JWT version hash
    3. If version mismatch → calls this endpoint → updates cache
    4. If version match → uses cached capabilities (no API call)

    Benefits:
    - Add features to YAML → zero code changes
    - Run sync_plans → version hash changes automatically
    - Frontend auto-refreshes capabilities on version change
    - Truly dynamic feature system
    """
    try:
        from authentication.services.jwt_subscription_service import JWTSubscriptionService

        # Get full capabilities for user's tier
        result = JWTSubscriptionService.get_user_capabilities(request.user)

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'get capabilities', request.user.id
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_subscription_payment(request):
    """
    Retry payment for a pending_payment subscription

    Use cases:
    - User's USSD session expired (30 min timeout)
    - User closed app without completing payment
    - Network error during payment

    Logic (gem.md principle: Subscription = intent, PaymentIntent = effort):
    1. If active PaymentIntent exists -> return it (resume payment)
    2. If expired -> create new PaymentIntent (retry payment)
    3. NEVER recreates subscription (preserves user intent)

    POST /api/subscriptions/retry-payment/
    {
        "phone_number": "237670123456",
        "provider": "fapshi",  // optional, default: fapshi
        "idempotency_key": "uuid"  // optional
    }

    Returns:
        - If existing valid payment: 200 with existing PaymentIntent details
        - If new payment created: 202 with new PaymentIntent details
    """
    try:
        phone_number = request.data.get('phone_number')
        preferred_provider = request.data.get('provider', 'fapshi')
        idempotency_key = request.data.get('idempotency_key')

        if not phone_number:
            return Response({
                'error': 'phone_number is required for payment'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract client context for fraud detection
        client_context = {
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'locale': request.META.get('HTTP_ACCEPT_LANGUAGE', 'en-CM'),
        }

        result = SubscriptionService.retry_pending_payment(
            user=request.user,
            phone_number=phone_number,
            preferred_provider=preferred_provider,
            idempotency_key=idempotency_key,
            client_context=client_context
        )

        # Determine response status based on result
        if result.get('already_processed'):
            return Response({
                'success': True,
                'already_processed': True,
                'subscription_id': result['subscription_id'],
                'payment_intent_id': result['payment_intent_id'],
                'amount': result['amount'],
                'message': 'Request already processed (idempotency key match)'
            }, status=status.HTTP_200_OK)

        if result.get('existing_payment'):
            return Response({
                'success': True,
                'existing_payment': True,
                'subscription_id': result['subscription_id'],
                'payment_intent_id': result['payment_intent_id'],
                'status': result['status'],
                'amount': result['amount'],
                'expires_at': result['expires_at'],
                'message': result['message']
            }, status=status.HTTP_200_OK)

        # New payment created
        return Response({
            'success': True,
            'subscription_id': result['subscription_id'],
            'payment_intent_id': result['payment_intent_id'],
            'payment_instructions': result.get('payment_instructions'),
            'redirect_url': result.get('redirect_url'),
            'amount': result['amount'],
            'plan': result['plan'],
            'billing_cycle': result['billing_cycle'],
            'billing_phase': result['billing_phase'],
            'cycle_duration_days': result['cycle_duration_days'],
            'retry_count': result.get('retry_count', 1),
            'message': result['message']
        }, status=status.HTTP_202_ACCEPTED)

    except ValidationError as e:
        error_message = e.message if hasattr(e, 'message') else str(e)

        if isinstance(error_message, dict):
            return Response(error_message, status=status.HTTP_409_CONFLICT)

        return Response({
            'error': error_message
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        from ..utils.error_handler import ProductionSafeErrorHandler
        return ProductionSafeErrorHandler.handle_view_error(
            e, 'retry subscription payment', request.user.id
        )
