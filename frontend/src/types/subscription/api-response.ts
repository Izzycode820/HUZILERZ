/**
 * API Response Types for Backend Integration
 * Based on actual backend response structure
 */

// Generic API response wrappers
export interface SubscriptionApiResponse<T = unknown> {
  readonly success: boolean;
  readonly data?: T;
  readonly message?: string;
  readonly timestamp?: string;
}

export interface SubscriptionApiError {
  readonly success: false;
  readonly error: string;
  readonly error_code?: string;
  readonly code?: string;
  readonly message?: string;
  readonly details?: string | Record<string, unknown>;
  readonly timestamp?: string;
  // Trial-specific fields
  readonly trial_id?: number;
  readonly trial_status?: string;
  readonly used_at?: string;
  readonly tier_used?: string;
  // Subscription-specific fields
  readonly current_tier?: string;
  readonly available_upgrades?: string[];
  readonly expired_at?: string;
  // Pending payment resumption (Stripe/Chargebee pattern)
  readonly pending_payment?: PendingPaymentInfo;
}

export interface PendingPaymentInfo {
  readonly payment_id: string;
  readonly expires_at: string | null;
  readonly time_remaining: number;
  readonly amount: number;
  readonly plan_tier: string;
  readonly created_at: string;
  // Note: payment_url removed - we use internal PaymentWizard UI, not external redirect
}

export interface PaginatedApiResponse<T> {
  readonly success: boolean;
  readonly data: T[];
  readonly pagination: {
    readonly page: number;
    readonly per_page: number;
    readonly total: number;
    readonly total_pages: number;
    readonly has_next: boolean;
    readonly has_previous: boolean;
  };
}

// Pricing API Response Structure
export interface PricingApiResponse {
  free: PlanPricingData;
  beginning: PlanPricingData;
  pro: PlanPricingData;
  enterprise: PlanPricingData;
}

export interface PlanPricingData {
  capabilities: {
    deployment_allowed: boolean;
    custom_domains_allowed: boolean;
    analytics_enabled: boolean;
    white_label_enabled: boolean;
    dedicated_support: boolean;
    api_access: boolean;
    priority_support: boolean;
  };
  limits: {
    storage_gb: number;
    bandwidth_gb: number;
    deployed_sites: number;
    workspaces: number;
    custom_domains: number;
    analytics_level: 'none' | 'core' | 'enhanced';
    support_level: 'community' | 'standard' | 'enterprise';
  };
  pricing: {
    base_price: number;
    final_price: number;
    currency: 'FCFA';
    period: 'month' | 'year';
    display: string;
    discount?: {
      original_price: number;
      discount_amount: number;
      final_price: number;
      discount_percentage: number;
    };
  };
}

// Feature Comparison API Response
export interface FeatureComparisonApiResponse {
  plans: Array<{
    id: string;
    name: string;
    price: {
      amount: number;
      display: string;
    };
    popular: boolean;
  }>;
  feature_categories: Array<{
    name: string;
    icon: string;
    features: Array<{
      plan_id: string;
      display: string;
      description: string;
      enabled: boolean;
    }>;
  }>;
}

// Transformed Plan Data for UI Components
export interface TransformedPlanData {
  id: string;
  tier: 'free' | 'beginning' | 'pro' | 'enterprise';
  name: string;
  description: string;
  price: {
    monthly: number;
    annually: number;
    display: string;
  };
  originalPrice?: number;
  discount?: {
    percentage: number;
    amount: number;
  };
  features: string[];
  resources: {
    storage_gb: number;
    bandwidth_gb: number;
    deployed_sites: number | 'unlimited';
    workspaces: number | 'unlimited';
    custom_domains: number | 'unlimited';
  };
  capabilities: {
    deployment_allowed: boolean;
    custom_domains_allowed: boolean;
    analytics_enabled: boolean;
    white_label_enabled: boolean;
    dedicated_support: boolean;
    api_access: boolean;
    priority_support: boolean;
  };
  support_level: 'community' | 'standard' | 'enterprise';
  popular: boolean;
  recommended?: boolean;
}


// API Endpoints
export const API_ENDPOINTS = {
  PRICING: '/api/subscriptions/pricing/',
  FEATURE_COMPARISON: '/api/subscriptions/pricing/comparison/',
  USER_ELIGIBILITY: '/api/subscriptions/pricing/eligibility/',
  DISCOUNT_CALCULATE: '/api/subscriptions/pricing/discount/calculate/',
} as const;