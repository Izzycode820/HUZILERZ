"""
Subscription Expiry and Grace Period Handler Tasks
Manage subscription expiry workflow with grace period
Automatically downgrade to free plan after grace period ends
Signal-driven: Tasks emit signals, receivers create notifications
"""
from django.utils import timezone
from django.db import transaction
from celery import shared_task
from datetime import timedelta
import logging

from ..models import Subscription, SubscriptionHistory
from ..services.subscription_service import SubscriptionService
from ..events import (
    grace_period_started,
    subscription_expired,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def handle_expired_subscriptions(self):
    """
    Process subscriptions that have expired (expires_at reached)
    Start grace period and emit grace_period_started signal
    Notifications handled by notifications/receivers.py
    """
    try:
        now = timezone.now()
        
        # Find subscriptions that expired (expires_at <= now) but not yet processed
        expired_subscriptions = Subscription.objects.filter(
            expires_at__lte=now,
            status='active',
            plan__tier__in=['beginning', 'pro', 'enterprise']
        ).select_related('user', 'plan', 'primary_workspace')
        
        processed_count = 0
        
        for subscription in expired_subscriptions:
            try:
                with transaction.atomic():
                    # Use service method to handle expiry (sets grace period)
                    SubscriptionService.handle_subscription_expiry(subscription)
                    
                    # Emit signal for notifications
                    grace_period_started.send(
                        sender=Subscription,
                        subscription=subscription,
                        user=subscription.user,
                        grace_period_ends_at=subscription.grace_period_ends_at
                    )
                    
                    processed_count += 1
                    logger.info(f"Started grace period for subscription {subscription.id}")
                    
            except Exception as e:
                logger.error(f"Failed to handle expiry for subscription {subscription.id}: {str(e)}")
                continue
        
        logger.info(f"Processed {processed_count} expired subscriptions")
        
        return {
            'success': True,
            'expired_subscriptions_processed': processed_count
        }
        
    except Exception as e:
        logger.error(f"Failed to handle expired subscriptions: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=900)
def handle_grace_period_end(self):
    """
    Process subscriptions where grace period has ended
    Moves to RESTRICTED status (keeps tier, gates actions)
    Auto-downgrade to free only after SUBSCRIPTION_DELINQUENCY_DAYS (default: 90)
    """
    try:
        now = timezone.now()

        # Find subscriptions where grace period has ended
        grace_period_ended = Subscription.objects.filter(
            status='grace_period',
            grace_period_ends_at__lte=now
        ).select_related('user', 'plan', 'primary_workspace')

        downgraded_count = 0

        for subscription in grace_period_ended:
            try:
                with transaction.atomic():
                    # Use service method to handle grace period end
                    # This downgrades to free plan and emits subscription_expired
                    SubscriptionService.handle_grace_period_end(subscription)
                    downgraded_count += 1

                    logger.info(f"Moved subscription {subscription.id} to restricted after grace period")

            except Exception as e:
                logger.error(f"Failed to handle grace period end for subscription {subscription.id}: {str(e)}")
                continue

        logger.info(f"Processed {downgraded_count} subscriptions to restricted status")
        
        return {
            'success': True,
            'subscriptions_restricted': downgraded_count
        }
        
    except Exception as e:
        logger.error(f"Failed to handle grace period end: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=1800)
def cleanup_abandoned_data(self):
    """
    Clean up data for subscriptions that have been suspended for 30+ days
    Note: Suspension is for fraud/abuse cases, not expiry (expiry downgrades to free)
    """
    try:
        now = timezone.now()
        cutoff_date = now - timedelta(days=30)

        # Find subscriptions suspended for 30+ days
        long_suspended = Subscription.objects.filter(
            status='suspended',
            grace_period_ends_at__lt=cutoff_date
        ).select_related('user', 'plan', 'primary_workspace')
        
        cleaned_count = 0
        
        for subscription in long_suspended:
            try:
                with transaction.atomic():
                    # Mark for data cleanup
                    if not subscription.subscription_metadata:
                        subscription.subscription_metadata = {}
                    
                    subscription.subscription_metadata['data_cleanup_scheduled'] = True
                    subscription.subscription_metadata['cleanup_date'] = now.isoformat()
                    subscription.subscription_metadata['data_retention_level'] = 'essential_only'
                    
                    subscription.save()
                    
                    # Create history record
                    SubscriptionHistory.objects.create(
                        subscription=subscription,
                        action='data_cleanup_scheduled',
                        notes=f"Scheduled cleanup after 30-day suspension period"
                    )
                    
                    cleaned_count += 1
                    logger.info(f"Scheduled data cleanup for subscription {subscription.id}")
                    
            except Exception as e:
                logger.error(f"Failed to schedule cleanup for subscription {subscription.id}: {str(e)}")
                continue
        
        return {
            'success': True,
            'cleanup_scheduled': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule data cleanup: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def handle_intro_period_end(self):
    """
    Process subscriptions where intro/trial period has ended
    Transition to regular billing or handle based on business rules
    
    Intro period: Discounted first period that transitions to regular pricing
    Trial period: Free trial that requires conversion
    """
    try:
        from ..events import trial_expired
        
        now = timezone.now()
        
        # Find subscriptions with intro pricing that's ending
        # These are subscriptions that started with intro pricing and need to renew at regular
        intro_ending = Subscription.objects.filter(
            status='active',
            subscription_metadata__has_key='intro_pricing_used',
            subscription_metadata__intro_pricing_used=True,
            expires_at__date=now.date()
        ).select_related('user', 'plan')
        
        processed_count = 0
        
        for subscription in intro_ending:
            try:
                # Mark that intro period is complete
                if not subscription.subscription_metadata:
                    subscription.subscription_metadata = {}
                    
                subscription.subscription_metadata['intro_period_completed'] = True
                subscription.subscription_metadata['intro_period_ended_at'] = now.isoformat()
                subscription.save()
                
                # Note: The actual expiry handling is done by handle_expired_subscriptions
                # This task just marks the intro period as complete for tracking
                
                processed_count += 1
                logger.info(f"Marked intro period complete for subscription {subscription.id}")
                
            except Exception as e:
                logger.error(f"Failed to process intro end for subscription {subscription.id}: {str(e)}")
                continue
        
        logger.info(f"Processed {processed_count} intro period endings")
        
        return {
            'success': True,
            'intro_periods_processed': processed_count
        }
        
    except Exception as e:
        logger.error(f"Failed to handle intro period end: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=900)
def handle_long_delinquency(self):
    """
    Process subscriptions in RESTRICTED status past delinquency threshold.
    Auto-downgrade to free plan after SUBSCRIPTION_DELINQUENCY_DAYS (default: 90).

    Industry Standard (gem.md):
    - Only downgrade after long inactivity (60-90 days unpaid)
    - Never delete data, just lock features beyond lower plan limits
    - This is the ONLY place where auto-downgrade to free happens
    """
    try:
        result = SubscriptionService.handle_long_delinquency()

        logger.info(
            f"Long delinquency processing complete: "
            f"{result['processed_count']} downgraded after {result['delinquency_days']} days"
        )

        return {
            'success': True,
            'subscriptions_downgraded': result['processed_count'],
            'delinquency_days': result['delinquency_days']
        }

    except Exception as e:
        logger.error(f"Failed to handle long delinquency: {str(e)}")
        raise self.retry(exc=e)