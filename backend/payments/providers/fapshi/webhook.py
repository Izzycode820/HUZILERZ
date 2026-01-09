"""
Fapshi Webhook Handler
Thin wrapper for processing Fapshi webhook notifications
"""
import logging
from typing import Dict, Any
from .adapter import FapshiAdapter

logger = logging.getLogger(__name__)


class FapshiWebhookHandler:
    """
    Handles Fapshi webhook payload processing
    Delegates to adapter for parsing and validation
    """

    @staticmethod
    def process_webhook(payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Process Fapshi webhook notification

        Args:
            payload: Raw webhook JSON payload
            headers: HTTP request headers

        Returns:
            Dict with processing result
        """
        try:
            # Create adapter instance with empty config (uses system config)
            adapter = FapshiAdapter({})

            # Parse webhook using adapter
            webhook_event = adapter.parse_webhook(payload, headers)

            logger.info(f"Fapshi webhook parsed: {webhook_event.provider_event_id} -> {webhook_event.status}")

            return {
                'success': True,
                'provider_event_id': webhook_event.provider_event_id,
                'provider_intent_id': webhook_event.provider_intent_id,
                'status': webhook_event.status,
                'amount': webhook_event.amount,
                'currency': webhook_event.currency,
                'metadata': webhook_event.metadata,
                'raw_payload': webhook_event.raw_payload
            }

        except ValueError as e:
            logger.error(f"Fapshi webhook validation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'invalid_webhook'
            }

        except Exception as e:
            logger.error(f"Fapshi webhook processing error: {e}")
            return {
                'success': False,
                'error': 'Webhook processing failed',
                'error_code': 'processing_error'
            }

    @staticmethod
    def verify_signature(payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Raw webhook JSON payload
            headers: HTTP request headers

        Returns:
            True if signature valid, False otherwise
        """
        try:
            adapter = FapshiAdapter({})
            return adapter.verify_webhook_signature(payload, headers)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
