"""
Subscription State Coordination Signals
Provides decoupled communication when subscription changes occur
"""
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import logging
import time

from .models.subscription import Subscription, SubscriptionPlan
from .models.trial import Trial
from .tasks.subscription_creation import create_user_subscription_fallback

User = get_user_model()
logger = logging.getLogger(__name__)

# Circuit breaker state
CIRCUIT_BREAKER_KEY = 'subscription_signal_circuit_breaker'
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60  # seconds

def _is_circuit_breaker_open():
    """Check if circuit breaker is open (too many recent failures)"""
    circuit_state = cache.get(CIRCUIT_BREAKER_KEY)
    if not circuit_state:
        return False

    failures, last_failure_time = circuit_state
    if failures >= CIRCUIT_BREAKER_FAILURE_THRESHOLD:
        # Check if recovery timeout has passed
        if time.time() - last_failure_time < CIRCUIT_BREAKER_RECOVERY_TIMEOUT:
            return True
        else:
            # Reset circuit breaker after recovery timeout
            cache.delete(CIRCUIT_BREAKER_KEY)
            return False
    return False

def _record_circuit_breaker_failure():
    """Record a failure in circuit breaker"""
    circuit_state = cache.get(CIRCUIT_BREAKER_KEY)
    if not circuit_state:
        circuit_state = [1, time.time()]
    else:
        failures, last_failure_time = circuit_state
        circuit_state = [failures + 1, time.time()]

    cache.set(CIRCUIT_BREAKER_KEY, circuit_state, timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT * 2)

def _reset_circuit_breaker():
    """Reset circuit breaker after successful operation"""
    cache.delete(CIRCUIT_BREAKER_KEY)


def _enqueue_to_dead_letter_queue(user_instance):
    """
    Enqueue user to dead letter queue when circuit breaker is open
    Called when too many recent failures - bypass immediate processing
    """
    try:
        logger.error(f"Circuit breaker open - enqueuing user {user_instance.id} to dead letter queue")

        # Store in dead letter queue (could be database table or external queue)
        # For now, immediately trigger fallback task with circuit_breaker flag
        create_user_subscription_fallback.delay(
            user_instance.id,
            failure_reason="circuit_breaker_open"
        )

        logger.info(f"User {user_instance.id} enqueued to dead letter queue (fallback task started)")

    except Exception as e:
        logger.error(f"Failed to enqueue to dead letter queue for user {user_instance.id}: {e}")


def _enqueue_async_provisioning_tasks(user_instance, subscription):
    """
    Enqueue async provisioning tasks after successful subscription creation
    Workspace setup, hosting environment, welcome notifications, etc.
    """
    try:
        logger.info(f"Enqueuing async provisioning tasks for user {user_instance.id}")

        # Example: Enqueue workspace provisioning task
        # from workspace.core.tasks.provisioning_tasks import provision_default_workspace
        # provision_default_workspace.delay(user_instance.id, subscription.id)

        # Example: Enqueue welcome notification
        # from .services.notification_service import NotificationService
        # NotificationService.send_welcome_notification.delay(user_instance.id)

        # Placeholder - implement based on your actual async task structure
        logger.debug(f"Async provisioning tasks placeholder for user {user_instance.id}")

    except Exception as e:
        logger.warning(f"Failed to enqueue async provisioning tasks for user {user_instance.id}: {e}")


def _enqueue_to_celery_fallback(user_instance, last_exception):
    """
    Enqueue to Celery fallback task after all retry attempts fail
    This is the final fallback mechanism
    """
    try:
        logger.error(f"All retries failed - enqueuing to Celery fallback for user {user_instance.id}")

        # Call the Celery fallback task with exponential backoff
        create_user_subscription_fallback.delay(
            user_instance.id,
            failure_reason=str(last_exception)[:500]  # Truncate long exception messages
        )

        logger.info(f"Celery fallback task enqueued for user {user_instance.id}")

    except Exception as e:
        logger.error(f"Failed to enqueue Celery fallback for user {user_instance.id}: {e}")
        # Last resort - log critically
        logger.critical(f"COMPLETE FAILURE: User {user_instance.id} subscription creation failed, even fallback failed: {e}")


def _send_critical_alert(user_instance, last_exception):
    """
    Send critical alert for manual intervention
    Called when all retries and fallbacks fail
    """
    try:
        logger.critical(
            f"CRITICAL ALERT: Subscription creation completely failed for user {user_instance.id}. "
            f"Exception: {last_exception}"
        )

        # In production: Send to monitoring system (Sentry, Datadog, PagerDuty, etc.)
        # Example:
        # import sentry_sdk
        # sentry_sdk.capture_exception(last_exception, extra={'user_id': user_instance.id})

        # Or send email/SMS alert to admin team
        # from .services.notification_service import NotificationService
        # NotificationService.send_admin_alert(
        #     alert_type='subscription_creation_failed',
        #     severity='critical',
        #     user_id=user_instance.id,
        #     exception=str(last_exception)
        # )

    except Exception as e:
        logger.error(f"Failed to send critical alert for user {user_instance.id}: {e}")


