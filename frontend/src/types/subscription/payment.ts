import { z } from 'zod';

/**
 * Payment Processing Types
 * Types matching exact backend payment API responses
 */

// Payment status from backend
export const PaymentStatus = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  SUCCESSFUL: 'successful',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

export type PaymentStatusType = typeof PaymentStatus[keyof typeof PaymentStatus];

// Payment type discriminator
export const PaymentType = {
  SUBSCRIPTION: 'subscription',
  TRIAL: 'trial',
} as const;

export type PaymentTypeType = typeof PaymentType[keyof typeof PaymentType];

// Payment method from backend (Fapshi gateway)
export const PaymentMethod = {
  FAPSHI: 'fapshi',
} as const;

export type PaymentMethodType = typeof PaymentMethod[keyof typeof PaymentMethod];

// Phone number validation for Cameroon
export const PhoneNumberSchema = z.string()
  .regex(/^[2-9][0-9]{8}$/, 'Invalid Cameroon phone number format (9 digits)');

/**
 * Payment Initiation Request
 * POST /api/subscriptions/payment/initiate/
 */
export const PaymentInitiationSchema = z.object({
  payment_type: z.enum(['subscription', 'trial']),
  plan_tier: z.enum(['beginning', 'pro', 'enterprise']),
  phone_number: PhoneNumberSchema,
  payment_method: z.enum(['fapshi']),
  amount: z.number().positive(),
});

export interface PaymentInitiationRequest {
  readonly payment_type: PaymentTypeType;
  readonly plan_tier: 'beginning' | 'pro' | 'enterprise';
  readonly phone_number: string;
  readonly payment_method: PaymentMethodType;
  readonly amount: number;
}

/**
 * Payment Initiation Response
 * Backend response after initiating payment
 */
export interface PaymentInitiationResponse {
  readonly success: boolean;
  readonly payment_id: string;
  readonly payment_reference: string;
  readonly amount: number;
  readonly total_amount: number;
  readonly currency: 'FCFA';
  readonly operator: string;
  readonly phone_display: string;
  readonly payment_link: string | null;
  readonly message: string;
  readonly environment: 'sandbox' | 'live';
}

/**
 * Payment Status Check Response
 * GET /api/subscriptions/payment/status/{payment_id}/
 */
export interface PaymentStatusResponse {
  readonly success: boolean;
  readonly payment_id: string;
  readonly status: PaymentStatusType;
  readonly amount: number;
  readonly currency: 'FCFA';
  readonly created_at: string;
}

/**
 * Payment record for display in UI
 */
export interface PaymentRecord {
  readonly id: string;
  readonly reference: string;
  readonly status: PaymentStatusType;
  readonly amount: number;
  readonly currency: 'FCFA';
  readonly operator: string;
  readonly phone_display: string;
  readonly created_at: string;
  readonly payment_type: PaymentTypeType;
}

/**
 * Type guard to check if payment is complete
 */
export function isPaymentComplete(status: PaymentStatusType): boolean {
  return status === PaymentStatus.COMPLETED || status === PaymentStatus.SUCCESSFUL;
}

/**
 * Type guard to check if payment failed
 */
export function isPaymentFailed(status: PaymentStatusType): boolean {
  return status === PaymentStatus.FAILED || status === PaymentStatus.CANCELLED;
}

/**
 * Type guard to check if payment is in progress
 */
export function isPaymentPending(status: PaymentStatusType): boolean {
  return status === PaymentStatus.PENDING || status === PaymentStatus.PROCESSING;
}

/**
 * Cancel Payment Request
 * POST /api/subscriptions/payment/cancel/{payment_id}/
 */
export const CancelPaymentSchema = z.object({
  reason: z.string().optional(),
});

export interface CancelPaymentRequest {
  readonly reason?: string;
}

/**
 * Cancel Payment Response
 * POST /api/subscriptions/payment/cancel/{payment_id}/
 * Following Stripe/Chargebee pattern for payment cancellation
 */
export interface CancelPaymentResponse {
  readonly success: boolean;
  readonly message: string;
  readonly payment?: {
    readonly id: string;
    readonly status: PaymentStatusType;
    readonly cancelled_at: string | null;
    readonly cancellation_reason: string;
  };
  readonly error?: string;
  readonly current_status?: string;
}

// ============================================================================
// Payment Error Types (Discriminated Unions)
// Aligned with PAYLOAD.md (2025-10-03)
// ============================================================================

/**
 * Cannot Cancel Completed Payment (400 BAD REQUEST)
 * POST /api/subscriptions/payment/cancel/{payment_id}/
 */
export interface CannotCancelCompletedPaymentError {
  readonly success: false;
  readonly error: string;
  readonly error_code: 'CANNOT_CANCEL_COMPLETED';
  readonly current_status: 'completed' | 'successful';
}

/**
 * Discriminated Union for All Payment Errors
 */
export type PaymentError = CannotCancelCompletedPaymentError;

// ============================================================================
// Type Guards for Payment Errors
// ============================================================================

export function isCannotCancelCompletedPaymentError(
  error: unknown
): error is CannotCancelCompletedPaymentError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error_code' in error &&
    error.error_code === 'CANNOT_CANCEL_COMPLETED'
  );
}