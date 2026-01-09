"""
Trial Views - Webhook-Driven Pattern
Aligned with TrialService for consistency
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
import logging

from ..models import Trial, SubscriptionPlan
from ..models.trial import TRIAL_PRICES
from ..services.trial_service import TrialService
from ..utils.error_handler import ProductionSafeErrorHandler

logger = logging.getLogger(__name__)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_trial(request):
    """
    Initiate trial creation (webhook-driven pattern)
    Returns PaymentIntent for USSD payment completion
    """
    try:
        plan_tier = request.data.get('tier')
        workspace_id = request.data.get('workspace_id')
        phone_number = request.data.get('phone_number')
        preferred_provider = request.data.get('provider', 'fapshi')

        if not plan_tier:
            return Response({
                'error': 'tier is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            return Response({
                'error': 'phone_number is required for payment'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get workspace if provided
        workspace = None
        if workspace_id:
            try:
                from workspace.core.models import Workspace
                workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
            except:
                return Response({
                    'error': 'Workspace not found'
                }, status=status.HTTP_404_NOT_FOUND)

        result = TrialService.initiate_trial(
            user=request.user,
            plan_tier=plan_tier,
            phone_number=phone_number,
            workspace=workspace,
            preferred_provider=preferred_provider
        )

        return Response({
            'success': True,
            'trial_id': result['trial_id'],
            'payment_intent_id': result['payment_intent_id'],
            'payment_instructions': result.get('payment_instructions'),
            'redirect_url': result.get('redirect_url'),
            'amount': result['amount'],
            'tier': result['tier'],
            'duration_days': result['duration_days'],
            'message': f'Complete USSD payment to activate {plan_tier} trial (28 days)'
        }, status=status.HTTP_202_ACCEPTED)

    except ValidationError as e:
        error_message = e.message if hasattr(e, 'message') else str(e)

        if isinstance(error_message, dict):
            return Response(error_message, status=status.HTTP_409_CONFLICT)

        return Response({
            'error': error_message
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error creating trial for user {request.user.id}: {str(e)}")
        return ProductionSafeErrorHandler.safe_error_response(
            e, 'create trial'
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_trial(request):
    """
    Convert trial to paid subscription
    User can choose ANY tier (even lower than trial tier)
    """
    try:
        trial_id = request.data.get('trial_id')
        target_tier = request.data.get('target_tier')
        phone_number = request.data.get('phone_number')
        preferred_provider = request.data.get('provider', 'fapshi')

        if not trial_id:
            return Response({
                'error': 'trial_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not target_tier:
            return Response({
                'error': 'target_tier is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number:
            return Response({
                'error': 'phone_number is required for payment'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = TrialService.convert_trial_to_subscription(
            user=request.user,
            trial_id=trial_id,
            target_tier=target_tier,
            phone_number=phone_number,
            preferred_provider=preferred_provider
        )

        return Response({
            'success': True,
            'trial_id': result['trial_id'],
            'trial_tier': result['trial_tier'],
            'subscription_tier': result['subscription_tier'],
            'subscription_payment_intent_id': result['subscription_payment_intent_id'],
            'payment_instructions': result.get('payment_instructions'),
            'redirect_url': result.get('redirect_url'),
            'amount': result['amount'],
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
        logger.error(f"Error converting trial for user {request.user.id}: {str(e)}")
        return ProductionSafeErrorHandler.safe_error_response(
            e, 'convert trial'
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_trial(request):
    """
    Cancel active trial immediately
    """
    try:
        trial_id = request.data.get('trial_id')
        reason = request.data.get('reason', 'user_requested')

        if not trial_id:
            return Response({
                'error': 'trial_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = TrialService.cancel_trial(
            user=request.user,
            trial_id=trial_id,
            reason=reason
        )

        return Response({
            'success': True,
            'trial_id': result['trial_id'],
            'status': result['status'],
            'reason': result['reason']
        }, status=status.HTTP_200_OK)

    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error cancelling trial for user {request.user.id}: {str(e)}")
        return ProductionSafeErrorHandler.safe_error_response(
            e, 'cancel trial'
        )

