"""
Notification Event Receivers

Event handlers that create notifications from domain events.
Follows existing pattern from subscription/receivers.py.

Design Principles:
- Graceful failure: notification errors never block order/subscription flow
- Comprehensive logging: all events logged for debugging
- Ownership validation: check workspace has owner before notifying
"""
import logging
from django.dispatch import receiver
from subscription.events import (
    subscription_expired,
    payment_failed,
    subscription_activated,
    subscription_renewed,
    subscription_downgraded,
    subscription_cancelled,
    grace_period_started,
    plan_change_scheduled,
    compliance_violation_detected,
    compliance_auto_enforced,
    plan_change_reminder_triggered,
    renewal_reminder_triggered,
    grace_period_reminder_triggered
)
from notifications.events import order_created, order_paid
from notifications.services.notification_service import NotificationService

logger = logging.getLogger('notifications.receivers')


# ============================================================================
# ORDER EVENT HANDLERS
# ============================================================================

@receiver(order_created)
def handle_order_created(sender, order, workspace, **kwargs):
    """
    Notify merchant of new order.
    
    Reliability: Graceful failure - does not block order creation
    
    Event Args:
        order: Order instance
        workspace: Workspace instance
    """
    try:
        owner = workspace.owner
        if not owner:
            logger.warning(
                f"No owner for workspace {workspace.id}, skipping order notification"
            )
            return
        
        # Format order total safely
        total = getattr(order, 'total_amount', 0) or 0
        customer_name = getattr(order, 'customer_name', 'Customer') or 'Customer'
        order_number = getattr(order, 'order_number', str(order.id)[:8])
        
        NotificationService.create_notification(
            recipient=owner,
            notification_type='order_created',
            title=f'New order #{order_number}',
            body=f'{customer_name} placed an order for {total} XAF',
            workspace=workspace,
            data={
                'order_id': str(order.id),
                'order_number': order_number,
                'total': str(total)
            }
        )
        logger.info(f"Order created notification sent for order {order.id}")
    except Exception as e:
        # Log but do not raise - notification failure should not block order flow
        logger.error(f"Failed to create order notification: {e}", exc_info=True)


@receiver(order_paid)
def handle_order_paid(sender, order, workspace, **kwargs):
    """
    Notify merchant when order is marked as paid.
    
    Triggered by: OrderProcessingService.mark_order_as_paid()
    """
    try:
        owner = workspace.owner
        if not owner:
            return

        total = getattr(order, 'total_amount', 0) or 0
        order_number = getattr(order, 'order_number', str(order.id)[:8])
        
        NotificationService.create_notification(
            recipient=owner,
            notification_type='order_paid',
            title=f'Order #{order_number} paid',
            body=f'Payment confirmed for {total} XAF',
            workspace=workspace,
            data={
                'order_id': str(order.id),
                'order_number': order_number
            }
        )
        logger.info(f"Order paid notification sent for order {order.id}")
    except Exception as e:
        logger.error(f"Failed to create payment notification: {e}", exc_info=True)


# ============================================================================
# SUBSCRIPTION EVENT HANDLERS
# ============================================================================

@receiver(subscription_activated)
def handle_subscription_activated(sender, subscription, **kwargs):
    """
    Notify user when subscription is activated.
    
    Triggered by: payment success
    """
    try:
        plan_name = getattr(subscription.plan, 'name', 'your plan')
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='subscription_activated',
            title='Subscription Activated',
            body=f'Your {plan_name} subscription is now active. Enjoy your features!',
            data={'subscription_id': str(subscription.id)}
        )
        logger.info(f"Subscription activated notification sent for {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create activation notification: {e}", exc_info=True)


@receiver(subscription_expired)
def handle_subscription_expired(sender, subscription, **kwargs):
    """
    Notify user of subscription expiry.
    
    Triggered by: grace period end
    """
    try:
        plan_name = getattr(subscription.plan, 'name', 'your plan')
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='subscription_expired',
            title='Subscription Expired',
            body=f'Your {plan_name} subscription has expired. Renew to restore access.',
            data={'subscription_id': str(subscription.id)}
        )
        logger.info(f"Subscription expired notification sent for {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create expiry notification: {e}", exc_info=True)


@receiver(subscription_renewed)
def handle_subscription_renewed(sender, subscription, **kwargs):
    """
    Notify user when subscription is renewed.
    
    Triggered by: manual renewal payment
    """
    try:
        plan_name = getattr(subscription.plan, 'name', 'your plan')
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='subscription_activated',  # Reuse type
            title='Subscription Renewed',
            body=f'Your {plan_name} subscription has been renewed successfully.',
            data={'subscription_id': str(subscription.id)}
        )
        logger.info(f"Subscription renewed notification sent for {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create renewal notification: {e}", exc_info=True)


