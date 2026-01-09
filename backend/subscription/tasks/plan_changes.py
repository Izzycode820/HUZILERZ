"""
Plan Change Application Tasks
Handle scheduled plan changes at billing cycle boundaries
Aligned with webhook-driven subscription architecture
Note: Resource/capability enforcement deferred to future capabilities service
"""
from django.utils import timezone
from django.db import transaction
from celery import shared_task
import logging

from ..models.subscription import Subscription, SubscriptionHistory
from ..services.subscription_service import SubscriptionService
from ..events import plan_change_reminder_triggered

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=900)
def apply_pending_plan_changes(self):
    """
    Apply scheduled plan changes at billing cycle boundaries
    Service layer emits plan_change_applied and subscription_downgraded signals
    Signal listeners will handle capability/feature adjustments when implemented
    """
    try:
        # Use service method to apply all pending changes
        # Service emits signals: plan_change_applied, subscription_downgraded
        result = SubscriptionService.apply_pending_plan_changes()

        applied_count = result.get('applied_count', 0)
        logger.info(f"Applied {applied_count} pending plan changes")

        return {
            'success': True,
            'plan_changes_applied': applied_count
        }

    except Exception as e:
        logger.error(f"Failed to apply pending plan changes: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=2, default_retry_delay=1800)
def notify_upcoming_plan_changes(self):
    """
    Notify users about plan changes scheduled for next billing cycle
    Send reminders 7 days, 3 days, and 1 day before effective date
    Decoupled via signal emission
    """
    try:
        now = timezone.now()
        
        # Find subscriptions with pending plan changes
        upcoming_changes = Subscription.objects.filter(
            pending_plan_change__isnull=False,
            plan_change_effective_date__gt=now
        ).select_related('user', 'plan', 'pending_plan_change')
        
        notifications_sent = 0
        
        for subscription in upcoming_changes:
            days_until_change = (subscription.plan_change_effective_date.date() - now.date()).days
            
            # Send reminders at specific intervals via signal
            if days_until_change in [7, 3, 1]:
                urgency_map = {7: 'low', 3: 'medium', 1: 'high'}
                urgency = urgency_map.get(days_until_change, 'low')
                
                plan_change_reminder_triggered.send(
                    sender=Subscription,
                    subscription=subscription,
                    user=subscription.user,
                    days_until_change=days_until_change,
                    urgency=urgency
                )
                notifications_sent += 1
                logger.info(f"Emitted plan change reminder signal for user {subscription.user.id} ({days_until_change} days)")
        
        return {
            'success': True,
            'reminders_sent': notifications_sent
        }
        
    except Exception as e:
        logger.error(f"Failed to send plan change reminders: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=2, default_retry_delay=3600)
def cleanup_expired_plan_change_requests(self):
    """
    Clean up plan change requests that were never applied
    Remove stale scheduling data
    """
    try:
        now = timezone.now()
        
        # Find plan changes that should have been applied but weren't
        expired_requests = Subscription.objects.filter(
            pending_plan_change__isnull=False,
            plan_change_effective_date__lt=now - timezone.timedelta(days=1)  # More than 1 day overdue
        )
        
        cleaned_count = 0
        
        for subscription in expired_requests:
            # Log the cleanup
            logger.warning(f"Cleaning up expired plan change request for subscription {subscription.id}")
            
            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='plan_change_expired',
                notes=f"Plan change request expired without processing: {subscription.pending_plan_change.tier}"
            )
            
            # Clear the pending change
            subscription.pending_plan_change = None
            subscription.plan_change_effective_date = None
            subscription.save()
            
            cleaned_count += 1
        
        return {
            'success': True,
            'expired_requests_cleaned': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired plan change requests: {str(e)}")
        raise self.retry(exc=e)