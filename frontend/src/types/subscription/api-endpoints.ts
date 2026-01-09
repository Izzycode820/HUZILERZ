/**
 * API Endpoint Types - Missing Implementations
 * Types for endpoints that exist in backend but were missing from frontend
 * All types match actual backend response structures
 */

import { PlanTierType } from './subscription';
import { PaymentStatusType } from './payment';
import { TrialTierType } from './trials';

/**
 * Upgrade Prompts Response
 * GET /api/subscription/pricing/upgrade-prompts/
 */
export interface UpgradePromptsResponse {
  readonly current_tier: PlanTierType;
  readonly upgrade_prompts: Array<{
    readonly id: number;
    readonly name: string;
    readonly message: string;
    readonly to_tier: PlanTierType;
    readonly priority: number;
    readonly trigger_condition: string;
    readonly preview_text: string;
    readonly comparison_text: string;
    readonly psychology_type: string;
  }>;
}

/**
 * Feature Comparison Response
 * GET /api/subscription/pricing/comparison/
 */
export interface FeatureComparisonResponse {
  readonly plans: Array<{
    readonly id: string;
    readonly name: string;
    readonly price: {
      readonly amount: number;
      readonly display: string;
    };
    readonly popular: boolean;
  }>;
  readonly feature_categories: Array<{
    readonly name: string;
    readonly icon?: string;
    readonly features: Array<{
      readonly plan_id?: string;
      readonly display?: string;
      readonly description: string;
      readonly enabled?: boolean;
      readonly name?: string;
      readonly values?: Record<string, string | boolean | number>;
    }>;
  }>;
}

/**
 * Payment Methods Response
 * GET /api/subscription/payment/methods/
 */
export interface PaymentMethodsResponse {
  readonly payment_methods: Array<{
    readonly id: string;
    readonly display_name: string;
    readonly phone_number: string;
    readonly is_default: boolean;
    readonly gateway: string;
    readonly status: string;
  }>;
  readonly gateway_status: Record<string, unknown>;
  readonly supported_types: Array<'subscription' | 'trial'>;
  readonly available_gateways: string[];
}

/**
 * Subscription History Response
 * GET /api/subscription/history/
 */
export interface SubscriptionHistoryResponse {
  readonly history: Array<HistoryEntry>;
  readonly statistics: {
    readonly total_payments: number;
    readonly total_spent: number;
    readonly currency: 'FCFA';
    readonly trials_used: number;
    readonly successful_conversions: number;
    readonly conversion_rate: number;
  };
  readonly current_status: {
    readonly subscription: {
      readonly plan_name: string;
      readonly plan_tier: PlanTierType;
      readonly status: string;
      readonly expires_at: string;
      readonly is_active: boolean;
    } | null;
    readonly trial: {
      readonly trial_id: string;
      readonly plan_name: string;
      readonly expires_at: string;
      readonly days_remaining: number;
    } | null;
    readonly has_active_subscription: boolean;
    readonly has_active_trial: boolean;
  };
  readonly pagination: {
    readonly showing: number;
    readonly total_available: number;
  };
}

export type HistoryEntry = PaymentHistoryEntry | TrialHistoryEntry;

export interface PaymentHistoryEntry {
  readonly id: string;
  readonly type: 'payment';
  readonly action: string;
  readonly amount_paid: number;
  readonly currency: 'FCFA';
  readonly payment_method: string;
  readonly payment_type: string;
  readonly gateway: string;
  readonly status: PaymentStatusType;
  readonly created_at: string;
  readonly notes: string;
}

export interface TrialHistoryEntry {
  readonly id: string;
  readonly type: 'trial';
  readonly action: string;
  readonly amount_paid: number;
  readonly currency: 'FCFA';
  readonly payment_method: string;
  readonly payment_type: string;
  readonly gateway: string;
  readonly status: string;
  readonly created_at: string;
  readonly trial_details: {
    readonly plan_name: string;
    readonly plan_tier: TrialTierType;
    readonly duration_days: number;
    readonly expires_at: string;
    readonly usage_summary: Record<string, unknown>;
  };
  readonly notes: string;
  readonly conversion_details?: {
    readonly converted_at: string;
    readonly subscription_id: string;
    readonly converted_to_plan: string;
  };
}

/**
 * Renew Subscription Request/Response
 * POST /api/subscription/renew/
 */
export interface RenewSubscriptionRequest {
  readonly payment_method_id: string;
  readonly days?: number;
}

export interface RenewSubscriptionResponse {
  readonly success: boolean;
  readonly message?: string;
  readonly subscription?: {
    readonly expires_at: string;
    readonly status: string;
  };
  readonly payment?: {
    readonly id: string;
    readonly amount: number;
    readonly status: string;
  };
  readonly error?: string;
  readonly payment_id?: string;
}

/**
 * Schedule Downgrade Request/Response
 * POST /api/subscription/schedule-downgrade/
 */
export interface ScheduleDowngradeRequest {
  readonly new_plan_tier: PlanTierType;
}

