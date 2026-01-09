"""
Subscription Creation Fallback Tasks
Handle subscription creation when primary signal fails
Dead letter queue processing and retry mechanisms
"""
from django.utils import timezone
from django.db import transaction
from celery import shared_task
import logging
import time

from ..models.subscription import Subscription, SubscriptionPlan, SubscriptionEventLog
from ..services.capability_engine import CapabilityEngine

logger = logging.getLogger(__name__)


def _get_free_plan_defaults():
    """
    Get free plan defaults from plans.yaml - single source of truth.
    Maps YAML capability fields to SubscriptionPlan model fields.
    Only includes fields defined in plans.yaml.
    """
    try:
        capabilities = CapabilityEngine.get_plan_capabilities('free')
        plans_yaml = CapabilityEngine.load_plans_yaml()
        pricing = plans_yaml['tiers']['free']['pricing']
        
        return {
            'name': 'Free Plan',
            'price_fcfa': pricing['regular']['monthly'],
            'price_usd': 0,
            'max_workspaces': capabilities.get('workspace_limit', 1),
            'deployment_allowed': capabilities.get('deployment_allowed', False),
            'storage_gb': capabilities.get('storage_gb', 0.5),
            'custom_domains': 0 if not capabilities.get('custom_domain', False) else 1,
            'analytics_level': capabilities.get('analytics', 'basic'),
            'dedicated_support': capabilities.get('dedicated_support', False),
            'infrastructure_model': 'POOL',
            'is_active': True,
        }
    except Exception as e:
        logger.error(f"Failed to load free plan from YAML: {e}")
        raise  # Don't use fallback - plans.yaml is the source of truth

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_user_subscription_fallback(self, user_id, failure_reason=None):
    """
    Fallback task for subscription creation when signal fails
    Called after 3 retry attempts in signal handler
    Industry standard: exponential backoff, dead letter queue pattern
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=user_id)

        logger.info(f"Processing subscription fallback for user {user_id}, attempt {self.request.retries + 1}")

        # 1. Ensure free plan exists (from plans.yaml - single source of truth)
        free_plan, _ = SubscriptionPlan.objects.get_or_create(
            tier='free',
            defaults=_get_free_plan_defaults()
        )

        # 2. Create free subscription (idempotent)
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': free_plan,
                'status': 'active',
                'started_at': timezone.now(),
                'expires_at': None,  # Free plans don't expire
            }
        )

        if created:
            logger.info(f"Successfully created free subscription for user {user_id} via fallback")

            # Create SubscriptionEventLog
            SubscriptionEventLog.objects.create(
                subscription=subscription,
                user=user,
                event_type='subscription_created_fallback',
                description=f'Free subscription created via fallback task. Original failure: {failure_reason}',
            )

        logger.info(f"Successfully processed subscription fallback for user {user_id}")

        return {
            'success': True,
            'user_id': user_id,
            'subscription_created': created,
            'subscription_id': subscription.id if subscription else None,
            'failure_reason': failure_reason,
        }

    except Exception as e:
        logger.error(f"Subscription fallback task failed for user {user_id}: {str(e)}", exc_info=True)

        # Check if we should retry
        if self.request.retries < self.max_retries:
            # Exponential backoff: 60, 120, 240 seconds
            countdown = self.default_retry_delay * (2 ** self.request.retries)
            logger.warning(f"Retrying subscription fallback for user {user_id} in {countdown}s")
            raise self.retry(exc=e, countdown=countdown)
        else:
            # Max retries exceeded - send to dead letter queue for manual intervention
            logger.critical(f"MAX RETRIES EXCEEDED for subscription fallback user {user_id}: {str(e)}")

            # Store in dead letter queue (could be a database table or external queue)
            _store_in_dead_letter_queue(user_id, str(e), failure_reason)

            # Send critical alert
            _send_critical_alert_dlq(user_id, str(e), failure_reason)

            return {
                'success': False,
                'user_id': user_id,
                'error': str(e),
                'failure_reason': failure_reason,
                'status': 'dead_letter_queue',
            }

@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def process_dead_letter_queue(self, batch_size=100):
    """
    Process dead letter queue entries for manual recovery
    Runs daily to attempt recovery of failed subscription creations
    """
    try:
        from django.contrib.auth import get_user_model
        from ..models.subscription import SubscriptionDeadLetterQueue

        User = get_user_model()
        logger.info("Starting dead letter queue processing")

        # Get unprocessed entries
        dead_letter_entries = SubscriptionDeadLetterQueue.objects.filter(
            task_type='subscription_creation',
            processed=False
        ).order_by('created_at')[:batch_size]

        processed_count = 0
        recovered_count = 0

        for entry in dead_letter_entries:
            try:
                user = User.objects.get(id=entry.user_id)

                # Check if subscription now exists
                if hasattr(user, 'subscription'):
                    entry.processed = True
                    entry.processed_at = timezone.now()
                    entry.resolution_notes = "Subscription already exists"
                    entry.save()
                    recovered_count += 1
                    continue

                # Create subscription (from plans.yaml - single source of truth)
                free_plan, _ = SubscriptionPlan.objects.get_or_create(
                    tier='free',
                    defaults=_get_free_plan_defaults()
                )

                subscription, created = Subscription.objects.get_or_create(
                    user=user,
                    defaults={
                        'plan': free_plan,
                        'status': 'active',
                        'started_at': timezone.now(),
                        'expires_at': None,
                    }
                )

                if created:
                    SubscriptionEventLog.objects.create(
                        subscription=subscription,
                        user=user,
                        event_type='subscription_created_recovery',
                        description=f'Recovered from DLQ. Error: {entry.error_message[:100]}',
                    )

                entry.processed = True
                entry.processed_at = timezone.now()
                entry.resolution_notes = "Successfully recovered"
                entry.save()

                recovered_count += 1
                logger.info(f"Recovered subscription for user {entry.user_id}")

            except Exception as e:
                logger.error(f"Failed to process DLQ entry {entry.id}: {str(e)}")
                entry.retry_count += 1
                entry.save()

            processed_count += 1

        logger.info(f"DLQ processing: {processed_count} processed, {recovered_count} recovered")

        return {
            'success': True,
            'processed': processed_count,
            'recovered': recovered_count,
        }

    except Exception as e:
        logger.error(f"Dead letter queue processing failed: {str(e)}")
        raise self.retry(exc=e)

def _store_in_dead_letter_queue(user_id, error_message, original_failure_reason=None):
    """
    Store failed subscription creation in dead letter queue
    Database table for manual recovery
    """
    try:
        from ..models.subscription import SubscriptionDeadLetterQueue

        SubscriptionDeadLetterQueue.objects.create(
            user_id=user_id,
            task_type='subscription_creation',
            error_message=error_message[:500],
            original_failure_reason=original_failure_reason[:500] if original_failure_reason else None,
            retry_count=3,
            priority='critical',
            processed=False,
        )

        logger.critical(
            f"DEAD LETTER QUEUE ENTRY: user_id={user_id}, "
            f"error={error_message[:200]}"
        )

    except Exception as e:
        logger.error(f"Failed to store in dead letter queue: {str(e)}")

def _send_critical_alert_dlq(user_id, error_message, original_failure_reason=None):
    """
    Send critical alert for dead letter queue entry
    Notify admin team for manual intervention
    """
    try:
        # Example: Send to monitoring system (Sentry, Datadog, etc.)
        logger.critical(
            f"CRITICAL ALERT: Subscription creation failed after all retries. "
            f"User ID: {user_id}, Error: {error_message[:200]}, "
            f"Original: {original_failure_reason}"
        )

        # In production:
        # from ..services.notification_service import NotificationService
        # NotificationService.send_admin_alert(
        #     alert_type='subscription_creation_failed',
        #     severity='critical',
        #     user_id=user_id,
        #     error_message=error_message,
        #     original_failure_reason=original_failure_reason,
        # )

    except Exception as e:
        logger.error(f"Failed to send critical alert: {str(e)}")