/**
 * Subscription Plans and Pricing Types
 * Types matching exact backend /api/subscriptions/pricing/ response
 */

// Plan capabilities from backend
export interface PlanCapabilities {
  readonly deployment_allowed: boolean;
  readonly custom_domains_allowed: boolean;
  readonly analytics_enabled: boolean;
  readonly white_label_enabled: boolean;
  readonly dedicated_support: boolean;
  readonly api_access: boolean;
  readonly priority_support: boolean;
}

// Plan limits from backend
export interface PlanLimits {
  readonly storage_gb: number;
  readonly bandwidth_gb: number;
  readonly deployed_sites: number;
  readonly workspaces: number;
  readonly custom_domains: number;
  readonly analytics_level: 'none' | 'core' | 'enhanced';
  readonly support_level: 'community' | 'standard' | 'enterprise';
}

// Plan pricing structure from backend
export interface PlanPricing {
  readonly monthly: {
    readonly base_price: number;
    readonly currency: 'FCFA';
    readonly period: 'month';
    readonly display: string;
  };
  readonly yearly: {
    readonly base_price: number;
    readonly discounted_price: number;
    readonly savings: number;
    readonly savings_percentage: number;
    readonly currency: 'FCFA';
    readonly period: 'year';
    readonly display: string;
  };
  readonly discount?: {
    readonly type: 'yearly_billing';
    readonly name: string;
    readonly available: boolean;
  };
}

// Individual plan structure
export interface PricingPlan {
  readonly name: string;
  readonly tagline: string;
  readonly description: string;
  readonly capabilities: PlanCapabilities;
  readonly limits: PlanLimits;
  readonly pricing: PlanPricing;
}

/**
 * Complete pricing response from backend
 * GET /api/subscription/pricing/
 */
export interface PricingResponse {
  readonly free: PricingPlan;
  readonly beginning: PricingPlan;
  readonly pro: PricingPlan;
  readonly enterprise: PricingPlan;
}

/**
 * Helper type for plan tier keys
 */
export type PlanTierKey = keyof PricingResponse;

/**
 * Plan resources for feature gating
 */
export const PlanResources = {
  FREE: {
    workspaces: 1,
    sites_per_workspace: 0,
    storage_gb: 0.5,
    bandwidth_gb: 0,
    custom_domains: 0,
    analytics_level: 'none',
    support_level: 'community',
  },
  BEGINNING: {
    workspaces: 1,
    sites_per_workspace: 1,
    storage_gb: 2,
    bandwidth_gb: 15,
    custom_domains: 1,
    analytics_level: 'none',
    support_level: 'standard',
  },
  PRO: {
    workspaces: 0,
    sites_per_workspace: 5,
    storage_gb: 5,
    bandwidth_gb: 50,
    custom_domains: 3,
    analytics_level: 'core',
    support_level: 'standard',
  },
  ENTERPRISE: {
    workspaces: 0,
    sites_per_workspace: 0,
    storage_gb: 10,
    bandwidth_gb: 200,
    custom_domains: 0,
    analytics_level: 'enhanced',
    support_level: 'enterprise',
  },
} as const;

/**
 * Plan pricing values for calculations
 */
export const PlanPricingValues = {
  free: {
    monthly: 0,
    yearly: 0,
  },
  beginning: {
    monthly: 10000,
    yearly: 102000, // 8500/month * 12
  },
  pro: {
    monthly: 25000,
    yearly: 255000, // 21250/month * 12
  },
  enterprise: {
    monthly: 50000,
    yearly: 510000, // 42500/month * 12
  },
} as const;