export interface ScheduleDowngradeResponse {
  readonly success: boolean;
  readonly message: string;
  readonly subscription: {
    readonly current_plan: PlanTierType;
    readonly pending_plan: PlanTierType;
    readonly effective_date: string;
  };
}

/**
 * Reactivate Subscription Request/Response
 * POST /api/subscription/reactivate/
 */
export interface ReactivateSubscriptionRequest {
  readonly payment_method_id: string;
}

export interface ReactivateSubscriptionResponse {
  readonly success: boolean;
  readonly message?: string;
  readonly subscription?: {
    readonly status: string;
    readonly expires_at: string;
  };
  readonly error?: string;
}

/**
 * Batch Discount Calculation
 * POST /api/subscription/batch/discount-calculation/
 */
export interface BatchDiscountCalculationRequest {
  readonly plans: PlanTierType[];
  readonly template_purchase?: boolean;
  readonly seasonal_code?: string;
}

export interface BatchDiscountCalculationResponse {
  readonly batch_results: Array<{
    readonly plan_tier: PlanTierType;
    readonly success: boolean;
    readonly discount?: {
      readonly original_amount: number;
      readonly final_amount: number;
      readonly discount_amount: number;
      readonly discount_percentage: number;
      readonly discount_name: string;
    };
    readonly error?: string;
  }>;
  readonly total_plans: number;
  readonly successful_calculations: number;
  readonly failed_calculations: number;
}

/**
 * Batch Payment Status Check
 * POST /api/subscription/batch/payment-status/
 */
export interface BatchPaymentStatusCheckRequest {
  readonly payment_ids: string[];
}

export interface BatchPaymentStatusCheckResponse {
  readonly batch_results: Array<{
    readonly payment_id: string;
    readonly success: boolean;
    readonly status?: PaymentStatusType;
    readonly amount?: number;
    readonly payment_type?: string;
    readonly gateway_used?: string;
    readonly created_at?: string;
    readonly completed_at?: string | null;
    readonly can_retry?: boolean;
    readonly error?: string;
  }>;
  readonly total_requested: number;
  readonly found_payments: number;
  readonly not_found_payments: number;
}

/**
 * Batch Feature Availability Check
 * POST /api/subscription/batch/feature-availability/
 */
export interface BatchFeatureAvailabilityRequest {
  readonly features: string[];
}

export interface BatchFeatureAvailabilityResponse {
  readonly feature_availability: Record<string, {
    readonly available: boolean;
    readonly current_tier: PlanTierType;
    readonly required_tiers: PlanTierType[];
    readonly usage_info?: {
      readonly is_over_limit: boolean;
    } | null;
    readonly upgrade_required: boolean;
    readonly minimum_required_tier: PlanTierType | null;
  }>;
  readonly current_subscription_tier: PlanTierType;
  readonly has_active_subscription: boolean;
  readonly total_features_checked: number;
}

/**
 * Batch Usage Analytics
 * POST /api/subscription/batch/usage-analytics/
 */
export interface BatchUsageAnalyticsRequest {
  readonly resource_types?: string[];
  readonly date_range?: number;
}

export interface BatchUsageAnalyticsResponse {
  readonly usage_analytics: Record<string, {
    readonly current_usage: number;
    readonly tier_limit: number;
    readonly usage_percentage: number;
    readonly limit_exceeded: boolean;
    readonly approaching_limit: boolean;
    readonly remaining_allowance: number;
    readonly last_updated: string | null;
  }>;
  readonly subscription_tier: PlanTierType;
  readonly date_range_days: number;
  readonly total_resource_types: number;
}

/**
 * Batch Subscription Comparison
 * POST /api/subscription/batch/subscription-comparison/
 */
export interface BatchSubscriptionComparisonRequest {
  readonly plans?: PlanTierType[];
  readonly include_pricing?: boolean;
  readonly include_features?: boolean;
  readonly include_discounts?: boolean;
}

export interface BatchSubscriptionComparisonResponse {
  readonly current_tier: PlanTierType;
  readonly plans: Record<PlanTierType, {
    readonly tier: PlanTierType;
    readonly name: string;
    readonly description: string;
    readonly is_current_plan: boolean;
    readonly is_upgrade: boolean;
    readonly is_downgrade: boolean;
    readonly pricing?: {
      readonly price_fcfa: number;
      readonly price_usd: number;
      readonly display: string;
    };
    readonly discount?: {
      readonly available: boolean;
      readonly original_price: number;
      readonly discounted_price: number;
      readonly savings: number;
      readonly discount_percentage: number;
    };
    readonly features?: {
      readonly deployment_allowed: boolean;
      readonly max_workspaces: number;
      readonly sites_limit: number;
      readonly storage_gb: number;
      readonly bandwidth_gb: number;
      readonly custom_domains: number;
      readonly analytics_level: string;
      readonly white_label_enabled: boolean;
      readonly dedicated_support: boolean;
    };
    readonly error?: string;
  }>;
  readonly recommendations: Array<{
    readonly type: 'upgrade' | 'downgrade';
    readonly target_tier: PlanTierType;
    readonly reason: string;
    readonly benefits: string[];
  }>;
}