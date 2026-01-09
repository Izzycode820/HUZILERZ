/**
 * Payment Error Toast Utilities
 * Handles discriminated union errors from payment operations
 * Shows specific error messages with actionable guidance
 */

import { toast } from 'sonner';
import type {
  CannotCancelCompletedPaymentError,
  PaymentError,
} from '@/types/subscription';
import { isCannotCancelCompletedPaymentError } from '@/types/subscription';

// ============================================================================
// Specific Error Handlers
// ============================================================================

/**
 * CANNOT_CANCEL_COMPLETED - Payment already completed
 */
function handleCannotCancelCompletedPaymentError(error: CannotCancelCompletedPaymentError) {
  const status = error.current_status === 'completed' ? 'completed' : 'successful';

  toast.error('Cannot Cancel Payment', {
    description: `This payment has already been ${status}. The funds have been processed. Contact support if you need assistance.`,
    duration: 6000,
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

interface HandlePaymentErrorOptions {
  error: unknown;
  fallbackMessage?: string;
}

/**
 * Main handler for payment errors
 * Uses type guards to identify error type and show appropriate toast
 */
export function handlePaymentError({
  error,
  fallbackMessage = 'Payment operation failed. Please try again.',
}: HandlePaymentErrorOptions) {
  // Check if it's a discriminated union error
  if (isCannotCancelCompletedPaymentError(error)) {
    handleCannotCancelCompletedPaymentError(error);
    return;
  }

  // Generic error handling
  const message = error instanceof Error ? error.message : fallbackMessage;
  toast.error('Payment Failed', {
    description: message,
    duration: 5000,
  });
}

// ============================================================================
// Success Toasts
// ============================================================================

export function showPaymentInitiatedToast(plan: string, amount: number) {
  const planName = plan.charAt(0).toUpperCase() + plan.slice(1);

  toast.success('Payment Initiated', {
    description: `Payment of ${amount.toLocaleString()} FCFA for ${planName} plan initiated. Complete payment to activate.`,
    duration: 5000,
  });
}

export function showPaymentCompletedToast(plan: string) {
  const planName = plan.charAt(0).toUpperCase() + plan.slice(1);

  toast.success('Payment Completed', {
    description: `Payment successful! Your ${planName} subscription is now active.`,
    duration: 5000,
  });
}