@receiver(post_save, sender=User)
def handle_user_registration(sender, instance, created, **kwargs):
    """
    Create free subscription for new users
    Every user must have a real subscription record (free plan)
    Industry-standard robustness: circuit breaker, retry, async fallback
    """
    if not created:
        return

    # 1. Circuit breaker check
    if _is_circuit_breaker_open():
        logger.error(f"Circuit breaker OPEN for subscription signal - skipping user {instance.id}")
        # Enqueue to Celery dead letter queue for later processing
        _enqueue_to_dead_letter_queue(instance)
        return

    # 2. Retry loop with exponential backoff (3 attempts)
    max_retries = 3
    last_exception = None

    for attempt in range(max_retries):
        try:
            # Get free plan from DB (must be synced via sync_plans.py)
            # No hardcoded defaults - YAML is source of truth
            try:
                free_plan = SubscriptionPlan.objects.get(tier='free', is_active=True)
            except SubscriptionPlan.DoesNotExist:
                logger.error(
                    f"Free plan not found in database. "
                    f"Run 'python manage.py sync_plans' to sync from YAML."
                )
                raise

            # Create free subscription (always) - MUST be in atomic transaction
            from django.db import transaction

            with transaction.atomic():
                subscription, sub_created = Subscription.objects.get_or_create(
                    user=instance,
                    defaults={
                        'plan': free_plan,
                        'status': 'active',
                        'started_at': timezone.now(),
                        'expires_at': None,  # Free plans don't expire
                    }
                )

                if sub_created:
                    logger.info(f" Created free subscription for new user {instance.email}")

                    # Create SubscriptionEventLog
                    from .models.subscription import SubscriptionEventLog
                    SubscriptionEventLog.objects.create(
                        subscription=subscription,
                        user=instance,
                        event_type='subscription_created',
                        description='Free subscription created at registration',
                    )

                    # 🔥 CRITICAL: Emit subscription_activated signal AFTER transaction commits
                    # This ensures subscription is visible in DB before async tasks query it
                    # Prevents "Subscription does not exist" errors in Celery tasks
                    from .events import subscription_activated

                    def emit_activation_signal():
                        subscription_activated.send(
                            sender=Subscription,
                            subscription=subscription,
                            user=instance,
                            previous_status=None
                        )
                        logger.info(f"📡 Emitted subscription_activated signal for user {instance.email}")

                    # Signal emitted AFTER transaction commits (ensures DB consistency)
                    transaction.on_commit(emit_activation_signal)

            # 3. Success - reset circuit breaker
            _reset_circuit_breaker()

            # 4. Optional: Enqueue async provisioning tasks
            _enqueue_async_provisioning_tasks(instance, subscription)

            return  # Success - exit function

        except Exception as e:
            last_exception = e
            logger.warning(f"Subscription creation attempt {attempt + 1}/{max_retries} failed for user {instance.id}: {e}")

            if attempt < max_retries - 1:
                # Exponential backoff: 2^attempt seconds
                backoff_seconds = 2 ** attempt
                time.sleep(backoff_seconds)
            else:
                # Final attempt failed
                _record_circuit_breaker_failure()
                logger.error(f"All {max_retries} retries failed for user {instance.id}: {e}", exc_info=True)

                # 5. Fallback to Celery task with dead letter queue
                _enqueue_to_celery_fallback(instance, last_exception)

                # 6. Critical alert - this should never happen in production
                _send_critical_alert(instance, last_exception)


@receiver(post_save, sender=Subscription)
def handle_subscription_change(sender, instance, created, **kwargs):
    """
    Handle subscription creation or updates
    Emit events for modules to provision their capability records
    """
    try:
        # Log subscription change for monitoring
        action = 'created' if created else 'updated'
        logger.info(
            f"Subscription {action} for user {instance.user.id}: "
            f"tier={instance.plan.tier}, status={instance.status}"
        )

        # Send notification for subscription activation
        if created and instance.status == 'active':
            try:
                from .services.notification_service import NotificationService
                if hasattr(NotificationService, 'send_subscription_activation_notification'):
                    NotificationService.send_subscription_activation_notification(instance)
            except Exception as notif_error:
                logger.warning(f"Could not send subscription activation notification: {notif_error}")

    except Exception as e:
        logger.error(f"Error handling subscription change: {e}")


@receiver(post_delete, sender=Subscription)
def handle_subscription_deletion(sender, instance, **kwargs):
    """
    Handle subscription deletion
    Emit events for modules to handle cleanup
    """
    try:
        logger.info(f"Subscription deleted for user {instance.user.id}")

        # Notify user about subscription cancellation
        try:
            from .services.notification_service import NotificationService
            if hasattr(NotificationService, 'send_subscription_cancellation_notification'):
                NotificationService.send_subscription_cancellation_notification(instance)
        except Exception as notif_error:
            logger.warning(f"Could not send subscription cancellation notification: {notif_error}")
        
    except Exception as e:
        logger.error(f"Error handling subscription deletion: {e}")


@receiver(post_save, sender=SubscriptionPlan)
def handle_subscription_plan_change(sender, instance, **kwargs):
    """
    Handle subscription plan updates
    Emit events for affected subscriptions to re-provision
    """
    try:
        # Find all active subscriptions using this plan
        active_subscriptions = Subscription.objects.filter(
            plan=instance,
            status='active'
        )

        logger.info(
            f"Updated subscription plan {instance.tier}: "
            f"affected {active_subscriptions.count()} users - modules will re-provision via signals"
        )
        
    except Exception as e:
        logger.error(f"Error handling subscription plan change: {e}")
