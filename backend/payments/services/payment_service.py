"""
Payment Service - Main Orchestrator
Facade for all payment operations across the SaaS
Handles subscriptions, domains, themes, checkouts, etc.
"""
import logging
import uuid
from datetime import timedelta
from typing import Dict, Any, Optional
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import (
    PaymentIntent,
    MerchantPaymentMethod,
    TransactionLog,
    EventLog,
    RefundRequest
)
from .registry import registry
from ..adapters.base import PaymentResult

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Main payment service - used across entire SaaS
    Orchestrates payments through different providers for different purposes

    Usage:
        # Create payment
        result = PaymentService.create_payment(
            workspace_id='workspace-123',
            user=user,
            amount=10000,  # 10000 XAF
            currency='XAF',
            purpose='subscription',
            metadata={'plan_tier': 'pro'}
        )

        # Check status
        status = PaymentService.check_payment_status(payment_intent_id)

        # Process refund
        refund = PaymentService.create_refund(payment_intent_id, amount, reason)
    """

    @staticmethod
    def create_payment(
        workspace_id: str,
        user,
        amount: int,
        currency: str,
        purpose: str,
        preferred_provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create payment intent and initiate payment with provider

        Args:
            workspace_id: Workspace/Store ID
            user: Django User instance
            amount: Amount in smallest currency unit (e.g., 10000 for 100.00 XAF)
            currency: Currency code (XAF, USD, EUR)
            purpose: Payment purpose (subscription, domain, theme, checkout)
            preferred_provider: Optional provider name (fapshi, mtn, orange)
            metadata: Additional context data
            idempotency_key: Optional idempotency key (auto-generated if not provided)

        Returns:
            Dict with payment initiation result
        """
        try:
            with transaction.atomic():
                # Generate idempotency key if not provided
                if not idempotency_key:
                    idempotency_key = f"{workspace_id}:{purpose}:{uuid.uuid4().hex[:16]}"

                # Check for existing payment with same idempotency key
                existing_intent = PaymentIntent.objects.filter(
                    idempotency_key=idempotency_key
                ).first()

                if existing_intent:
                    logger.info(f"Returning existing PaymentIntent: {existing_intent.id}")
                    return PaymentService._build_payment_response(existing_intent)

                # Validate amount
                if amount <= 0:
                    return {
                        'success': False,
                        'error': 'Amount must be greater than 0',
                        'error_code': 'invalid_amount'
                    }

                # Select provider
                provider_name = PaymentService._select_provider(
                    workspace_id, preferred_provider, currency
                )

                if not provider_name:
                    return {
                        'success': False,
                        'error': 'No payment provider available for this workspace',
                        'error_code': 'no_provider'
                    }

                # Create PaymentIntent
                payment_intent = PaymentIntent.objects.create(
                    workspace_id=workspace_id,
                    user=user,
                    amount=amount,
                    currency=currency,
                    purpose=purpose,
                    provider_name=provider_name,
                    metadata=metadata or {},
                    idempotency_key=idempotency_key,
                    created_by_user_id=user.id,
                    expires_at=timezone.now() + timedelta(minutes=30),
                    status='created'
                )

                logger.info(f"PaymentIntent created: {payment_intent.id} for {workspace_id}")

                # Get provider adapter
                adapter = PaymentService._get_adapter(workspace_id, provider_name)
                if not adapter:
                    payment_intent.mark_failed('Provider configuration not found')
                    return {
                        'success': False,
                        'error': 'Payment provider not configured',
                        'error_code': 'provider_not_configured'
                    }

                # Call provider to create payment
                try:
                    result: PaymentResult = adapter.create_payment(payment_intent)

                    # Log transaction
                    TransactionLog.objects.create(
                        payment_intent=payment_intent,
                        event_type='payment_created',
                        provider_name=provider_name,
                        provider_response=result.metadata,
                        status=result.status or 'pending'
                    )

                    if not result.success:
                        payment_intent.mark_failed(result.error_message or 'Provider error')
                        return {
                            'success': False,
                            'error': result.error_message or 'Payment initiation failed',
                            'error_code': result.error_code or 'provider_error',
                            'payment_intent_id': str(payment_intent.id)
                        }

                    # Update payment intent with provider details
                    payment_intent.provider_intent_id = result.provider_intent_id
                    payment_intent.status = 'pending'
                    payment_intent.save(update_fields=['provider_intent_id', 'status'])

                    logger.info(f"Payment initiated with {provider_name}: {payment_intent.id}")

                    return {
                        'success': True,
                        'payment_intent_id': str(payment_intent.id),
                        'provider': provider_name,
                        'amount': amount,
                        'currency': currency,
                        'mode': result.mode,
                        'redirect_url': result.redirect_url,
                        'client_token': result.client_token,
                        'qr_code': result.qr_code,
                        'instructions': result.instructions,
                        'expires_at': payment_intent.expires_at.isoformat(),
                        'metadata': result.metadata
                    }

                except Exception as e:
                    logger.error(f"Provider error during payment creation: {e}")
                    payment_intent.mark_failed(f'Provider error: {str(e)}')
                    return {
                        'success': False,
                        'error': 'Payment provider error',
                        'error_code': 'provider_exception',
                        'payment_intent_id': str(payment_intent.id)
                    }

        except Exception as e:
            logger.error(f"Payment creation failed: {e}")
            return {
                'success': False,
                'error': 'Payment creation failed',
                'error_code': 'system_error'
            }

    @staticmethod
    def retry_payment(
        purpose: str,
        reference_id: str,
        workspace_id: str,
        user,
        phone_number: Optional[str] = None,
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retry payment for an existing business intent (subscription, domain, etc.)

        If the latest PaymentIntent is still valid (not expired), returns its details.
        If expired, creates a new PaymentIntent linked to the same reference.

        Thread-safe with race condition protection via database locking.

        Args:
            purpose: Payment purpose (subscription, domain, theme, checkout)
            reference_id: Business object ID (subscription_id, domain_id, etc.)
            workspace_id: Workspace ID
            user: Django User instance
            phone_number: Optional phone number (can be updated on retry)
            preferred_provider: Optional provider name

        Returns:
            Dict with payment retry result
        """
        try:
            with transaction.atomic():
                # Lock row to prevent race conditions (select_for_update)
                # Find latest PaymentIntent for this purpose + reference
                latest_intent = PaymentIntent.objects.select_for_update().filter(
                    workspace_id=workspace_id,
                    purpose=purpose,
                    metadata__reference_id=reference_id
                ).order_by('-created_at').first()

                if not latest_intent:
                    return {
                        'success': False,
                        'error': f'No payment found for {purpose} with reference {reference_id}',
                        'error_code': 'payment_not_found'
                    }

                # Check if latest intent is still valid (not expired and not in final state)
                # Refresh expiry check from DB to avoid stale data
                latest_intent.refresh_from_db()

                if not latest_intent.is_expired and not latest_intent.is_final_state:
                    # Intent still valid - return existing payment details
                    logger.info(f"Reusing valid PaymentIntent: {latest_intent.id}")
                    return PaymentService._build_payment_response(latest_intent)

                # Intent is expired or failed - check if retry already in progress
                # Check if there's a newer pending intent created in last 5 minutes (race condition check)
                recent_pending = PaymentIntent.objects.filter(
                    workspace_id=workspace_id,
                    purpose=purpose,
                    metadata__reference_id=reference_id,
                    status__in=['created', 'pending'],
                    created_at__gte=timezone.now() - timedelta(minutes=5)
                ).exclude(id=latest_intent.id).first()

                if recent_pending and not recent_pending.is_expired:
                    # Another retry already created - return it
                    logger.info(f"Returning recent pending PaymentIntent: {recent_pending.id}")
                    return PaymentService._build_payment_response(recent_pending)

                # Safe to create new intent
                logger.info(f"Creating new PaymentIntent (retry) for {purpose} {reference_id}")

                # Update metadata with new phone number if provided
                new_metadata = latest_intent.metadata.copy()
                new_metadata['reference_id'] = reference_id
                if phone_number:
                    new_metadata['phone_number'] = phone_number

                # Generate idempotency key with timestamp to prevent duplicates
                retry_idempotency_key = f"{workspace_id}:{purpose}:{reference_id}:retry:{int(timezone.now().timestamp())}"

                # Create new payment with same details
                result = PaymentService.create_payment(
                    workspace_id=workspace_id,
                    user=user,
                    amount=latest_intent.amount,
                    currency=latest_intent.currency,
                    purpose=purpose,
                    preferred_provider=preferred_provider or latest_intent.provider_name,
                    metadata=new_metadata,
                    idempotency_key=retry_idempotency_key
                )

                # Link to original payment intent for tracking
                if result.get('success') and result.get('payment_intent_id'):
                    new_intent = PaymentIntent.objects.get(id=result['payment_intent_id'])
                    # Track the first payment in the chain
                    original_id = latest_intent.original_payment_intent_id or latest_intent.id
                    new_intent.original_payment_intent_id = original_id
                    new_intent.retry_count = latest_intent.retry_count + 1
                    new_intent.save(update_fields=['original_payment_intent_id', 'retry_count'])

                    logger.info(
                        f"Payment retry created: {new_intent.id} "
                        f"(retry #{new_intent.retry_count} of original {original_id})"
                    )

                return result

        except Exception as e:
            logger.error(f"Payment retry failed: {e}")
            return {
                'success': False,
                'error': 'Payment retry failed',
                'error_code': 'retry_error'
            }

    @staticmethod
    def check_payment_status(payment_intent_id: str) -> Dict[str, Any]:
        """
        Check payment status from DB ONLY (no provider call)
        Used by frontend polling endpoint

        For provider reconciliation, use reconcile_pending_payment()

        Args:
            payment_intent_id: PaymentIntent ID

        Returns:
            Dict with current payment status from DB
        """
        try:
            payment_intent = PaymentIntent.objects.get(id=payment_intent_id)
            return PaymentService._build_payment_response(payment_intent)

        except PaymentIntent.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found',
                'error_code': 'payment_not_found'
            }

    @staticmethod
    def reconcile_pending_payment(payment_intent_id: str) -> Dict[str, Any]:
        """
        Reconcile pending payment by polling provider directly
        Called ONLY by Celery reconciliation job (webhook fallback)

        This is the ONLY method that polls provider for status updates.
        It triggers business logic if payment succeeded but webhook was missed.

        Args:
            payment_intent_id: PaymentIntent ID to reconcile

        Returns:
            Dict with reconciliation result
        """
        try:
            payment_intent = PaymentIntent.objects.select_for_update().get(id=payment_intent_id)

            # Skip if already in final state
            if payment_intent.is_final_state:
                logger.info(f"Payment {payment_intent.id} already in final state: {payment_intent.status}")
                return {
                    'success': True,
                    'already_final': True,
                    'status': payment_intent.status
                }

            # Check if webhook already processed (idempotency check)
            webhook_received = TransactionLog.objects.filter(
                payment_intent=payment_intent,
                event_type='webhook_received'
            ).exists()

            if webhook_received:
                logger.info(f"Payment {payment_intent.id} already processed by webhook - skipping reconciliation")
                return {
                    'success': True,
                    'webhook_processed': True,
                    'status': payment_intent.status
                }

            # Poll provider for current status
            if not payment_intent.provider_intent_id:
                logger.warning(f"Payment {payment_intent.id} has no provider_intent_id - cannot reconcile")
                return {
                    'success': False,
                    'error': 'No provider transaction ID',
                    'error_code': 'no_provider_id'
                }

            adapter = PaymentService._get_adapter(
                payment_intent.workspace_id,
                payment_intent.provider_name
            )

            if not adapter:
                logger.error(f"No adapter found for {payment_intent.provider_name}")
                return {
                    'success': False,
                    'error': 'Provider adapter not found',
                    'error_code': 'no_adapter'
                }

            try:
                result: PaymentResult = adapter.confirm_payment(
                    payment_intent.provider_intent_id
                )

                # Log reconciliation attempt
                TransactionLog.objects.create(
                    payment_intent=payment_intent,
                    event_type='reconciliation',
                    provider_name=payment_intent.provider_name,
                    provider_response=result.metadata,
                    status=result.status or 'unknown'
                )

                old_status = payment_intent.status

                # Update status and trigger business logic if changed
                if result.status == 'success':
                    payment_intent.mark_success()

                    if old_status != 'success':
                        logger.info(f"Reconciliation: Payment {payment_intent.id} succeeded (webhook missed) - triggering business logic")
                        # Import WebhookRouter to reuse webhook logic (ensures idempotency)
                        from ..webhooks.router import WebhookRouter
                        WebhookRouter._trigger_payment_success(payment_intent)

                        return {
                            'success': True,
                            'reconciled': True,
                            'status': 'success',
                            'old_status': old_status,
                            'message': 'Payment reconciled - webhook was missed'
                        }

                elif result.status in ['failed', 'cancelled']:
                    payment_intent.mark_failed(result.error_message or 'Payment failed')

                    if old_status not in ['failed', 'cancelled']:
                        logger.info(f"Reconciliation: Payment {payment_intent.id} failed")
                        from ..webhooks.router import WebhookRouter
                        WebhookRouter._trigger_payment_failure(payment_intent, result.error_message or 'Payment failed')

                        return {
                            'success': True,
                            'reconciled': True,
                            'status': result.status,
                            'old_status': old_status,
                            'message': 'Payment failed - reconciled'
                        }

                # Status unchanged
                return {
                    'success': True,
                    'reconciled': False,
                    'status': payment_intent.status,
                    'message': 'Status unchanged'
                }

            except Exception as e:
                logger.error(f"Provider reconciliation error for {payment_intent.id}: {e}")
                return {
                    'success': False,
                    'error': f'Provider error: {str(e)}',
                    'error_code': 'provider_error'
                }

        except PaymentIntent.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found',
                'error_code': 'payment_not_found'
            }
        except Exception as e:
            logger.error(f"Reconciliation failed for {payment_intent_id}: {e}")
            return {
                'success': False,
                'error': 'Reconciliation failed',
                'error_code': 'system_error'
            }

    @staticmethod
    def _select_provider(
        workspace_id: str,
        preferred_provider: Optional[str],
        currency: str
    ) -> Optional[str]:
        """
        Select payment provider for workspace

        Priority:
        1. Preferred provider if specified and enabled
        2. First enabled provider that supports currency
        3. System default provider (Fapshi)
        """
        # If preferred provider specified, try to use it
        if preferred_provider:
            method = MerchantPaymentMethod.objects.filter(
                workspace_id=workspace_id,
                provider_name=preferred_provider,
                enabled=True,
                verified=True
            ).first()
            if method:
                return preferred_provider

        # Find any enabled provider
        method = MerchantPaymentMethod.objects.filter(
            workspace_id=workspace_id,
            enabled=True,
            verified=True
        ).first()

        if method:
            return method.provider_name

        # Use system default (Fapshi) if no merchant config
        return 'fapshi'

    @staticmethod
    def _get_adapter(workspace_id: str, provider_name: str):
        """
        Get provider adapter with decrypted config

        Args:
            workspace_id: Workspace ID
            provider_name: Provider name

        Returns:
            Adapter instance or None
        """
        try:
            # Get merchant config (if exists)
            method = MerchantPaymentMethod.objects.filter(
                workspace_id=workspace_id,
                provider_name=provider_name
            ).first()

            if method:
                # Decrypt config (FUTURE: use KMS encryption)
                import json
                config = json.loads(method.config_encrypted) if isinstance(method.config_encrypted, str) else {}

                # If config is empty, use platform credentials (platform-only mode)
                if not config or config == {}:
                    config = PaymentService._get_system_config(provider_name)
            else:
                # No merchant config - use system default config from settings
                config = PaymentService._get_system_config(provider_name)

            # Get adapter from registry
            return registry.get_adapter(provider_name, config)

        except Exception as e:
            logger.error(f"Error getting adapter for {provider_name}: {e}")
            return None

    @staticmethod
    def _get_system_config(provider_name: str) -> Dict[str, Any]:
        """Get system-level provider config from Django settings"""
        from django.conf import settings

        if provider_name == 'fapshi':
            return {
                'api_user': getattr(settings, 'FAPSHI_LIVE_API_USER', ''),
                'api_key': getattr(settings, 'FAPSHI_LIVE_API_KEY', ''),
                'use_sandbox': getattr(settings, 'FAPSHI_USE_SANDBOX', False),
                'sandbox_api_user': getattr(settings, 'FAPSHI_SANDBOX_API_USER', ''),
                'sandbox_api_key': getattr(settings, 'FAPSHI_SANDBOX_API_KEY', ''),
            }
        # Add other providers here
        return {}

    @staticmethod
    def _build_payment_response(payment_intent: PaymentIntent) -> Dict[str, Any]:
        """Build standardized payment response"""
        return {
            'success': True,
            'payment_intent_id': str(payment_intent.id),
            'status': payment_intent.status,
            'amount': payment_intent.amount,
            'currency': payment_intent.currency,
            'provider': payment_intent.provider_name,
            'created_at': payment_intent.created_at.isoformat(),
            'expires_at': payment_intent.expires_at.isoformat(),
            'completed_at': payment_intent.completed_at.isoformat() if payment_intent.completed_at else None,
            'metadata': payment_intent.metadata
        }

    @staticmethod
    def void_payment(payment_intent_id: str, reason: str = 'Cancelled by user') -> Dict[str, Any]:
        """
        Void/cancel a pending payment
        Used when user cancels subscription before payment completes

        Args:
            payment_intent_id: PaymentIntent ID to void
            reason: Cancellation reason

        Returns:
            Dict with void result
        """
        try:
            with transaction.atomic():
                payment_intent = PaymentIntent.objects.select_for_update().get(id=payment_intent_id)

                # Only void pending/created payments
                if payment_intent.status not in ['created', 'pending']:
                    return {
                        'success': False,
                        'error': f'Cannot void payment with status: {payment_intent.status}',
                        'error_code': 'invalid_status_for_void',
                        'current_status': payment_intent.status
                    }

                # Mark as cancelled
                payment_intent.status = 'cancelled'
                payment_intent.completed_at = timezone.now()
                payment_intent.save(update_fields=['status', 'completed_at'])

                # Log transaction
                TransactionLog.objects.create(
                    payment_intent=payment_intent,
                    event_type='payment_voided',
                    provider_name=payment_intent.provider_name,
                    provider_response={'reason': reason},
                    status='cancelled'
                )

                logger.info(f"Payment voided: {payment_intent.id} - Reason: {reason}")

                return {
                    'success': True,
                    'payment_intent_id': str(payment_intent.id),
                    'status': 'cancelled',
                    'message': 'Payment voided successfully'
                }

        except PaymentIntent.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found',
                'error_code': 'payment_not_found'
            }
        except Exception as e:
            logger.error(f"Void payment failed: {e}")
            return {
                'success': False,
                'error': 'Failed to void payment',
                'error_code': 'void_error'
            }

    @staticmethod
    def create_refund(
        payment_intent_id: str,
        amount: int,
        reason: str,
        requested_by
    ) -> Dict[str, Any]:
        """
        Create refund request

        Args:
            payment_intent_id: PaymentIntent to refund
            amount: Amount to refund (in smallest currency unit)
            reason: Refund reason
            requested_by: User requesting refund

        Returns:
            Dict with refund result
        """
        try:
            with transaction.atomic():
                payment_intent = PaymentIntent.objects.get(id=payment_intent_id)

                # Validate payment can be refunded
                if payment_intent.status != 'success':
                    return {
                        'success': False,
                        'error': 'Only successful payments can be refunded',
                        'error_code': 'invalid_status'
                    }

                # Create refund request
                refund_request = RefundRequest.objects.create(
                    payment_intent=payment_intent,
                    amount=amount,
                    reason=reason,
                    requested_by=requested_by,
                    status='requested'
                )

                # Get adapter and process refund
                adapter = PaymentService._get_adapter(
                    payment_intent.workspace_id,
                    payment_intent.provider_name
                )

                if not adapter:
                    refund_request.mark_failed('Provider not configured')
                    return {
                        'success': False,
                        'error': 'Provider not configured',
                        'error_code': 'provider_not_configured'
                    }

                # Check if provider supports refunds
                if not adapter.supports_refunds():
                    refund_request.mark_failed('Provider does not support refunds')
                    return {
                        'success': False,
                        'error': 'Provider does not support refunds',
                        'error_code': 'refunds_not_supported'
                    }

                # Process refund
                try:
                    result = adapter.refund_payment(
                        payment_intent.provider_intent_id,
                        amount,
                        reason
                    )

                    if result.success:
                        refund_request.mark_success(result.provider_refund_id)
                        # Update payment intent if full refund
                        if amount == payment_intent.amount:
                            payment_intent.status = 'refunded'
                            payment_intent.save(update_fields=['status'])

                        return {
                            'success': True,
                            'refund_id': str(refund_request.id),
                            'status': refund_request.status,
                            'amount': amount
                        }
                    else:
                        refund_request.mark_failed(result.error_message or 'Refund failed')
                        return {
                            'success': False,
                            'error': result.error_message or 'Refund failed',
                            'error_code': result.error_code or 'refund_error',
                            'refund_id': str(refund_request.id)
                        }

                except Exception as e:
                    logger.error(f"Refund processing error: {e}")
                    refund_request.mark_failed(str(e))
                    return {
                        'success': False,
                        'error': 'Refund processing error',
                        'error_code': 'provider_exception',
                        'refund_id': str(refund_request.id)
                    }

        except PaymentIntent.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found',
                'error_code': 'payment_not_found'
            }
        except Exception as e:
            logger.error(f"Refund creation failed: {e}")
            return {
                'success': False,
                'error': 'Refund creation failed',
                'error_code': 'system_error'
            }
