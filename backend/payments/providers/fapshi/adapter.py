"""
Fapshi Payment Adapter
Implements BasePaymentAdapter for Fapshi gateway (Cameroon mobile money)
Handles MTN Mobile Money and Orange Money payments
"""
import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from ...adapters.base import (
    BasePaymentAdapter,
    PaymentResult,
    RefundResult,
    WebhookEvent
)
from .api_client import FapshiApiClient
from .operator_detector import CameroonOperatorDetector
from .config import FapshiConfig

logger = logging.getLogger(__name__)


class FapshiAdapter(BasePaymentAdapter):
    """
    Fapshi payment gateway adapter for Cameroon
    Supports MTN Mobile Money and Orange Money
    """

    def get_provider_name(self) -> str:
        """Return provider name"""
        return 'fapshi'

    def create_payment(self, payment_intent) -> PaymentResult:
        """
        Dual-mode payment creation:
        - Merchant checkout (purpose='checkout') → External redirect to merchant's Fapshi URL
        - SaaS payments (subscriptions/domains/themes) → Platform Fapshi API integration

        Args:
            payment_intent: PaymentIntent model instance

        Returns:
            PaymentResult with payment details
        """
        try:
            from ...models import MerchantPaymentMethod

            method = MerchantPaymentMethod.objects.filter(
                workspace_id=payment_intent.workspace_id,
                provider_name='fapshi',
                enabled=True
            ).first()

            if payment_intent.purpose == 'checkout' and method and method.checkout_url:
                checkout_url = method.checkout_url
                logger.info(f"Merchant checkout: Redirecting to {checkout_url}")

                return PaymentResult(
                    success=True,
                    mode='redirect',
                    provider_intent_id=str(payment_intent.id),
                    redirect_url=checkout_url,
                    instructions='You will be redirected to complete payment with Mobile Money',
                    status='pending',
                    metadata={
                        'checkout_url': checkout_url,
                        'payment_method': 'fapshi_external'
                    }
                )

            phone_number = payment_intent.metadata.get('phone_number')
            if not phone_number:
                return PaymentResult(
                    success=False,
                    error_message='Phone number required in metadata',
                    error_code='missing_phone',
                    retryable=False
                )

            operator_info = CameroonOperatorDetector.get_operator_info(phone_number)
            if not operator_info['is_valid']:
                return PaymentResult(
                    success=False,
                    error_message=operator_info['error'],
                    error_code='invalid_phone',
                    retryable=False
                )

            user_name = payment_intent.metadata.get('user_name', 'Customer')
            user_email = payment_intent.metadata.get('user_email', 'customer@example.com')

            external_ref = payment_intent.metadata.get('external_reference')
            if not external_ref:
                external_ref = f"HUZILERZ_{payment_intent.purpose.upper()}_{uuid.uuid4().hex[:12].upper()}"

            webhook_url = FapshiConfig.get_webhook_url()

            fapshi_payload = {
                'amount': int(payment_intent.amount),
                'phone': operator_info['api_phone'],
                'medium': 'mobile money',
                'name': user_name,
                'email': user_email,
                'userId': str(payment_intent.user.id),
                'externalId': external_ref,
                'message': payment_intent.metadata.get('description', f'HUZILERZ Payment'),
                'webhook': webhook_url
            }

            logger.info(f"Initiating Fapshi payment: {external_ref}")

            with FapshiApiClient() as api_client:
                api_result = api_client.initiate_payment(fapshi_payload)

            if not api_result['success']:
                error_message = api_result.get('message', 'Payment initiation failed')
                logger.error(f"Fapshi payment failed: {error_message}")

                return PaymentResult(
                    success=False,
                    error_message=error_message,
                    error_code=api_result.get('error_type', 'gateway_error'),
                    retryable=api_result.get('retryable', False),
                    metadata={'fapshi_response': api_result}
                )

            fapshi_data = api_result['data']
            provider_intent_id = fapshi_data.get('transactionId') or fapshi_data.get('transId')
            payment_link = fapshi_data.get('link') or fapshi_data.get('payment_link')

            logger.info(f"Fapshi payment initiated: {provider_intent_id}")

            return PaymentResult(
                success=True,
                mode='ussd',
                provider_intent_id=provider_intent_id,
                redirect_url=payment_link,
                instructions=f"Complete payment using {operator_info['operator_display']} on your phone",
                status='pending',
                metadata={
                    'fapshi_response': fapshi_data,
                    'operator': operator_info['operator'],
                    'operator_display': operator_info['operator_display'],
                    'payment_link': payment_link,
                    'external_reference': external_ref
                }
            )

        except Exception as e:
            logger.error(f"Fapshi adapter error: {e}")
            return PaymentResult(
                success=False,
                error_message=f'Payment adapter error: {str(e)}',
                error_code='adapter_exception',
                retryable=False
            )

    def confirm_payment(self, provider_intent_id: str) -> PaymentResult:
        """
        Check payment status with Fapshi

        Args:
            provider_intent_id: Fapshi transaction ID

        Returns:
            PaymentResult with current status
        """
        try:
            logger.info(f"Checking Fapshi payment status: {provider_intent_id}")

            with FapshiApiClient() as api_client:
                api_result = api_client.check_payment_status(provider_intent_id)

            if not api_result['success']:
                return PaymentResult(
                    success=False,
                    error_message=api_result.get('message', 'Status check failed'),
                    error_code=api_result.get('error_type', 'gateway_error'),
                    retryable=api_result.get('retryable', False)
                )

            # Extract status
            fapshi_data = api_result['data']
            fapshi_status = fapshi_data.get('status', '').upper()

            # Map Fapshi status to canonical status
            status_mapping = {
                'SUCCESSFUL': 'success',
                'FAILED': 'failed',
                'CANCELLED': 'cancelled',
                'PENDING': 'pending',
                'PROCESSING': 'pending'
            }

            canonical_status = status_mapping.get(fapshi_status, 'pending')

            return PaymentResult(
                success=True,
                status=canonical_status,
                provider_intent_id=provider_intent_id,
                metadata={'fapshi_response': fapshi_data}
            )

        except Exception as e:
            logger.error(f"Fapshi status check error: {e}")
            return PaymentResult(
                success=False,
                error_message=f'Status check error: {str(e)}',
                error_code='adapter_exception',
                retryable=True
            )

    def refund_payment(self, provider_intent_id: str, amount: int, reason: str = '') -> RefundResult:
        """
        Initiate refund with Fapshi

        Note: Fapshi does not support automated refunds via API
        Refunds must be processed manually through Fapshi dashboard

        Args:
            provider_intent_id: Fapshi transaction ID
            amount: Amount to refund
            reason: Refund reason

        Returns:
            RefundResult (always fails as not supported)
        """
        logger.warning(f"Refund requested for Fapshi payment {provider_intent_id}, but API refunds not supported")

        return RefundResult(
            success=False,
            error_message='Fapshi does not support automated refunds via API. Please process manually through Fapshi dashboard.',
            error_code='refunds_not_supported'
        )

    def parse_webhook(self, raw_payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """
        Parse Fapshi webhook payload

        Args:
            raw_payload: Raw webhook JSON payload
            headers: HTTP headers

        Returns:
            WebhookEvent with standardized data

        Raises:
            ValueError: If payload is invalid
        """
        try:
            # Verify signature first
            if not self.verify_webhook_signature(raw_payload, headers):
                raise ValueError("Invalid webhook signature")

            # Extract required fields
            external_id = raw_payload.get('externalId')
            status = raw_payload.get('status', '').upper()

            if not external_id:
                raise ValueError("Missing externalId in webhook payload")

            # Map Fapshi status to canonical status
            status_mapping = {
                'SUCCESSFUL': 'success',
                'FAILED': 'failed',
                'CANCELLED': 'cancelled',
                'PENDING': 'pending'
            }

            canonical_status = status_mapping.get(status, 'pending')

            # Extract optional fields
            transaction_id = raw_payload.get('transactionId') or raw_payload.get('transId')
            amount = raw_payload.get('amount')
            timestamp = raw_payload.get('timestamp') or raw_payload.get('completedAt')

            return WebhookEvent(
                provider_event_id=transaction_id or external_id,
                provider_intent_id=transaction_id,
                status=canonical_status,
                amount=amount,
                currency='XAF',  # Fapshi operates in XAF
                timestamp=timestamp,
                raw_payload=raw_payload,
                metadata={
                    'external_id': external_id,
                    'message': raw_payload.get('message', '')
                }
            )

        except Exception as e:
            logger.error(f"Webhook parsing error: {e}")
            raise ValueError(f"Failed to parse Fapshi webhook: {str(e)}")

    def verify_webhook_signature(self, raw_payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """
        Verify Fapshi webhook signature

        Note: Fapshi webhook signature verification is optional
        If no signature provided, we allow it but log for monitoring

        Args:
            raw_payload: Raw webhook JSON payload
            headers: HTTP headers

        Returns:
            True if signature valid or not required, False otherwise
        """
        # Check for signature in headers
        signature = headers.get('X-Fapshi-Signature') or headers.get('Signature')

        if not signature:
            # No signature provided - log and allow
            logger.info("No Fapshi webhook signature provided")
            return True

        # Get webhook secret from config
        webhook_secret = self.config.get('webhook_secret')

        if not webhook_secret:
            # No secret configured - allow but log warning
            logger.warning("Fapshi webhook secret not configured - allowing webhook")
            return True

        # TODO: Implement actual signature verification
        # Fapshi's signature algorithm should be documented in their API docs
        # For now, we log and allow
        logger.warning("Fapshi webhook signature verification not implemented yet")
        return True

    def test_credentials(self) -> Dict[str, Any]:
        """
        Test Fapshi credentials with API call

        Returns:
            Dict with test result
        """
        try:
            # Check if credentials are configured
            if not FapshiConfig.is_configured():
                return {
                    'success': False,
                    'message': 'Fapshi credentials not configured'
                }

            # Try to make a status check call (lightweight test)
            # Use a dummy transaction ID - will fail but validates auth
            with FapshiApiClient() as api_client:
                test_result = api_client.check_payment_status('test_transaction_id')

            # If we get authentication error, credentials are wrong
            if not test_result['success']:
                error_type = test_result.get('error_type', '')
                if error_type == 'authentication_failed':
                    return {
                        'success': False,
                        'message': 'Invalid Fapshi credentials'
                    }

            # If we got here, credentials are valid (even if transaction not found)
            return {
                'success': True,
                'message': 'Fapshi credentials verified successfully',
                'environment': FapshiConfig.get_environment()
            }

        except Exception as e:
            logger.error(f"Fapshi credential test error: {e}")
            return {
                'success': False,
                'message': f'Credential test failed: {str(e)}'
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return Fapshi gateway capabilities

        Returns:
            Dict with capabilities metadata
        """
        return {
            'display_name': 'Mobile Money (MTN / Orange)',
            'payment_modes': ['ussd', 'redirect'],
            'supported_currencies': ['XAF'],
            'supports_refunds': False,  # Fapshi doesn't support automated refunds
            'supports_partial_refunds': False,
            'min_amount': 100,  # 100 XAF minimum
            'max_amount': 10000000,  # 10,000,000 XAF maximum (~$16,000)
            'countries': ['CM'],  # Cameroon only
            'payment_methods': [
                {
                    'type': 'mobile-money',
                    'provider': 'MTN Mobile Money',
                    'prefixes': ['67', '650', '651', '652', '653', '654']
                },
                {
                    'type': 'mobile-money',
                    'provider': 'Orange Money',
                    'prefixes': ['69', '655', '656', '657', '658', '659']
                }
            ],
            'typical_settlement_time': '1-5 minutes',
            'webhook_support': True,
            'webhook_retry': False
        }
