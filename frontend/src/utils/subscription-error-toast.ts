/**
 * Subscription Error Toast Utilities
 * Handles discriminated union errors from subscription/trial operations
 * Shows specific error messages with actionable guidance
 */

import { toast } from 'sonner';
import type {
  PaidSubscriptionExistsError,
  ActiveTrialExistsError,
  PaymentExpiredRetryAvailableError,
  CannotCancelActiveSubscriptionError,
  SubscriptionError,
} from '@/types/subscription';
import {
  isPaidSubscriptionExistsError,
  isActiveTrialExistsError,
  isPaymentExpiredRetryAvailableError,
  isCannotCancelActiveSubscriptionError,
} from '@/types/subscription';

// ============================================================================
// Specific Error Handlers
// ============================================================================

/**
 * PAID_SUBSCRIPTION_EXISTS - User tried to start trial but has active subscription
 */
function handlePaidSubscriptionExistsError(error: PaidSubscriptionExistsError) {
  const planName = error.current_plan.charAt(0).toUpperCase() + error.current_plan.slice(1);

  toast.error('Cannot Start Trial', {
    description: `You have an active ${planName} subscription. Trials are only available for new users.`,
    duration: 6000,
  });
}

/**
 * ACTIVE_TRIAL_EXISTS - User tried to subscribe but has active trial
 */
function handleActiveTrialExistsError(error: ActiveTrialExistsError) {
  const trialPlan = error.trial_tier.charAt(0).toUpperCase() + error.trial_tier.slice(1);
  const daysLeft = error.days_remaining;

  toast.warning('Active Trial in Progress', {
    description: `You're currently on a ${trialPlan} trial (${daysLeft} day${daysLeft !== 1 ? 's' : ''} remaining). You can upgrade to a paid plan at any time.`,
    duration: 7000,
  });
}

/**
 * PAYMENT_EXPIRED_RETRY_AVAILABLE - Payment failed but grace period active
 */
interface PaymentExpiredOptions {
  error: PaymentExpiredRetryAvailableError;
  onRetry?: () => void;
  onCancel?: () => void;
}

export function handlePaymentExpiredRetryAvailableError({
  error,
  onRetry,
  onCancel,
}: PaymentExpiredOptions) {
  const planName = error.plan_tier.charAt(0).toUpperCase() + error.plan_tier.slice(1);
  const hoursLeft = error.grace_period_remaining_hours;

  toast.warning('Payment Grace Period Active', {
    description: `Your ${planName} subscription payment needs to be completed. ${hoursLeft} hour${hoursLeft !== 1 ? 's' : ''} remaining to retry.`,
    duration: Infinity, // Keep until user acts
    action: onRetry ? {
      label: 'Retry Payment',
      onClick: onRetry,
    } : undefined,
    cancel: onCancel ? {
      label: 'Cancel Subscription',
      onClick: onCancel,
    } : undefined,
  });
}

/**
 * CANNOT_CANCEL_ACTIVE_SUBSCRIPTION - User tried to cancel but payment already completed
 */
function handleCannotCancelActiveSubscriptionError(error: CannotCancelActiveSubscriptionError) {
  toast.error('Cannot Cancel Subscription', {
    description: `Your subscription is currently active. Payment has already been processed. Contact support if you need assistance.`,
    duration: 7000,
    action: {
      label: 'Contact Support',
      onClick: () => {
        window.location.href = '/support';
      }
    }
  });
}

// ============================================================================
// Main Error Handler
// ============================================================================

interface HandleSubscriptionErrorOptions {
  error: unknown;
  fallbackMessage?: string;
  onRetryPayment?: () => void;
  onCancelSubscription?: () => void;
}

/**
 * Main handler for subscription errors
 * Uses type guards to identify error type and show appropriate toast
 */
export function handleSubscriptionError({
  error,
  fallbackMessage = 'Operation failed. Please try again.',
  onRetryPayment,
  onCancelSubscription,
}: HandleSubscriptionErrorOptions) {
  // Check if it's a discriminated union error
  if (isPaidSubscriptionExistsError(error)) {
    handlePaidSubscriptionExistsError(error);
    return;
  }

  if (isActiveTrialExistsError(error)) {
    handleActiveTrialExistsError(error);
    return;
  }

  if (isPaymentExpiredRetryAvailableError(error)) {
    handlePaymentExpiredRetryAvailableError({
      error,
      onRetry: onRetryPayment,
      onCancel: onCancelSubscription,
    });
    return;
  }

  if (isCannotCancelActiveSubscriptionError(error)) {
    handleCannotCancelActiveSubscriptionError(error);
    return;
  }

  // Generic error handling
  const message = error instanceof Error ? error.message : fallbackMessage;
  toast.error('Operation Failed', {
    description: message,
    duration: 5000,
  });
}

// ============================================================================
// Success Toasts
// ============================================================================

export function showSubscriptionSuccessToast(plan: string) {
  const planName = plan.charAt(0).toUpperCase() + plan.slice(1);
  toast.success('Subscription Activated', {
    description: `Your ${planName} plan is now active. Enjoy your new features!`,
    duration: 5000,
  });
}

export function showUpgradeSuccessToast(fromPlan: string, toPlan: string) {
  const from = fromPlan.charAt(0).toUpperCase() + fromPlan.slice(1);
  const to = toPlan.charAt(0).toUpperCase() + toPlan.slice(1);

  toast.success('Upgrade Successful', {
    description: `Successfully upgraded from ${from} to ${to}. Your new features are ready!`,
    duration: 5000,
  });
}

export function showSubscriptionCancelledToast() {
  toast.success('Subscription Cancelled', {
    description: 'Your subscription has been cancelled. You can reactivate anytime.',
    duration: 4000,
  });
}