@receiver(payment_failed)
def handle_payment_failed(sender, payment_intent=None, subscription=None, **kwargs):
    """
    Notify user of payment failure.
    
    Triggered by: payment webhook failure
    """
    try:
        if not subscription:
            logger.warning("Payment failed event without subscription, skipping notification")
            return
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='payment_failed',
            title='Payment Failed',
            body='Your payment could not be processed. Please try again or update your payment method.',
            data={'subscription_id': str(subscription.id)}
        )
        logger.info(f"Payment failed notification sent for subscription {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create payment failed notification: {e}", exc_info=True)


# ============================================================================
# ADDITIONAL SUBSCRIPTION EVENT HANDLERS
# ============================================================================

@receiver(subscription_downgraded)
def handle_subscription_downgraded(sender, subscription, old_plan, new_plan, **kwargs):
    """
    Notify user when subscription is downgraded to lower tier.
    
    Triggered by: scheduled downgrade applied
    """
    try:
        old_plan_name = getattr(old_plan, 'name', 'previous plan')
        new_plan_name = getattr(new_plan, 'name', 'new plan')
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='subscription_downgraded',
            title='Plan Downgraded',
            body=f'Your plan has changed from {old_plan_name} to {new_plan_name}.',
            data={
                'subscription_id': str(subscription.id),
                'old_plan': old_plan_name,
                'new_plan': new_plan_name
            }
        )
        logger.info(f"Subscription downgraded notification sent for {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create downgrade notification: {e}", exc_info=True)


@receiver(subscription_cancelled)
def handle_subscription_cancelled(sender, subscription, reason=None, **kwargs):
    """
    Notify user when subscription is cancelled.
    
    Triggered by: user cancellation
    """
    try:
        plan_name = getattr(subscription.plan, 'name', 'your plan')
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='subscription_cancelled',
            title='Subscription Cancelled',
            body=f'Your {plan_name} subscription has been cancelled. You can resubscribe anytime.',
            data={
                'subscription_id': str(subscription.id),
                'reason': reason or 'user_requested'
            }
        )
        logger.info(f"Subscription cancelled notification sent for {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create cancellation notification: {e}", exc_info=True)


@receiver(grace_period_started)
def handle_grace_period_started(sender, subscription, grace_period_ends_at=None, **kwargs):
    """
    Notify user when subscription enters grace period.
    
    Triggered by: subscription expiry with grace period enabled
    """
    try:
        plan_name = getattr(subscription.plan, 'name', 'your plan')
        ends_date = grace_period_ends_at.strftime('%Y-%m-%d') if grace_period_ends_at else 'soon'
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='grace_period_started',
            title='Subscription Expiring',
            body=f'Your {plan_name} subscription has expired. Renew by {ends_date} to keep access.',
            data={
                'subscription_id': str(subscription.id),
                'grace_period_ends_at': str(grace_period_ends_at) if grace_period_ends_at else None
            }
        )
        logger.info(f"Grace period started notification sent for {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create grace period notification: {e}", exc_info=True)


@receiver(plan_change_scheduled)
def handle_plan_change_scheduled(sender, subscription, current_plan, pending_plan, effective_date=None, **kwargs):
    """
    Notify user when plan change is scheduled.
    
    Triggered by: downgrade scheduling
    """
    try:
        current_name = getattr(current_plan, 'name', 'current plan')
        pending_name = getattr(pending_plan, 'name', 'new plan')
        date_str = effective_date.strftime('%Y-%m-%d') if effective_date else 'your next billing cycle'
        
        NotificationService.create_notification(
            recipient=subscription.user,
            notification_type='plan_change_scheduled',
            title='Plan Change Scheduled',
            body=f'Your plan will change from {current_name} to {pending_name} on {date_str}.',
            data={
                'subscription_id': str(subscription.id),
                'current_plan': current_name,
                'pending_plan': pending_name,
                'effective_date': str(effective_date) if effective_date else None
            }
        )
        logger.info(f"Plan change scheduled notification sent for {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to create plan change notification: {e}", exc_info=True)


# ============================================================================
# COMPLIANCE EVENT HANDLERS (Downgrade Flow)
# ============================================================================

@receiver(compliance_violation_detected)
def handle_compliance_violation_detected(sender, user, workspace=None, violations=None, grace_deadline=None, **kwargs):
    """
    Notify user when their downgrade causes capability violations.
    
    Triggered by: downgrade compliance detection
    """
    try:
        violation_count = len(violations) if violations else 0
        deadline_str = grace_deadline.strftime('%Y-%m-%d') if grace_deadline else '7 days'
        
        NotificationService.create_notification(
            recipient=user,
            notification_type='compliance_violation',
            title='Action Required: Plan Limits',
            body=f'Your new plan has {violation_count} limit(s) exceeded. Resolve by {deadline_str} or items will be auto-adjusted.',
            workspace=workspace,
            data={
                'violation_count': violation_count,
                'grace_deadline': str(grace_deadline) if grace_deadline else None,
                'violations': [v.violation_type for v in violations] if violations else []
            }
        )
        logger.info(f"Compliance violation notification sent for user {user.id}")
    except Exception as e:
        logger.error(f"Failed to create compliance notification: {e}", exc_info=True)


