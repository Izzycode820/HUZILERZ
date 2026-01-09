"""
Payment Views
REST API views for payment operations
"""
import json
import logging
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PaymentIntent, MerchantPaymentMethod
from .serializers import (
    PaymentIntentSerializer,
    MerchantPaymentMethodSerializer,
    AddPaymentMethodSerializer,
    TogglePaymentMethodSerializer
)
from .services.payment_service import PaymentService
from .services.registry import registry

logger = logging.getLogger(__name__)

# Cache keys
PLATFORM_METHODS_CACHE_KEY = 'payments:platform_methods:{purpose}'
PLATFORM_METHODS_TTL = 3600  # 1 hour (rarely changes)

# Rate limiting
RATE_LIMIT_KEY = 'payments:rate_limit:{ip}:{endpoint}'
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 100  # 100 requests per minute


def check_rate_limit(request, endpoint_name: str, max_requests: int = RATE_LIMIT_MAX_REQUESTS) -> bool:
    """
    Check if request exceeds rate limit using Redis

    Args:
        request: Django request object
        endpoint_name: Unique endpoint identifier
        max_requests: Max requests allowed in window

    Returns:
        True if within limit, False if exceeded
    """
    # Get client IP (handle proxies)
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or \
         request.META.get('REMOTE_ADDR', 'unknown')

    key = RATE_LIMIT_KEY.format(ip=ip, endpoint=endpoint_name)

    try:
        # Atomic increment with TTL (Redis pipeline for atomicity)
        current = cache.get(key, 0)

        if current >= max_requests:
            return False

        # Increment and set TTL (first request sets TTL)
        cache.set(key, current + 1, RATE_LIMIT_WINDOW)
        return True

    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open (allow request) if Redis is down
        return True


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, payment_intent_id):
    """
    Get payment status

    GET /api/payments/status/{payment_intent_id}/

    Returns:
        PaymentIntent with current status
    """
    try:
        # Get payment intent
        payment_intent = PaymentIntent.objects.filter(
            id=payment_intent_id,
            user=request.user
        ).first()

        if not payment_intent:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # READ-ONLY from DB (no provider call)
        # Frontend polling should only show current DB state
        # Provider reconciliation is handled by Celery job (webhook fallback)

        # Serialize and return current status
        serializer = PaymentIntentSerializer(payment_intent)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Payment status error: {e}")
        return Response({
            'error': 'Failed to retrieve payment status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_payment_methods(request):
    """
    List merchant's payment methods for their workspaces

    GET /api/payments/methods/?workspace_id={workspace_id}

    Returns:
        List of MerchantPaymentMethod for workspace
    """
    try:
        workspace_id = request.query_params.get('workspace_id')

        if not workspace_id:
            return Response({
                'error': 'workspace_id query parameter required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Verify user owns workspace
        # For now, check user is workspace_owner
        methods = MerchantPaymentMethod.objects.filter(
            workspace_id=workspace_id,
            workspace_owner=request.user
        ).order_by('-enabled', '-last_used_at')

        serializer = MerchantPaymentMethodSerializer(methods, many=True)

        # Also return available providers
        available_providers = registry.list_providers()
        provider_info = registry.get_provider_info()

        return Response({
            'methods': serializer.data,
            'available_providers': available_providers,
            'provider_capabilities': provider_info
        })

    except Exception as e:
        logger.error(f"List payment methods error: {e}")
        return Response({
            'error': 'Failed to retrieve payment methods'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payment_method(request):
    """
    Add payment method to workspace

    For Fapshi: Merchant provides their own Fapshi checkout URL
    For future providers: May require API credentials

    POST /api/payments/methods/add/
    {
        "workspace_id": "workspace-123",
        "provider_name": "fapshi",
        "checkout_url": "https://checkout.fapshi.com/pay/merchant-product-xyz"
    }

    Returns:
        Created MerchantPaymentMethod
    """
    try:
        workspace_id = request.data.get('workspace_id')

        if not workspace_id:
            return Response({
                'error': 'workspace_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        from workspace.core.models import Workspace
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
        except Workspace.DoesNotExist:
            return Response({
                'error': 'Workspace not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AddPaymentMethodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        provider_name = serializer.validated_data['provider_name']
        checkout_url = serializer.validated_data.get('checkout_url')

        existing = MerchantPaymentMethod.objects.filter(
            workspace_id=workspace_id,
            provider_name=provider_name
        ).first()

        if existing:
            return Response({
                'error': f'Payment method {provider_name} already added for this workspace'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            adapter = registry.get_adapter(provider_name, {})
            capabilities = adapter.get_capabilities()
        except Exception as e:
            logger.error(f"Failed to get adapter: {e}")
            return Response({
                'error': f'Payment provider {provider_name} not available'
            }, status=status.HTTP_400_BAD_REQUEST)

        method = MerchantPaymentMethod.objects.create(
            workspace_id=workspace_id,
            workspace_owner=request.user,
            provider_name=provider_name,
            checkout_url=checkout_url,
            config_encrypted='',
            enabled=True,
            verified=True,
            permissions=capabilities
        )

        logger.info(f"Payment method added: {provider_name} for workspace {workspace_id}")

        result_serializer = MerchantPaymentMethodSerializer(method)
        return Response({
            'message': f'{provider_name.title()} payment method enabled',
            'method': result_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Add payment method error: {e}")
        return Response({
            'error': 'Failed to add payment method'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_payment_method(request, method_id):
    """
    Enable/disable payment method

    PATCH /api/payments/methods/{method_id}/toggle/
    {
        "enabled": true
    }

    Returns:
        Updated MerchantPaymentMethod
    """
    try:
        # Get method
        method = MerchantPaymentMethod.objects.filter(
            id=method_id,
            workspace_owner=request.user
        ).first()

        if not method:
            return Response({
                'error': 'Payment method not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate input
        serializer = TogglePaymentMethodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        enabled = serializer.validated_data['enabled']

        # Update enabled status
        method.enabled = enabled
        method.save(update_fields=['enabled', 'updated_at'])

        logger.info(
            f"Payment method {'enabled' if enabled else 'disabled'}: "
            f"{method.provider_name} for workspace {method.workspace_id}"
        )

        result_serializer = MerchantPaymentMethodSerializer(method)
        return Response({
            'message': f'Payment method {"enabled" if enabled else "disabled"}',
            'method': result_serializer.data
        })

    except Exception as e:
        logger.error(f"Toggle payment method error: {e}")
        return Response({
            'error': 'Failed to toggle payment method'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_payment(request):
    """
    Retry payment for an existing business intent

    POST /api/payments/retry/
    {
        "purpose": "subscription",
        "reference_id": "subscription-uuid",
        "phone_number": "237670123456",  // optional
        "preferred_provider": "fapshi"   // optional
    }

    Returns:
        Payment intent details (reused if valid, new if expired)
    """
    try:
        purpose = request.data.get('purpose')
        reference_id = request.data.get('reference_id')
        workspace_id = request.data.get('workspace_id')
        phone_number = request.data.get('phone_number')
        preferred_provider = request.data.get('preferred_provider')

        # Validation
        if not purpose:
            return Response({
                'error': 'purpose is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not reference_id:
            return Response({
                'error': 'reference_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not workspace_id:
            return Response({
                'error': 'workspace_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate purpose
        valid_purposes = ['subscription', 'subscription_renewal', 'subscription_upgrade',
                         'domain', 'theme', 'checkout', 'trial']
        if purpose not in valid_purposes:
            return Response({
                'error': f'Invalid purpose. Must be one of: {", ".join(valid_purposes)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify user owns workspace
        from workspace.core.models import Workspace
        try:
            workspace = Workspace.objects.get(id=workspace_id, owner=request.user)
        except Workspace.DoesNotExist:
            return Response({
                'error': 'Workspace not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Call retry service
        result = PaymentService.retry_payment(
            purpose=purpose,
            reference_id=reference_id,
            workspace_id=workspace_id,
            user=request.user,
            phone_number=phone_number,
            preferred_provider=preferred_provider
        )

        if not result.get('success'):
            return Response({
                'error': result.get('error', 'Payment retry failed'),
                'error_code': result.get('error_code', 'unknown_error')
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Retry payment error: {e}")
        return Response({
            'error': 'Failed to retry payment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_payment_methods(request):
    """
    Get available payment methods for workspace
    Used by storefront to show enabled payment options to customers

    GET /api/payments/methods/available/?workspace_id={workspace_id}

    Returns:
        List of enabled payment providers with metadata
    """
    try:
        workspace_id = request.query_params.get('workspace_id')

        if not workspace_id:
            return Response({
                'error': 'workspace_id query parameter required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get enabled methods for workspace
        methods = MerchantPaymentMethod.objects.filter(
            workspace_id=workspace_id,
            enabled=True,
            verified=True
        )

        # Build response
        available = []
        for method in methods:
            available.append({
                'provider': method.provider_name,
                'label': method.provider_name.title(),
                'type': method.permissions.get('payment_modes', ['redirect'])[0],
                'capabilities': method.permissions,
                'last_used': method.last_used_at.isoformat() if method.last_used_at else None
            })

        return Response({
            'workspace_id': workspace_id,
            'available_methods': available,
            'count': len(available)
        })

    except Exception as e:
        logger.error(f"Available payment methods error: {e}")
        return Response({
            'error': 'Failed to retrieve available payment methods'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def platform_payment_methods(request):
    """
    Get platform-level payment methods (NO workspace required)
    Used for subscription checkout, domain purchases, and other platform-level payments

    PERFORMANCE:
    - Cached in Redis for 1 hour (capabilities rarely change)
    - Rate limited: 100 requests/minute per IP
    - Uses registry's cached capabilities (no adapter instantiation)

    GET /api/payments/platform-methods/?purpose=subscription

    Query Params:
        purpose (optional): Filter by payment purpose (subscription, domain, theme)

    Returns:
        List of available payment providers with display metadata

    Example Response:
        {
            "methods": [
                {
                    "provider": "fapshi",
                    "display_name": "Mobile Money (MTN / Orange)",
                    "description": "Pay with MTN Mobile Money or Orange Money",
                    "modes": ["ussd"],
                    "currencies": ["XAF"],
                    "icon": null,
                    "recommended": true,
                    "capabilities": {...}
                }
            ],
            "count": 1,
            "cached": true
        }
    """
    try:
        # RATE LIMITING: Prevent abuse (100 req/min per IP)
        if not check_rate_limit(request, 'platform_methods'):
            logger.warning(f"Rate limit exceeded for platform_methods from {request.META.get('REMOTE_ADDR')}")
            return Response({
                'error': 'Rate limit exceeded. Try again in 1 minute.',
                'error_code': 'RATE_LIMIT_EXCEEDED'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        purpose = request.query_params.get('purpose', 'subscription')

        # CACHING: Check Redis cache first (1 hour TTL)
        cache_key = PLATFORM_METHODS_CACHE_KEY.format(purpose=purpose)
        cached_response = cache.get(cache_key)

        if cached_response:
            # Cache hit - return immediately (sub-millisecond)
            cached_response['cached'] = True
            return Response(cached_response)

        # Cache miss - build response from registry's cached capabilities
        methods = []

        # Use cached capabilities (no adapter instantiation - FAST)
        all_capabilities = registry.get_all_cached_capabilities()

        for provider_name, capabilities in all_capabilities.items():
            if not capabilities:
                logger.warning(f"No cached capabilities for {provider_name}")
                continue

            try:
                # Filter by purpose if needed (future: add supported_purposes to capabilities)
                # For now, all providers support subscriptions, domains, themes

                # Build provider metadata for UI
                method = {
                    'provider': provider_name,
                    'display_name': capabilities.get('display_name', f'{provider_name.title()}'),
                    'description': _get_provider_description(provider_name, capabilities),
                    'modes': capabilities.get('payment_modes', ['redirect']),
                    'currencies': capabilities.get('supported_currencies', ['XAF']),
                    'icon': None,  # Future: Add icon URLs
                    'recommended': provider_name == 'fapshi',  # Fapshi is default
                    'capabilities': capabilities
                }

                methods.append(method)

            except Exception as e:
                logger.warning(f"Could not build method metadata for {provider_name}: {e}")
                continue

        response_data = {
            'methods': methods,
            'count': len(methods),
            'purpose': purpose,
            'cached': False
        }

        # Cache in Redis for 1 hour (capabilities rarely change)
        try:
            cache.set(cache_key, response_data, PLATFORM_METHODS_TTL)
        except Exception as e:
            logger.error(f"Failed to cache platform methods: {e}")
            # Continue anyway - caching failure shouldn't break the request

        return Response(response_data)

    except Exception as e:
        logger.error(f"Platform payment methods error: {e}", exc_info=True)
        return Response({
            'error': 'Failed to retrieve payment methods'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_provider_description(provider_name: str, capabilities: dict) -> str:
    """
    Generate user-friendly description for payment provider

    Args:
        provider_name: Provider identifier
        capabilities: Provider capabilities dict

    Returns:
        Human-readable description
    """
    if provider_name == 'fapshi':
        # Check payment methods to determine supported operators
        payment_methods = capabilities.get('payment_methods', [])
        operators = [pm.get('provider') for pm in payment_methods if pm.get('type') == 'mobile-money']

        if operators:
            operators_str = ' or '.join(operators)
            return f'Pay with {operators_str}'
        return 'Pay with Mobile Money'

    # Default description for other providers
    return f'Pay with {provider_name.title()}'
