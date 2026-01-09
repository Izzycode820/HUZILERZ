"""
Renewal Reminder Tasks
Handle automated notification system for subscription renewals
Signal-driven: Tasks emit signals, receivers create notifications

Reminder schedule (matches 5-day renewal window):
- 5 days before expiry (medium urgency) - Renewal window opens
- 3 days before expiry (high urgency)  
- 1 day before expiry (critical urgency)
"""
from django.utils import timezone
from datetime import timedelta
from celery import shared_task
import logging

from ..models import Subscription
from ..events import renewal_reminder_triggered, grace_period_reminder_triggered

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_renewal_reminders(self):
    """
    Send renewal reminders at 5, 3, and 1 days before expiry
    Runs daily via Celery beat
    Decoupled via signal emission
    
    NOTE: Renewal window is 5 days. Users cannot renew before day 5.
    """
    try:
        now = timezone.now()
        total_reminders = 0
        
        # 5 days before expiry - Medium urgency (renewal window opens!)
        five_days_ahead = now + timedelta(days=5)
        subscriptions_5_days = Subscription.objects.filter(
            expires_at__date=five_days_ahead.date(),
            status='active',
            plan__tier__in=['beginning', 'pro', 'enterprise']
        ).select_related('user', 'plan')
        
        for subscription in subscriptions_5_days:
            renewal_reminder_triggered.send(
                sender=Subscription,
                subscription=subscription,
                user=subscription.user,
                days_remaining=5,
                urgency='medium'
            )
            total_reminders += 1
        
        # 3 days before expiry - High urgency
        three_days_ahead = now + timedelta(days=3)
        subscriptions_3_days = Subscription.objects.filter(
            expires_at__date=three_days_ahead.date(),
            status='active',
            plan__tier__in=['beginning', 'pro', 'enterprise']
        ).select_related('user', 'plan')
        
        for subscription in subscriptions_3_days:
            renewal_reminder_triggered.send(
                sender=Subscription,
                subscription=subscription,
                user=subscription.user,
                days_remaining=3,
                urgency='high'
            )
            total_reminders += 1
        
        # 1 day before expiry - Critical urgency
        one_day_ahead = now + timedelta(days=1)
        subscriptions_1_day = Subscription.objects.filter(
            expires_at__date=one_day_ahead.date(),
            status='active',
            plan__tier__in=['beginning', 'pro', 'enterprise']
        ).select_related('user', 'plan')
        
        for subscription in subscriptions_1_day:
            renewal_reminder_triggered.send(
                sender=Subscription,
                subscription=subscription,
                user=subscription.user,
                days_remaining=1,
                urgency='critical'
            )
            total_reminders += 1
        
        logger.info(f"Emitted {total_reminders} renewal reminder signals")
        
        return {
            'success': True,
            'reminders_sent': total_reminders,
            '5_day_reminders': len(subscriptions_5_days),
            '3_day_reminders': len(subscriptions_3_days),
            '1_day_reminders': len(subscriptions_1_day)
        }
        
    except Exception as e:
        logger.error(f"Failed to send renewal reminders: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def send_grace_period_reminders(self):
    """
    Send reminders during grace period
    Runs every 12 hours via Celery beat
    Decoupled via signal emission
    """
    try:
        now = timezone.now()
        reminders_sent = 0
        
        # Find subscriptions in grace period
        subscriptions_in_grace = Subscription.objects.filter(
            status='grace_period',
            grace_period_ends_at__gt=now
        ).select_related('user', 'plan')
        
        for subscription in subscriptions_in_grace:
            hours_remaining = int((subscription.grace_period_ends_at - now).total_seconds() / 3600)
            
            # Send at specific intervals
            should_send = False
            urgency = 'medium'
            
            if 71 <= hours_remaining <= 73:  # ~72 hours
                should_send = True
                urgency = 'medium'
            elif 47 <= hours_remaining <= 49:  # ~48 hours
                should_send = True
                urgency = 'high'
            elif 23 <= hours_remaining <= 25:  # ~24 hours
                should_send = True
                urgency = 'high'
            elif 5 <= hours_remaining <= 7:  # ~6 hours
                should_send = True
                urgency = 'critical'
                
            if should_send:
                grace_period_reminder_triggered.send(
                    sender=Subscription,
                    subscription=subscription,
                    user=subscription.user,
                    hours_remaining=hours_remaining,
                    urgency=urgency
                )
                reminders_sent += 1
        
        logger.info(f"Emitted {reminders_sent} grace period reminder signals")
        
        return {
            'success': True,
            'grace_period_reminders_sent': reminders_sent
        }
        
    except Exception as e:
        logger.error(f"Failed to send grace period reminders: {str(e)}")
        raise self.retry(exc=e)