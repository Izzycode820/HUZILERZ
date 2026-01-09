"""
Subscription Background Tasks
Aligned with webhook-driven subscription architecture
"""

# Renewal and expiry handling
from .renewal_reminders import (
    send_renewal_reminders,
    send_grace_period_reminders
)

from .expiry_handler import (
    handle_expired_subscriptions,
    handle_grace_period_end,
    cleanup_abandoned_data,
    handle_intro_period_end,
    handle_long_delinquency,  # Auto-downgrade after delinquency period
)

# Plan changes
from .plan_changes import (
    apply_pending_plan_changes,
    notify_upcoming_plan_changes,
    cleanup_expired_plan_change_requests
)

# User creation fallback
from .subscription_creation import (
    create_user_subscription_fallback,
    process_dead_letter_queue
)

# Compliance enforcement (downgrade flow)
from .compliance_tasks import (
    detect_and_handle_violations,
    check_compliance_deadlines,
    enforce_workspace_compliance,
    check_violation_resolved
)

# Trial expiry
from .trial_expiry import (
    check_trial_expiry,
)

__all__ = [
    # Renewal reminders
    'send_renewal_reminders',
    'send_grace_period_reminders',

    # Expiry handling
    'handle_expired_subscriptions',
    'handle_grace_period_end',
    'cleanup_abandoned_data',
    'handle_intro_period_end',
    'handle_long_delinquency',

    # Plan changes
    'apply_pending_plan_changes',
    'notify_upcoming_plan_changes',
    'cleanup_expired_plan_change_requests',

    # User creation
    'create_user_subscription_fallback',
    'process_dead_letter_queue',

    # Compliance (downgrade flow)
    'detect_and_handle_violations',
    'check_compliance_deadlines',
    'enforce_workspace_compliance',
    'check_violation_resolved',

    # Trial expiry
    'check_trial_expiry',
]
