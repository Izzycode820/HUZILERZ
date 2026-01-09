"""
Custom Subscription Lifecycle Signals
Event-driven architecture for decoupled subscription state management
Emitted by service layer, consumed by async task handlers
"""
from django.dispatch import Signal

# ============================================================================
# SUBSCRIPTION LIFECYCLE EVENTS
# ============================================================================

subscription_upgrade_initiated = Signal()
"""
Emitted when user initiates plan upgrade
Args: subscription, target_plan, user
Triggers: payment intent creation, pending_payment status
"""

subscription_activated = Signal()
"""
Emitted when subscription becomes active (after payment)
Args: subscription, user, previous_status
Triggers: provisioning, feature enablement, welcome notifications
"""

subscription_renewed = Signal()
"""
Emitted when user manually renews subscription (Cameroon context)
Args: subscription, user, payment_record
Triggers: extend expiry, provisioning check, renewal confirmation
"""

subscription_expired = Signal()
"""
Emitted when subscription expires (after grace period)
Args: subscription, user
Triggers: downgrade to free, de-provisioning, expiry notifications
"""

subscription_downgraded = Signal()
"""
Emitted when subscription downgrades to lower tier
Args: subscription, old_plan, new_plan, user
Triggers: feature removal, resource de-allocation, downgrade notifications
"""

subscription_cancelled = Signal()
"""
Emitted when user cancels subscription
Args: subscription, user, reason
Triggers: immediate downgrade to free, cancellation notifications
"""

subscription_suspended = Signal()
"""
Emitted when subscription is suspended (fraud/abuse/non-payment)
Args: subscription, user, reason
Triggers: workspace access revoked, suspension notifications
"""

subscription_reactivated = Signal()
"""
Emitted when subscription is reactivated after being restricted/suspended
Args: subscription, user
Triggers: restore workspace access, clear restrictions, reactivation notifications
"""

subscription_reactivated = Signal()
"""
Emitted when suspended subscription is reactivated
Args: subscription, user
Triggers: restore access, provisioning check, reactivation notifications
"""

# ============================================================================
# GRACE PERIOD EVENTS
# ============================================================================

grace_period_started = Signal()
"""
Emitted when subscription enters grace period after expiry
Args: subscription, user, grace_period_ends_at
Triggers: grace period notifications, limited access warnings
"""

grace_period_ended = Signal()
"""
Emitted when grace period ends without renewal
Args: subscription, user
Triggers: final downgrade to free, final expiry notifications
"""

# ============================================================================
# TRIAL EVENTS
# ============================================================================

trial_started = Signal()
"""
Emitted when user starts trial (after payment)
Args: trial, user, tier
Triggers: trial provisioning, trial welcome notifications
"""

trial_upgraded = Signal()
"""
Emitted when user upgrades trial to higher tier
Args: trial, old_tier, new_tier, user
Triggers: tier upgrade provisioning, upgrade notifications
"""

trial_converted = Signal()
"""
Emitted when trial converts to full subscription
Args: trial, subscription, user
Triggers: subscription provisioning, conversion notifications, history tracking
"""

trial_expired = Signal()
"""
Emitted when trial expires without conversion
Args: trial, user
Triggers: trial expiry notifications, downgrade to free
"""

trial_initiated = Signal()
"""
Emitted when trial payment is initiated (before payment completion)
Args: trial, user, tier
Triggers: payment tracking, trial intent logging
"""

trial_activated = Signal()
"""
Emitted when trial is activated after successful payment
Args: trial, user, tier
Triggers: trial provisioning, trial welcome notifications, capabilities assignment
"""

trial_cancelled = Signal()
"""
Emitted when user cancels trial
Args: trial, user, reason
Triggers: trial cleanup, cancellation notifications
"""

# ============================================================================
# PAYMENT EVENTS
# ============================================================================

payment_received = Signal()
"""
Emitted when payment webhook confirms successful payment
Args: payment_record, subscription, user
Triggers: subscription activation, payment confirmation notifications
"""

payment_failed = Signal()
"""
Emitted when payment fails or webhook indicates failure
Args: payment_intent, subscription, user, reason
Triggers: payment failure notifications, retry prompts
"""

# ============================================================================
# PLAN CHANGE EVENTS
# ============================================================================

plan_change_scheduled = Signal()
"""
Emitted when plan change is scheduled for next billing cycle
Args: subscription, current_plan, pending_plan, effective_date, user
Triggers: scheduled change notifications, reminder setup
"""

plan_change_applied = Signal()
"""
Emitted when scheduled plan change is applied
Args: subscription, old_plan, new_plan, user
Triggers: provisioning adjustment, plan change notifications
"""

# ============================================================================
# PROVISIONING EVENTS (for monitoring/debugging)
# ============================================================================

provisioning_started = Signal()
"""
Emitted when provisioning tasks start
Args: subscription, user, task_type
Triggers: monitoring, logging
"""

provisioning_completed = Signal()
"""
Emitted when provisioning tasks complete successfully
Args: subscription, user, task_type, result
Triggers: success logging, analytics
"""

provisioning_failed = Signal()
"""
Emitted when provisioning tasks fail
Args: subscription, user, task_type, error
Triggers: error logging, alerts, retry scheduling
"""

# ============================================================================
# COMPLIANCE EVENTS (Downgrade Flow)
# ============================================================================

compliance_violation_detected = Signal()
"""
Emitted when subscription downgrade causes capability violations
Args: user, workspace, violations (list of ViolationRecord), grace_deadline
Triggers: compliance notifications, violation tracking, frontend warnings
"""

compliance_grace_expired = Signal()
"""
Emitted when compliance grace period expires without resolution
Args: workspace, violations
Triggers: auto-enforcement task, deadline notifications
"""

compliance_auto_enforced = Signal()
"""
Emitted after auto-enforcement completes
Args: workspace, enforcement_results (dict per violation type)
Triggers: post-enforcement notifications, audit logging
"""

compliance_resolved = Signal()
"""
Emitted when user manually resolves a violation (or all violations)
Args: workspace, violation_type, resolution_method ('manual' or 'auto')
Triggers: compliance status update, resolution notifications
"""

# ============================================================================
# NOTIFICATION REMINDER EVENTS 
# ============================================================================

plan_change_reminder_triggered = Signal()
"""
Emitted when a plan change reminder is due
Args: subscription, user, days_until_change, urgency
Triggers: notification service to send reminder
"""

renewal_reminder_triggered = Signal()
"""
Emitted when a renewal reminder is due
Args: subscription, user, days_remaining, urgency
Triggers: notification service to send reminder
"""

grace_period_reminder_triggered = Signal()
"""
Emitted when a grace period reminder is due
Args: subscription, user, hours_remaining, urgency
Triggers: notification service to send reminder
"""

