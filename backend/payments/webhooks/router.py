"""
Webhook Router
Routes incoming webhooks to correct payment provider
Handles webhook processing, idempotency, and business logic triggers
"""
import logging
from typing import Dict, Any
from django.db import transaction
from django.utils import timezone

from ..models import PaymentIntent, EventLog, TransactionLog
from ..services.registry import registry

logger = logging.getLogger(__name__)


class WebhookRouter:
    """
    Central webhook routing and processing system

    Responsibilities:
    1. Route webhooks to correct provider adapter
    2. Ensure idempotency (prevent duplicate processing)
    3. Update PaymentIntent status
    4. Log all webhook events
    5. Trigger business logic on payment completion
    """

    @staticmethod
    def process_webhook(
        provider_name: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process incoming webhook from payment provider

        Args:
            provider_name: Provider identifier (fapshi, mtn, orange, etc.)
            payload: Raw webhook JSON payload
            headers: HTTP headers from webhook request

        Returns:
            Dict with processing result
        """
        try:
            # Get provider adapter
            if not registry.is_registered(provider_name):
                logger.error(f"Unknown provider in webhook: {provider_name}")
                return {
                    'success': False,
                    'error': f'Unknown provider: {provider_name}',
                    'error_code': 'unknown_provider'
                }

            # Get adapter with empty config (will use system config)
            adapter = registry.get_adapter(provider_name, {})

            # Parse webhook using provider adapter
            try:
                webhook_event = adapter.parse_webhook(payload, headers)
            except ValueError as e:
                logger.error(f"Webhook parsing error ({provider_name}): {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'error_code': 'invalid_webhook'
                }

            logger.info(
                f"Webhook received: {provider_name} - "
                f"{webhook_event.provider_event_id} - "
                f"{webhook_event.status}"
            )

            # Check idempotency - prevent duplicate processing
            with transaction.atomic():
                event_log, created = EventLog.objects.get_or_create(
                    provider_event_id=webhook_event.provider_event_id,
                    defaults={
                        'provider_name': provider_name,
                        'payload': webhook_event.raw_payload,
                        'processed': False
                    }
                )

                if not created and event_log.processed:
                    logger.info(f"Webhook already processed: {webhook_event.provider_event_id}")
                    return {
                        'success': True,
                        'message': 'Webhook already processed (idempotent)',
                        'duplicate': True
                    }

                # Find PaymentIntent by provider_intent_id
                payment_intent = PaymentIntent.objects.filter(
                    provider_intent_id=webhook_event.provider_intent_id
                ).first()

                # Fallback: Try finding by external_id in metadata (provider often sends this back)
                if not payment_intent and webhook_event.metadata.get('external_id'):
                    external_id = webhook_event.metadata.get('external_id')
                    payment_intent = PaymentIntent.objects.filter(
                        metadata__external_reference=external_id
                    ).first()
                    
                    if payment_intent:
                        logger.info(f"PaymentIntent found via external_id: {external_id}")

                if not payment_intent:
                    logger.warning(
                        f"PaymentIntent not found for webhook: "
                        f"{webhook_event.provider_intent_id} (External ID: {webhook_event.metadata.get('external_id')})"
                    )
                    # Mark event as processed anyway to prevent retries
                    event_log.mark_processed()
                    return {
                        'success': False,
                        'error': 'Payment not found',
                        'error_code': 'payment_not_found'
                    }

                # Log transaction
                TransactionLog.objects.create(
                    payment_intent=payment_intent,
                    event_type='webhook_received',
                    provider_name=provider_name,
                    provider_response=webhook_event.raw_payload,
                    status=webhook_event.status,
                    request_metadata={
                        'headers': headers,
                        'provider_event_id': webhook_event.provider_event_id
                    }
                )

                # Update PaymentIntent status based on webhook
                old_status = payment_intent.status

                if webhook_event.status == 'success':
                    payment_intent.mark_success(webhook_event.provider_intent_id)
                    logger.info(f"Payment completed: {payment_intent.id}")

                    # Trigger business logic (async recommended)
                    WebhookRouter._trigger_payment_success(payment_intent)

                elif webhook_event.status in ['failed', 'cancelled']:
                    failure_reason = webhook_event.metadata.get('message', f'Payment {webhook_event.status}')
                    payment_intent.mark_failed(failure_reason)
                    logger.info(f"Payment failed: {payment_intent.id} - {failure_reason}")

                    # Trigger failure logic if needed
                    WebhookRouter._trigger_payment_failure(payment_intent, failure_reason)

                elif webhook_event.status == 'pending':
                    # Still pending - update timestamp but keep status
                    payment_intent.updated_at = timezone.now()
                    payment_intent.save(update_fields=['updated_at'])
                    logger.info(f"Payment still pending: {payment_intent.id}")

                # Mark event as processed
                event_log.mark_processed()

                logger.info(
                    f"Webhook processed successfully: "
                    f"{webhook_event.provider_event_id} - "
                    f"{old_status} -> {payment_intent.status}"
                )

                return {
                    'success': True,
                    'message': 'Webhook processed successfully',
                    'payment_intent_id': str(payment_intent.id),
                    'old_status': old_status,
                    'new_status': payment_intent.status,
                    'provider_event_id': webhook_event.provider_event_id
                }

        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Internal webhook processing error',
                'error_code': 'processing_error'
            }

    @staticmethod
    def _trigger_payment_success(payment_intent: PaymentIntent):
        """
        Trigger business logic on successful payment

        This is where you call:
        - Subscription activation
        - Domain purchase completion
        - Theme purchase fulfillment
        - Store checkout order creation

        Args:
            payment_intent: Completed PaymentIntent
        """
        purpose = payment_intent.purpose
        metadata = payment_intent.metadata

        logger.info(f"Triggering payment success logic for: {purpose}")

        try:
            # Route to appropriate business logic based on purpose
            if purpose in ['subscription', 'subscription_renewal', 'subscription_upgrade']:
                WebhookRouter._handle_subscription_payment(payment_intent)

            elif purpose == 'trial':
                WebhookRouter._handle_trial_payment(payment_intent)

            elif purpose == 'domain':
                WebhookRouter._handle_domain_purchase(payment_intent)

            elif purpose == 'domain_renewal':
                WebhookRouter._handle_domain_renewal(payment_intent)

            elif purpose == 'theme':
                WebhookRouter._handle_theme_purchase(payment_intent)

            elif purpose == 'checkout':
                WebhookRouter._handle_checkout_payment(payment_intent)

            else:
                logger.warning(f"Unknown payment purpose: {purpose}")

        except Exception as e:
            logger.error(f"Business logic trigger error: {e}", exc_info=True)
            # Don't fail webhook processing if business logic fails
            # Business logic should have its own retry mechanism

    @staticmethod
    def _trigger_payment_failure(payment_intent: PaymentIntent, reason: str):
        """
        Trigger business logic on payment failure

        Args:
            payment_intent: Failed PaymentIntent
            reason: Failure reason
        """
        purpose = payment_intent.purpose
        logger.info(f"Triggering payment failure logic for: {purpose} - {reason}")

        try:
            # Route to appropriate failure handler based on purpose
            if purpose in ['subscription', 'subscription_renewal', 'subscription_upgrade']:
                from subscription.services.subscription_service import SubscriptionService
                SubscriptionService.handle_payment_failure(payment_intent)

            elif purpose == 'domain':
                WebhookRouter._handle_domain_purchase_failure(payment_intent, reason)

            elif purpose == 'domain_renewal':
                WebhookRouter._handle_domain_renewal_failure(payment_intent, reason)

            elif purpose in ['theme', 'checkout', 'trial']:
                logger.warning(f"No failure handler implemented for purpose: {purpose}")

            else:
                logger.warning(f"Unknown payment purpose for failure: {purpose}")

        except Exception as e:
            logger.error(f"Failure logic trigger error: {e}", exc_info=True)

    # Business logic handlers (stubs - implement based on your needs)

    @staticmethod
    def _handle_subscription_payment(payment_intent: PaymentIntent):
        """Handle subscription payment completion"""
        logger.info(f"Subscription payment completed: {payment_intent.id}")

        try:
            # Import subscription webhook handler
            from subscription.webhooks import handle_subscription_payment_webhook

            # Delegate to subscription module
            result = handle_subscription_payment_webhook(payment_intent)

            if result['success']:
                logger.info(f"Subscription activated successfully: {result.get('subscription_id')}")
            else:
                logger.error(f"Failed to activate subscription: {result.get('error')}")

        except ImportError as e:
            logger.error(f"Failed to import subscription webhook handler: {e}")
        except Exception as e:
            logger.error(f"Subscription activation error: {e}", exc_info=True)

    @staticmethod
    def _handle_trial_payment(payment_intent: PaymentIntent):
        """
        Handle trial payment completion
        Activates trial via TrialService (idempotent)
        """
        logger.info(f"Trial payment completed: {payment_intent.id}")

        try:
            from subscription.services.trial_service import TrialService

            result = TrialService.activate_trial_from_payment(payment_intent)

            if result['success']:
                logger.info(
                    f"Trial activated successfully: {result.get('trial_id')} - "
                    f"Tier: {result.get('tier')}, Expires: {result.get('expires_at')}"
                )
            else:
                logger.error(
                    f"Trial activation failed for PaymentIntent {payment_intent.id}: "
                    f"{result.get('error')}"
                )

        except Exception as e:
            logger.error(
                f"Trial payment handling failed for {payment_intent.id}: {str(e)}",
                exc_info=True
            )

    @staticmethod
    def _handle_domain_purchase(payment_intent: PaymentIntent):
        """
        Handle domain purchase payment completion
        Triggers Celery task to purchase from GoDaddy
        IDEMPOTENT: Safe to call multiple times
        """
        logger.info(f"Domain purchase payment completed: {payment_intent.id}")

        try:
            from workspace.hosting.models import DomainPurchase
            from subscription.models import PaymentRecord

            purchase_id = payment_intent.metadata.get('purchase_id')
            if not purchase_id:
                logger.error(f"PaymentIntent {payment_intent.id} missing purchase_id in metadata")
                return

            # IDEMPOTENCY: Check if already processed
            existing_payment_record = PaymentRecord.objects.filter(payment_intent=payment_intent).first()
            if existing_payment_record:
                logger.info(f"Domain purchase payment already processed: {purchase_id} (idempotent)")
                return

            # Get DomainPurchase record with locking
            domain_purchase = DomainPurchase.objects.select_for_update().select_related(
                'custom_domain', 'user'
            ).get(id=purchase_id)

            # Validate status
            if domain_purchase.payment_status not in ['pending', 'pending_payment']:
                logger.warning(
                    f"Domain purchase payment webhook for non-pending purchase: {purchase_id} "
                    f"(status: {domain_purchase.payment_status})"
                )
                return

            with transaction.atomic():
                # Mark payment received and status as processing
                domain_purchase.mark_payment_received(payment_intent.provider_intent_id)
                domain_purchase.payment_provider = payment_intent.provider_name
                domain_purchase.save(update_fields=['payment_provider', 'updated_at'])

                # Create PaymentRecord for idempotency
                PaymentRecord.objects.create(
                    user=domain_purchase.user,
                    payment_intent=payment_intent,
                    amount=payment_intent.amount,
                    reference=payment_intent.provider_intent_id or '',
                    momo_operator=payment_intent.metadata.get('momo_operator', ''),
                    momo_phone_used=payment_intent.metadata.get('phone_number', ''),
                    transaction_id=payment_intent.provider_intent_id or '',
                    raw_webhook_payload=payment_intent.metadata,
                    status='success'
                )

                logger.info(
                    f"Payment confirmed for domain purchase {purchase_id}: "
                    f"{payment_intent.provider_intent_id} via {payment_intent.provider_name}"
                )

                # Trigger async domain purchase from registrar via Celery
                from workspace.hosting.tasks.domain_tasks import process_domain_purchase
                process_domain_purchase.apply_async(
                    args=[str(purchase_id)],
                    countdown=5
                )

                logger.info(f"Celery task queued for domain purchase: {purchase_id}")

        except Exception as e:
            logger.error(
                f"Domain purchase payment handling failed for {payment_intent.id}: {str(e)}",
                exc_info=True
            )

    @staticmethod
    def _handle_domain_renewal(payment_intent: PaymentIntent):
        """
        Handle domain renewal payment completion
        Triggers Celery task to renew with GoDaddy
        IDEMPOTENT: Safe to call multiple times
        """
        logger.info(f"Domain renewal payment completed: {payment_intent.id}")

        try:
            from workspace.hosting.models import DomainRenewal
            from subscription.models import PaymentRecord

            renewal_id = payment_intent.metadata.get('renewal_id')
            if not renewal_id:
                logger.error(f"PaymentIntent {payment_intent.id} missing renewal_id in metadata")
                return

            # IDEMPOTENCY: Check if already processed
            existing_payment_record = PaymentRecord.objects.filter(payment_intent=payment_intent).first()
            if existing_payment_record:
                logger.info(f"Domain renewal payment already processed: {renewal_id} (idempotent)")
                return

            # Get DomainRenewal record with locking
            domain_renewal = DomainRenewal.objects.select_for_update().select_related(
                'custom_domain', 'user'
            ).get(id=renewal_id)

            # Validate status
            if domain_renewal.renewal_status not in ['pending_payment', 'pending']:
                logger.warning(
                    f"Domain renewal payment webhook for non-pending renewal: {renewal_id} "
                    f"(status: {domain_renewal.renewal_status})"
                )
                return

            with transaction.atomic():
                # Mark payment received and status as processing
                domain_renewal.mark_payment_received(payment_intent.provider_intent_id)
                domain_renewal.payment_provider = payment_intent.provider_name
                domain_renewal.save(update_fields=['payment_provider', 'updated_at'])

                # Create PaymentRecord for idempotency
                PaymentRecord.objects.create(
                    user=domain_renewal.user,
                    payment_intent=payment_intent,
                    amount=payment_intent.amount,
                    reference=payment_intent.provider_intent_id or '',
                    momo_operator=payment_intent.metadata.get('momo_operator', ''),
                    momo_phone_used=payment_intent.metadata.get('phone_number', ''),
                    transaction_id=payment_intent.provider_intent_id or '',
                    raw_webhook_payload=payment_intent.metadata,
                    status='success'
                )

                logger.info(
                    f"Payment confirmed for domain renewal {renewal_id}: "
                    f"{payment_intent.provider_intent_id} via {payment_intent.provider_name}"
                )

                # Trigger async domain renewal with registrar via Celery
                from workspace.hosting.tasks.domain_tasks import process_domain_renewal
                process_domain_renewal.apply_async(
                    args=[str(renewal_id)],
                    countdown=5
                )

                logger.info(f"Celery task queued for domain renewal: {renewal_id}")

        except Exception as e:
            logger.error(
                f"Domain renewal payment handling failed for {payment_intent.id}: {str(e)}",
                exc_info=True
            )

    @staticmethod
    def _handle_domain_purchase_failure(payment_intent: PaymentIntent, reason: str):
        """
        Handle domain purchase payment failure
        Marks DomainPurchase and CustomDomain as failed
        """
        logger.info(f"Domain purchase payment failed: {payment_intent.id} - {reason}")

        try:
            from workspace.hosting.models import DomainPurchase

            purchase_id = payment_intent.metadata.get('purchase_id')
            if not purchase_id:
                logger.error(f"PaymentIntent {payment_intent.id} missing purchase_id in metadata")
                return

            domain_purchase = DomainPurchase.objects.select_related('custom_domain').get(id=purchase_id)

            with transaction.atomic():
                # Mark purchase as failed
                domain_purchase.mark_failed(reason)

                # Mark CustomDomain as failed
                custom_domain = domain_purchase.custom_domain
                custom_domain.status = 'failed'
                custom_domain.save(update_fields=['status', 'updated_at'])

                logger.info(f"Marked domain purchase {purchase_id} as failed: {reason}")

        except Exception as e:
            logger.error(
                f"Domain purchase failure handling failed for {payment_intent.id}: {str(e)}",
                exc_info=True
            )

    @staticmethod
    def _handle_domain_renewal_failure(payment_intent: PaymentIntent, reason: str):
        """
        Handle domain renewal payment failure
        Marks DomainRenewal as failed, keeps CustomDomain in current state
        """
        logger.info(f"Domain renewal payment failed: {payment_intent.id} - {reason}")

        try:
            from workspace.hosting.models import DomainRenewal

            renewal_id = payment_intent.metadata.get('renewal_id')
            if not renewal_id:
                logger.error(f"PaymentIntent {payment_intent.id} missing renewal_id in metadata")
                return

            domain_renewal = DomainRenewal.objects.select_related('custom_domain').get(id=renewal_id)

            with transaction.atomic():
                # Mark renewal as failed
                domain_renewal.mark_failed(reason)

                logger.info(
                    f"Marked domain renewal {renewal_id} as failed: {reason}. "
                    f"Domain {domain_renewal.domain_name} remains in current state."
                )

        except Exception as e:
            logger.error(
                f"Domain renewal failure handling failed for {payment_intent.id}: {str(e)}",
                exc_info=True
            )

    @staticmethod
    def _handle_theme_purchase(payment_intent: PaymentIntent):
        """Handle theme purchase completion"""
        logger.info(f"Theme purchase completed: {payment_intent.id}")

        # TODO: Grant theme access to workspace
        logger.info(
            f"TODO: Grant theme access to workspace {payment_intent.workspace_id}"
        )

    @staticmethod
    def _handle_checkout_payment(payment_intent: PaymentIntent):
        """Handle store checkout payment completion"""
        logger.info(f"Checkout payment completed: {payment_intent.id}")

        # TODO: Create order, reduce inventory, notify merchant & buyer
        logger.info(
            f"TODO: Create order for workspace {payment_intent.workspace_id}"
        )


class WebhookSecurityValidator:
    """
    Security validation for webhooks
    Additional layer before routing
    """

    @staticmethod
    def validate_source_ip(ip_address: str, provider_name: str) -> bool:
        """
        Validate webhook source IP against provider allowlist

        Args:
            ip_address: Source IP of webhook request
            provider_name: Provider name

        Returns:
            True if IP allowed, False otherwise
        """
        # TODO: Implement IP allowlisting per provider
        # For now, allow all (configure in production)

        logger.debug(f"Webhook from IP {ip_address} for provider {provider_name}")
        return True

    @staticmethod
    def validate_timestamp(timestamp: str) -> bool:
        """
        Validate webhook timestamp to prevent replay attacks
        Reject webhooks older than 5 minutes

        Args:
            timestamp: ISO timestamp from webhook

        Returns:
            True if timestamp valid, False otherwise
        """
        try:
            from datetime import datetime, timedelta

            webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(webhook_time.tzinfo)

            # Reject webhooks older than 5 minutes
            if current_time - webhook_time > timedelta(minutes=5):
                logger.warning(f"Webhook timestamp too old: {timestamp}")
                return False

            # Reject webhooks from future (clock skew > 1 min)
            if webhook_time - current_time > timedelta(minutes=1):
                logger.warning(f"Webhook timestamp from future: {timestamp}")
                return False

            return True

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid webhook timestamp: {timestamp} - {e}")
            return True  # Allow if timestamp invalid (some providers don't send it)

    @staticmethod
    def rate_limit_check(provider_name: str, identifier: str) -> bool:
        """
        Rate limit webhook processing
        Prevent webhook flooding attacks

        Args:
            provider_name: Provider name
            identifier: Unique identifier (IP or provider_event_id)

        Returns:
            True if within limits, False otherwise
        """
        # TODO: Implement rate limiting (Redis-based)
        # For now, allow all
        return True
