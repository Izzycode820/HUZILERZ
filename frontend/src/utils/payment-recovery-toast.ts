/**
 * Payment Recovery Toast Utilities
 * Clean shadcn Sonner toast for payment session resumption
 * Following Stripe/Chargebee UX patterns with minimal UI disruption
 * Opens internal PaymentWizard (custom UI, not external redirect)
 */

import { toast } from 'sonner';
import type { PendingPaymentInfo } from '@/types/subscription';

interface PaymentRecoveryToastOptions {
  pendingPayment: PendingPaymentInfo;
  onResume: () => void; // Opens PaymentWizard modal
  onCancel: () => void; // Cancels payment and refreshes
}

/**
 * Show payment recovery toast with resume/cancel actions
 * Minimal, non-intrusive shadcn toast pattern
 * Resume opens internal payment wizard (no external redirect)
 */
export function showPaymentRecoveryToast({
  pendingPayment,
  onResume,
  onCancel,
}: PaymentRecoveryToastOptions) {
  // Format time remaining
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Check if payment expired
  if (pendingPayment.time_remaining <= 0) {
    toast.error('Payment Session Expired', {
      description: 'Your previous payment session has expired. Please create a new subscription.',
      duration: 5000,
    });
    return;
  }

  // Show payment recovery toast with action buttons
  const planName = pendingPayment.plan_tier.charAt(0).toUpperCase() + pendingPayment.plan_tier.slice(1);

  toast.warning('Pending Payment', {
    description: `You have a pending ${planName} plan payment (${pendingPayment.amount.toLocaleString()} FCFA). Time remaining: ${formatTime(pendingPayment.time_remaining)}`,
    duration: Infinity, // Keep until user acts
    action: {
      label: 'Resume',
      onClick: onResume, // Opens PaymentWizard modal
    },
    cancel: {
      label: 'Cancel',
      onClick: onCancel, // Cancels payment
    },
  });
}

/**
 * Show payment cancellation success toast
 */
export function showPaymentCancelledToast() {
  toast.success('Payment Cancelled', {
    description: 'Your pending payment has been cancelled. You can now create a new subscription.',
    duration: 4000,
  });
}

/**
 * Show payment cancellation error toast
 */
export function showPaymentCancellationErrorToast(error?: string) {
  toast.error('Cancellation Failed', {
    description: error || 'Failed to cancel payment. Please try again.',
    duration: 5000,
  });
}
