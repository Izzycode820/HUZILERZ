/**
 * Upgrade Recovery Toast Utilities
 * Shows pending upgrade notifications with action buttons
 * Similar to payment recovery but for subscription upgrades
 */

import { toast } from 'sonner';

interface PendingUpgradeInfo {
  subscription_id: string;
  current_plan: string;
  target_plan: string;
  amount_due: number;
  time_remaining_hours: number; // Hours left in 23hr grace period
  status: 'pending_payment';
}

interface UpgradeRecoveryToastOptions {
  pendingUpgrade: PendingUpgradeInfo;
  onCompletePayment: () => void;
  onCancelUpgrade: () => void;
}

/**
 * Show upgrade recovery toast with complete/cancel actions
 * Appears when user has a pending upgrade within 23hr window
 */
export function showUpgradeRecoveryToast({
  pendingUpgrade,
  onCompletePayment,
  onCancelUpgrade,
}: UpgradeRecoveryToastOptions) {
  // Check if grace period expired
  if (pendingUpgrade.time_remaining_hours <= 0) {
    toast.error('Upgrade Expired', {
      description: 'Your pending upgrade has expired. Please create a new upgrade request.',
      duration: 5000,
    });
    return;
  }

  const fromPlan = pendingUpgrade.current_plan.charAt(0).toUpperCase() + pendingUpgrade.current_plan.slice(1);
  const toPlan = pendingUpgrade.target_plan.charAt(0).toUpperCase() + pendingUpgrade.target_plan.slice(1);
  const hoursLeft = pendingUpgrade.time_remaining_hours;

  toast.warning('Pending Upgrade', {
    description: `You have a pending upgrade from ${fromPlan} to ${toPlan} (${pendingUpgrade.amount_due.toLocaleString()} FCFA). ${hoursLeft} hour${hoursLeft !== 1 ? 's' : ''} remaining to complete payment.`,
    duration: Infinity, // Keep until user acts
    action: {
      label: 'Complete Payment',
      onClick: onCompletePayment,
    },
    cancel: {
      label: 'Cancel Upgrade',
      onClick: onCancelUpgrade,
    },
  });
}

/**
 * Show upgrade cancelled success toast
 */
export function showUpgradeCancelledToast() {
  toast.success('Upgrade Cancelled', {
    description: 'Your pending upgrade has been cancelled. You can create a new upgrade anytime.',
    duration: 4000,
  });
}

/**
 * Show upgrade cancellation error toast
 */
export function showUpgradeCancellationErrorToast(error?: string) {
  toast.error('Cancellation Failed', {
    description: error || 'Failed to cancel upgrade. Please try again.',
    duration: 5000,
  });
}
