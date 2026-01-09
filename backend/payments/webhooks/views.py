"""
Webhook Views
Django views for handling provider webhook callbacks
"""
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator

from .router import WebhookRouter, WebhookSecurityValidator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_http_methods(['POST']), name='dispatch')
class GenericWebhookView(View):
    """
    Generic webhook view that routes to correct provider
    Handles common webhook processing logic
    """

    def post(self, request, provider_name):
        """
        Process webhook from any payment provider

        Args:
            request: Django HttpRequest
            provider_name: Provider identifier from URL (fapshi, mtn, orange, etc.)

        Returns:
            JsonResponse with processing result
        """
        try:
            # Get client IP for security logging
            client_ip = self._get_client_ip(request)

            logger.info(f"Webhook received from {provider_name} (IP: {client_ip})")

            # Security validation
            if not WebhookSecurityValidator.validate_source_ip(client_ip, provider_name):
                logger.warning(f"Webhook from unauthorized IP: {client_ip}")
                return JsonResponse({'error': 'Unauthorized'}, status=401)

            # Parse JSON payload
            try:
                payload = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook from {provider_name}: {e}")
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

            # Extract headers (convert META to dict for provider)
            headers = {
                key: value
                for key, value in request.META.items()
                if key.startswith('HTTP_') or key in ['CONTENT_TYPE', 'CONTENT_LENGTH']
            }

            # Additional security: timestamp validation
            timestamp = payload.get('timestamp')
            if timestamp and not WebhookSecurityValidator.validate_timestamp(timestamp):
                logger.warning(f"Webhook timestamp validation failed from {provider_name}")
                return JsonResponse({'error': 'Invalid timestamp'}, status=400)

            # Rate limiting check
            if not WebhookSecurityValidator.rate_limit_check(provider_name, client_ip):
                logger.warning(f"Webhook rate limit exceeded from {provider_name} ({client_ip})")
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

            # Process webhook through router
            result = WebhookRouter.process_webhook(provider_name, payload, headers)

            if result['success']:
                logger.info(
                    f"Webhook processed successfully: {provider_name} - "
                    f"{result.get('provider_event_id', 'unknown')}"
                )
                return JsonResponse({
                    'status': 'success',
                    'message': result.get('message', 'Webhook processed')
                })
            else:
                logger.error(
                    f"Webhook processing failed: {provider_name} - "
                    f"{result.get('error', 'Unknown error')}"
                )
                return JsonResponse({
                    'status': 'error',
                    'error': result.get('error', 'Processing failed')
                }, status=400)

        except Exception as e:
            logger.error(f"Webhook view error ({provider_name}): {e}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'error': 'Internal server error'
            }, status=500)

    def _get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@csrf_exempt
@require_http_methods(['POST'])
def fapshi_webhook(request):
    """
    Fapshi-specific webhook endpoint
    Delegates to generic webhook view

    URL: /payments/webhooks/fapshi/
    """
    view = GenericWebhookView.as_view()
    return view(request, provider_name='fapshi')


@csrf_exempt
@require_http_methods(['POST'])
def mtn_webhook(request):
    """
    MTN-specific webhook endpoint

    URL: /payments/webhooks/mtn/
    """
    view = GenericWebhookView.as_view()
    return view(request, provider_name='mtn')


@csrf_exempt
@require_http_methods(['POST'])
def orange_webhook(request):
    """
    Orange-specific webhook endpoint

    URL: /payments/webhooks/orange/
    """
    view = GenericWebhookView.as_view()
    return view(request, provider_name='orange')


@csrf_exempt
@require_http_methods(['POST'])
def flutterwave_webhook(request):
    """
    Flutterwave-specific webhook endpoint

    URL: /payments/webhooks/flutterwave/
    """
    view = GenericWebhookView.as_view()
    return view(request, provider_name='flutterwave')


@require_http_methods(['GET'])
def webhook_status(request):
    """
    Webhook system health check
    Returns status of webhook configuration

    URL: /payments/webhooks/status/
    """
    from ..services.registry import registry

    registered_providers = registry.list_providers()

    return JsonResponse({
        'status': 'active',
        'registered_providers': registered_providers,
        'webhook_endpoints': {
            provider: f'/payments/webhooks/{provider}/'
            for provider in registered_providers
        }
    })


@csrf_exempt
@require_http_methods(['POST'])
def test_webhook(request):
    """
    Test webhook endpoint for development
    Only available in DEBUG mode

    URL: /payments/webhooks/test/

    Usage:
        POST /payments/webhooks/test/
        {
            "provider": "fapshi",
            "externalId": "TEST_123",
            "status": "SUCCESSFUL",
            "amount": 10000,
            "transactionId": "FAPSHI_TEST_456"
        }
    """
    from django.conf import settings

    if not settings.DEBUG:
        return JsonResponse({'error': 'Only available in DEBUG mode'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        provider = payload.pop('provider', 'fapshi')

        logger.info(f"Test webhook: {provider}")

        # Process through router
        result = WebhookRouter.process_webhook(provider, payload, {})

        return JsonResponse({
            'test_mode': True,
            'result': result
        })

    except Exception as e:
        logger.error(f"Test webhook error: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)


@require_http_methods(['GET'])
def webhook_logs(request, payment_intent_id):
    """
    Get webhook logs for a specific payment

    URL: /payments/webhooks/logs/<payment_intent_id>/
    """
    from ..models import PaymentIntent, TransactionLog

    try:
        payment_intent = PaymentIntent.objects.get(id=payment_intent_id)

        # Get all webhook logs for this payment
        logs = TransactionLog.objects.filter(
            payment_intent=payment_intent,
            event_type='webhook_received'
        ).order_by('-created_at')

        log_data = [
            {
                'id': str(log.id),
                'provider': log.provider_name,
                'status': log.status,
                'created_at': log.created_at.isoformat(),
                'response': log.provider_response
            }
            for log in logs
        ]

        return JsonResponse({
            'payment_intent_id': str(payment_intent.id),
            'current_status': payment_intent.status,
            'webhook_logs': log_data,
            'total_logs': len(log_data)
        })

    except PaymentIntent.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        logger.error(f"Webhook logs error: {e}")
        return JsonResponse({'error': 'Failed to retrieve logs'}, status=500)
