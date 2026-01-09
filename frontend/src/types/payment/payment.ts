/**
 * Payment Types
 * Aligned with backend PaymentService and webhook-driven payment flow
 * Features: Status polling, retry mechanism, USSD mobile money integration
 */

// ============================================================================
// Payment Status Types
// ============================================================================

export type PaymentStatus =
  | 'created'
  | 'pending'
  | 'success'
  | 'failed'
  | 'cancelled';

export type PaymentPurpose =
  | 'subscription'
  | 'subscription_renewal'
  | 'subscription_upgrade'
  | 'domain'
  | 'theme'
  | 'checkout'
  | 'trial';

export interface PaymentStatusResponse {
  id: string;
  workspace_id: string;
  amount: number;
  amount_decimal: string;
  currency: string;
  purpose: PaymentPurpose;
  provider_name: string;
  provider_intent_id: string;
  status: PaymentStatus;
  idempotency_key: string;
  created_at: string;
  updated_at: string;
  expires_at: string;
  completed_at: string | null;
  failure_reason: string | null;
  is_expired: boolean;
  metadata: Record<string, any>;
}

// ============================================================================
// Payment Instructions Types
// ============================================================================

export interface PaymentInstructions {
  message: string;
  steps?: string[];
  ussd_code?: string;
}

export interface CreatePaymentResponse {
  success: boolean;
  payment_intent_id: string;
  instructions: PaymentInstructions;
  redirect_url?: string;
  error?: string;
}

// ============================================================================
// Constants
// ============================================================================

export const PAYMENT_STATUSES = {
  CREATED: 'created',
  PENDING: 'pending',
  SUCCESS: 'success',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

export const PAYMENT_PURPOSES = {
  SUBSCRIPTION: 'subscription',
  SUBSCRIPTION_RENEWAL: 'subscription_renewal',
  SUBSCRIPTION_UPGRADE: 'subscription_upgrade',
  DOMAIN: 'domain',
  THEME: 'theme',
  CHECKOUT: 'checkout',
  TRIAL: 'trial',
} as const;

// ============================================================================
// Platform Payment Methods Types (NO workspace required)
// ============================================================================

export type PaymentMode = 'ussd' | 'redirect' | 'widget';

export interface MobileMoneyMethod {
  type: 'mobile-money';
  provider: string; // "MTN Mobile Money", "Orange Money"
  prefixes: string[]; // ["67", "650", "651", ...]
}

export interface PaymentCapabilities {
  display_name: string;
  payment_modes: PaymentMode[];
  supported_currencies: string[];
  supports_refunds: boolean;
  supports_partial_refunds: boolean;
  min_amount: number;
  max_amount: number;
  countries: string[];
  payment_methods: MobileMoneyMethod[];
  typical_settlement_time: string;
  webhook_support: boolean;
  webhook_retry: boolean;
}

export interface PaymentProvider {
  provider: string; // "fapshi", "mtn", "orange"
  display_name: string; // "Mobile Money (MTN / Orange)"
  description: string; // "Pay with MTN Mobile Money or Orange Money"
  modes: PaymentMode[];
  currencies: string[];
  icon: string | null;
  recommended: boolean;
  capabilities: PaymentCapabilities;
}

export interface PlatformPaymentMethodsResponse {
  methods: PaymentProvider[];
  count: number;
  purpose: string;
  cached: boolean;
}

// ============================================================================
// Payment Method Selection Types (for UI state)
// ============================================================================

export interface SelectedPaymentMethod {
  provider: string;
  displayName: string;
  mode: PaymentMode;
}