@receiver(compliance_auto_enforced)
def handle_compliance_auto_enforced(sender, workspace, enforcement_results=None, **kwargs):
    """
    Notify user when auto-enforcement is applied.
    
    Triggered by: grace period expiry enforcement
    """
    try:
        if not workspace or not workspace.owner:
            return
        
        NotificationService.create_notification(
            recipient=workspace.owner,
            notification_type='compliance_enforced',
            title='Plan Limits Auto-Adjusted',
            body='Some items were adjusted to match your current plan limits. Visit settings to review.',
            workspace=workspace,
            data={
                'workspace_id': str(workspace.id),
                'enforcement_results': enforcement_results or {}
            }
        )
        logger.info(f"Compliance enforced notification sent for workspace {workspace.id}")
    except Exception as e:
        logger.error(f"Failed to create enforcement notification: {e}", exc_info=True)


# ============================================================================
# REMINDER EVENT HANDLERS (Decoupled Architecture)
# ============================================================================

@receiver(plan_change_reminder_triggered)
def handle_plan_change_reminder(sender, subscription, user, days_until_change, urgency, **kwargs):
    """
    Handle plan change reminder signal.
    """
    try:
        current_plan_name = getattr(subscription.plan, 'name', 'Current Plan')
        new_plan_name = getattr(subscription.pending_plan_change, 'name', 'New Plan')
        effective_date = subscription.plan_change_effective_date.strftime('%Y-%m-%d')
        
        title_map = {
            'low': 'Upcoming Plan Change',
            'medium': 'Plan Change Reminder',
            'high': 'Plan Change Tomorrow'
        }
        
        NotificationService.create_notification(
            recipient=user,
            notification_type='plan_change_reminder',
            title=title_map.get(urgency, 'Plan Change Reminder'),
            body=f'Your plan will change from {current_plan_name} to {new_plan_name} in {days_until_change} days ({effective_date}).',
            data={
                'subscription_id': str(subscription.id),
                'days_until_change': days_until_change,
                'urgency': urgency,
                'effective_date': effective_date,
                'current_plan': current_plan_name,
                'new_plan': new_plan_name
            }
        )
        logger.info(f"Plan change reminder sent via signal to {user.id}")
    except Exception as e:
        logger.error(f"Failed to handle plan change reminder signal: {e}", exc_info=True)


@receiver(renewal_reminder_triggered)
def handle_renewal_reminder(sender, subscription, user, days_remaining, urgency, **kwargs):
    """
    Handle renewal reminder signal.
    """
    try:
        plan_name = getattr(subscription.plan, 'name', 'your plan')
        expires_at = subscription.expires_at.strftime('%Y-%m-%d') if subscription.expires_at else 'soon'
        
        title_map = {
            'medium': 'Subscription Renewal Reminder',
            'high': 'Renewal Due Soon',
            'critical': 'Final Renewal Notice'
        }
        
        NotificationService.create_notification(
            recipient=user,
            notification_type='renewal_reminder',
            title=title_map.get(urgency, 'Renewal Reminder'),
            body=f'Your {plan_name} subscription expires in {days_remaining} day(s) on {expires_at}. Renew now to avoid interruption.',
            data={
                'subscription_id': str(subscription.id),
                'days_remaining': days_remaining,
                'urgency': urgency,
                'expires_at': expires_at
            }
        )
        logger.info(f"Renewal reminder sent via signal to {user.id}")
    except Exception as e:
        logger.error(f"Failed to handle renewal reminder signal: {e}", exc_info=True)


@receiver(grace_period_reminder_triggered)
def handle_grace_period_reminder(sender, subscription, user, hours_remaining, urgency, **kwargs):
    """
    Handle grace period reminder signal.
    """
    try:
        plan_name = getattr(subscription.plan, 'name', 'your plan')
        ends_at = subscription.grace_period_ends_at.strftime('%Y-%m-%d %H:%M') if subscription.grace_period_ends_at else 'soon'
        
        title_map = {
            'medium': 'Grace Period Reminder',
            'high': 'Urgent: Subscription Expiring',
            'critical': 'Final Notice: Last Chance to Renew'
        }
        
        NotificationService.create_notification(
            recipient=user,
            notification_type='grace_period_reminder',
            title=title_map.get(urgency, 'Grace Period Reminder'),
            body=f'Your {plan_name} access expires in {hours_remaining} hours. Renew now to keep your features.',
            data={
                'subscription_id': str(subscription.id),
                'hours_remaining': hours_remaining,
                'urgency': urgency,
                'grace_period_ends_at': ends_at
            }
        )
        logger.info(f"Grace period reminder sent via signal to {user.id}")
    except Exception as e:
        logger.error(f"Failed to handle grace period reminder signal: {e}", exc_info=True)


