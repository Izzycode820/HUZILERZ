/**
 * Subscription Types
 * Aligned with backend SubscriptionService and PaymentService
 * Features: Webhook-driven payments, manual renewal, strict validation
 */

// ============================================================================
// Subscription Plan Types
// ============================================================================

export type SubscriptionTier = 'free' | 'beginner' | 'pro' | 'enterprise';
export type BillingCycle = 'monthly' | 'yearly';
export type PricingMode = 'intro' | 'regular';
export type BillingPhase = 'intro' | 'regular';
export type SubscriptionStatus =
  | 'pending_payment'
  | 'change_pending'
  | 'active'
  | 'expired'
  | 'grace_period'
  | 'suspended'
  | 'cancelled';

export interface SubscriptionPlan {
  id: string;
  name: string;
  tier: SubscriptionTier;
  description: string;

  // Intro pricing (28-day first cycle)
  intro_price: number;
  intro_duration_days: number;

  // Regular pricing
  regular_price_monthly: number;
  regular_price_yearly: number;

  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Create Subscription Types
// ============================================================================

export interface CreateSubscriptionRequest {
  plan_tier: SubscriptionTier;
  workspace_id?: string;
  phone_number: string;
  provider?: string;
  billing_cycle?: BillingCycle;
  pricing_mode?: PricingMode; // NEW: Explicit user choice (intro or regular)
  idempotency_key?: string;
}

export interface CreateSubscriptionResponse {
  success: boolean;
  subscription_id?: string;
  payment_intent_id?: string;
  payment_instructions?: string;
  redirect_url?: string;
  amount?: number;
  plan?: SubscriptionTier;
  billing_cycle?: BillingCycle;
  billing_phase?: BillingPhase; // NEW: intro or regular
  cycle_duration_days?: number; // NEW: 28/30/365
  message?: string;
  already_processed?: boolean;
  error?: string;
}

// ============================================================================
// Renew Subscription Types
// ============================================================================

export interface RenewSubscriptionRequest {
  phone_number: string;
  provider?: string;
  idempotency_key?: string;
}

export interface RenewSubscriptionResponse {
  success: boolean;
  subscription_id?: string;
  payment_intent_id?: string;
  payment_instructions?: string;
  redirect_url?: string;
  amount?: number;
  billing_cycle?: BillingCycle; // NEW
  cycle_duration_days?: number; // NEW
  message?: string;
  already_processed?: boolean;
  error?: string;
}

// ============================================================================
// Upgrade Subscription Types
// ============================================================================

export interface UpgradeSubscriptionRequest {
  new_plan_tier: SubscriptionTier;
  phone_number: string;
  provider?: string;
  idempotency_key?: string;
}

export interface UpgradeSubscriptionResponse {
  success: boolean;
  subscription_id?: string;
  payment_intent_id?: string;
  payment_instructions?: string;
  redirect_url?: string;
  amount?: number;
  from_plan?: SubscriptionTier;
  to_plan?: SubscriptionTier;
  billing_cycle?: BillingCycle; // NEW
  billing_phase?: BillingPhase; // NEW: always 'regular' for upgrades
  cycle_duration_days?: number; // NEW
  message?: string;
  already_processed?: boolean;
  error?: string;
}

// ============================================================================
// Schedule Downgrade Types
// ============================================================================

export interface ScheduleDowngradeRequest {
  new_plan_tier: SubscriptionTier;
  effective_date?: string;
}

export interface ScheduleDowngradeResponse {
  success: boolean;
  subscription_id?: string;
  from_plan?: SubscriptionTier;
  to_plan?: SubscriptionTier;
  effective_date?: string;
  message?: string;
  error?: string;
}

// ============================================================================
// Cancel Subscription Types
// ============================================================================

export interface CancelSubscriptionRequest {
  reason?: string;
}

export interface CancelSubscriptionResponse {
  success: boolean;
  subscription_id?: string;
  previous_plan?: SubscriptionTier;
  current_plan?: SubscriptionTier;
  plan?: SubscriptionTier;
  status?: string;
  expires_at?: string | null;
  upgrade_cancelled?: boolean;
  downgraded_immediately?: boolean;
  message?: string;
  error?: string;
}

// ============================================================================
// Resume Cancelled Subscription Types
// ============================================================================

export interface ResumeSubscriptionResponse {
  success: boolean;
  subscription_id?: string;
  plan?: SubscriptionTier;
  status?: string;
  expires_at?: string | null;
  days_remaining?: number;
  message?: string;
  error?: string;
  error_code?: string;
}

// ============================================================================
// Void Pending Payment Types
// ============================================================================

export interface VoidPendingPaymentResponse {
  success: boolean;
  message?: string;
  subscription_id?: string;
  status?: string;
  error?: string;
  current_status?: SubscriptionStatus;
  error_code?: string;
}

// ============================================================================
// Reactivate Subscription Types
// ============================================================================

export interface ReactivateSubscriptionResponse {
  success: boolean;
  subscription_id?: string;
  status?: SubscriptionStatus;
  message?: string;
  error?: string;
}

// ============================================================================
// Subscription Status/Capabilities Types
// ============================================================================

export interface SubscriptionStatusResponse {
  status: SubscriptionStatus;
  message: string;
  current_plan: SubscriptionTier;
  target_plan?: SubscriptionTier;
  previous_plan?: SubscriptionTier;
  access_level: SubscriptionTier;
  action_required: string | null;
  expires_at: string | null;
  expired_at?: string | null;
  days_remaining?: number | null;
}

export interface SubscriptionCapabilitiesResponse {
  tier: SubscriptionTier;
  capabilities: Record<string, unknown>;
  version_hash: string;
}

// ============================================================================
// Payment Retry Types (NEW)
// ============================================================================

export interface RetryPaymentRequest {
  purpose: 'subscription' | 'subscription_renewal' | 'subscription_upgrade' | 'domain' | 'theme' | 'checkout' | 'trial';
  reference_id: string;
  workspace_id: string;
  phone_number?: string;
  preferred_provider?: string;
}

export interface RetryPaymentResponse {
  success: boolean;
  payment_intent_id?: string;
  status?: string;
  amount?: number;
  currency?: string;
  provider?: string;
  mode?: string;
  redirect_url?: string;
  client_token?: string;
  qr_code?: string;
  instructions?: string;
  expires_at?: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
  completed_at?: string | null;
  error?: string;
  error_code?: string;
}

// Subscription-specific retry (simpler interface - user context from auth)
export interface RetrySubscriptionPaymentRequest {
  phone_number: string;
  provider?: string;  // default: 'fapshi'
  idempotency_key?: string;
}

export interface RetrySubscriptionPaymentResponse {
  success: boolean;
  subscription_id?: string;
  payment_intent_id?: string;
  payment_instructions?: string;
  redirect_url?: string;
  amount?: number;
  plan?: SubscriptionTier;
  billing_cycle?: BillingCycle;
  billing_phase?: BillingPhase;
  cycle_duration_days?: number;
  retry_count?: number;
  status?: string;
  expires_at?: string;
  existing_payment?: boolean;  // true if returning active PaymentIntent
  already_processed?: boolean;  // true if idempotency key match
  message?: string;
  error?: string;
  error_code?: string;
}

// ============================================================================
// Error Types
// ============================================================================

export interface SubscriptionError {
  error: string;
  error_code?: string;
  current_status?: SubscriptionStatus;
  subscription_id?: string;
  payment_intent_id?: string;
  trial_tier?: SubscriptionTier;
  trial_expires_at?: string | null;
  days_remaining?: number | null;
  grace_period_remaining_hours?: number;
  expires_at?: string | null;
  grace_period_ends_at?: string | null;
  days_until_renewal_window?: number;
  renewal_window_starts?: string | null;
  current_expires_at?: string | null;
  current_plan?: SubscriptionTier;
  scheduled_plan?: SubscriptionTier;
  scheduled_date?: string | null;
  suggestion?: string;
}

export type SubscriptionErrorCode =
  | 'ACTIVE_TRIAL_EXISTS'
  | 'PENDING_PAYMENT'
  | 'PAYMENT_EXPIRED_RETRY_AVAILABLE'
  | 'RENEWAL_OUTSIDE_WINDOW'
  | 'GRACE_PERIOD_EXPIRED'
  | 'SUBSCRIPTION_EXPIRED'
  | 'INVALID_STATUS_FOR_RENEWAL'
  | 'UPGRADE_OUTSIDE_RENEWAL_WINDOW'
  | 'INVALID_STATUS_FOR_VOID'
  | 'INVALID_STATUS_FOR_DOWNGRADE'
  | 'USE_CANCEL_ENDPOINT'
  | 'NOT_A_DOWNGRADE'
  | 'DOWNGRADE_ALREADY_SCHEDULED'
  | 'INVALID_DATE_FORMAT'
  | 'PAST_EFFECTIVE_DATE'
  | 'EARLY_EFFECTIVE_DATE'
  | 'NO_EXPIRY_DATE'
  | 'PLAN_NOT_FOUND'
  | 'GRACE_PERIOD_ACTIVE'
  | 'INVALID_PRICING_MODE' // NEW
  | 'INTRO_ALREADY_USED'; // NEW

// ============================================================================
// Subscription State Types (Discriminated Union)
// ============================================================================

export type SubscriptionState =
  | {
    status: 'idle';
    subscription: null;
    error: null;
    isLoading: false;
  }
  | {
    status: 'loading';
    subscription: null;
    error: null;
    isLoading: true;
  }
  | {
    status: 'loaded';
    subscription: SubscriptionStatusResponse;
    error: null;
    isLoading: false;
  }
  | {
    status: 'error';
    subscription: null;
    error: SubscriptionError;
    isLoading: false;
  };

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseSubscriptionReturn {
  state: SubscriptionState;
  createSubscription: (data: CreateSubscriptionRequest) => Promise<CreateSubscriptionResponse>;
  renewSubscription: (data: RenewSubscriptionRequest) => Promise<RenewSubscriptionResponse>;
  upgradeSubscription: (data: UpgradeSubscriptionRequest) => Promise<UpgradeSubscriptionResponse>;
  scheduleDowngrade: (data: ScheduleDowngradeRequest) => Promise<ScheduleDowngradeResponse>;
  cancelSubscription: (data: CancelSubscriptionRequest) => Promise<CancelSubscriptionResponse>;
  resumeSubscription: () => Promise<ResumeSubscriptionResponse>;
  voidPendingPayment: (subscriptionId: string) => Promise<VoidPendingPaymentResponse>;
  reactivateSubscription: () => Promise<ReactivateSubscriptionResponse>;
  retryPayment: (data: RetryPaymentRequest) => Promise<RetryPaymentResponse>;
  clearError: () => void;
}

export interface UseSubscriptionActionsReturn {
  createSubscription: (data: CreateSubscriptionRequest) => Promise<CreateSubscriptionResponse>;
  renewSubscription: (data: RenewSubscriptionRequest) => Promise<RenewSubscriptionResponse>;
  upgradeSubscription: (data: UpgradeSubscriptionRequest) => Promise<UpgradeSubscriptionResponse>;
  scheduleDowngrade: (data: ScheduleDowngradeRequest) => Promise<ScheduleDowngradeResponse>;
  cancelSubscription: (data: CancelSubscriptionRequest) => Promise<CancelSubscriptionResponse>;
  resumeSubscription: () => Promise<ResumeSubscriptionResponse>;
  voidPendingPayment: (subscriptionId: string) => Promise<VoidPendingPaymentResponse>;
  reactivateSubscription: () => Promise<ReactivateSubscriptionResponse>;
  retryPayment: (data: RetryPaymentRequest) => Promise<RetryPaymentResponse>;
  isLoading: boolean;
  error: SubscriptionError | null;
  clearError: () => void;
}

export interface UseSubscriptionStatusReturn {
  status: SubscriptionStatusResponse | null;
  isLoading: boolean;
  error: SubscriptionError | null;
  refetch: () => Promise<void>;
}

// ============================================================================
// Constants
// ============================================================================

export const SUBSCRIPTION_TIERS = {
  FREE: 'free',
  BEGINNER: 'beginner',
  PRO: 'pro',
  ENTERPRISE: 'enterprise',
} as const;

export const BILLING_CYCLES = {
  MONTHLY: 'monthly',
  YEARLY: 'yearly',
} as const;

export const PRICING_MODES = {
  INTRO: 'intro',
  REGULAR: 'regular',
} as const;

export const BILLING_PHASES = {
  INTRO: 'intro',
  REGULAR: 'regular',
} as const;

export const SUBSCRIPTION_STATUSES = {
  PENDING_PAYMENT: 'pending_payment',
  CHANGE_PENDING: 'change_pending',
  ACTIVE: 'active',
  EXPIRED: 'expired',
  GRACE_PERIOD: 'grace_period',
  SUSPENDED: 'suspended',
  CANCELLED: 'cancelled',
} as const;

export const SUBSCRIPTION_ERROR_CODES = {
  ACTIVE_TRIAL_EXISTS: 'ACTIVE_TRIAL_EXISTS',
  PENDING_PAYMENT: 'PENDING_PAYMENT',
  PAYMENT_EXPIRED_RETRY_AVAILABLE: 'PAYMENT_EXPIRED_RETRY_AVAILABLE',
  RENEWAL_OUTSIDE_WINDOW: 'RENEWAL_OUTSIDE_WINDOW',
  GRACE_PERIOD_EXPIRED: 'GRACE_PERIOD_EXPIRED',
  SUBSCRIPTION_EXPIRED: 'SUBSCRIPTION_EXPIRED',
  INVALID_STATUS_FOR_RENEWAL: 'INVALID_STATUS_FOR_RENEWAL',
  UPGRADE_OUTSIDE_RENEWAL_WINDOW: 'UPGRADE_OUTSIDE_RENEWAL_WINDOW',
  INVALID_STATUS_FOR_VOID: 'INVALID_STATUS_FOR_VOID',
  INVALID_STATUS_FOR_DOWNGRADE: 'INVALID_STATUS_FOR_DOWNGRADE',
  USE_CANCEL_ENDPOINT: 'USE_CANCEL_ENDPOINT',
  NOT_A_DOWNGRADE: 'NOT_A_DOWNGRADE',
  DOWNGRADE_ALREADY_SCHEDULED: 'DOWNGRADE_ALREADY_SCHEDULED',
  GRACE_PERIOD_ACTIVE: 'GRACE_PERIOD_ACTIVE',
  INVALID_PRICING_MODE: 'INVALID_PRICING_MODE', // NEW
  INTRO_ALREADY_USED: 'INTRO_ALREADY_USED', // NEW
} as const;
