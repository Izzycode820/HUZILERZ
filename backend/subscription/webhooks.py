"""
Subscription Payment Webhook Handler
Called by payment module's WebhookRouter for purpose='subscription'
Bridges payment system and subscription business logic
"""
import logging
from django.db import transaction

from .services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


def handle_subscription_payment_webhook(payment_intent):
    """
    Handle subscription payment webhook
    Called by: payments.webhooks.router.WebhookRouter
    When: PaymentIntent with purpose='subscription' succeeds

    Args:
        payment_intent: PaymentIntent instance with status='success'

    Returns:
        dict: {'success': bool, 'subscription_id': str, ...}
    """
    try:
        logger.info(f"Processing subscription payment webhook for PaymentIntent {payment_intent.id}")

        # Validate payment status
        if payment_intent.status != 'success':
            logger.warning(f"Webhook called with non-success status: {payment_intent.status}")
            return {
                'success': False,
                'error': f"Payment status is {payment_intent.status}, expected 'success'"
            }

        # Validate purpose
        if payment_intent.purpose != 'subscription':
            logger.error(f"Wrong webhook handler - purpose is {payment_intent.purpose}, expected 'subscription'")
            return {
                'success': False,
                'error': f"Wrong purpose: {payment_intent.purpose}"
            }

        # Delegate to subscription service
        result = SubscriptionService.activate_subscription_from_payment(payment_intent)

        if result['success']:
            logger.info(f"Successfully activated subscription from payment webhook: {result.get('subscription_id')}")
        else:
            logger.error(f"Failed to activate subscription from payment webhook: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Unhandled error in subscription payment webhook: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f"Webhook processing error: {str(e)}"
        }


# Export for payment module to import
__all__ = ['handle_subscription_payment_webhook']
