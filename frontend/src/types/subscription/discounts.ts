import { z } from 'zod';

// Discount types matching Django backend
export const DISCOUNT_TYPES = {
  PERCENTAGE: 'percentage',
  FIXED_AMOUNT: 'fixed_amount',
  FREE_TRIAL: 'free_trial',
  BULK_DISCOUNT: 'bulk_discount',
} as const;

export type DiscountType = typeof DISCOUNT_TYPES[keyof typeof DISCOUNT_TYPES];

// Discount validation schema
export const DiscountCodeSchema = z.string()
  .min(3, 'Discount code must be at least 3 characters')
  .max(50, 'Discount code cannot exceed 50 characters')
  .regex(/^[A-Z0-9_-]+$/i, 'Discount code can only contain letters, numbers, hyphens, and underscores');

// Main discount interfaces matching Django backend
export interface DiscountInfo {
  readonly code: string;
  readonly type: DiscountType;
  readonly value: number; // percentage (0-100) or fixed amount in FCFA
  readonly max_discount_amount?: number; // maximum discount in FCFA for percentage discounts
  readonly minimum_order_amount?: number; // minimum subscription amount required
  readonly is_active: boolean;
  readonly valid_from: string;
  readonly valid_until?: string;
  readonly usage_limit?: number;
  readonly usage_count: number;
  readonly description: string;
  readonly terms_conditions?: string;
  readonly available?: boolean;
}

// Extended discount details with user-specific info
export interface DiscountDetail extends DiscountInfo {
  readonly user_usage_count: number;
  readonly can_be_used: boolean;
  readonly restriction_reason?: string;
  readonly applicable_tiers: ('beginning' | 'pro' | 'enterprise')[];
  readonly stackable_with: string[];
  readonly priority_order: number;
}

// Applied discount result
export interface AppliedDiscount {
  readonly discount_code: string;
  readonly original_amount: number;
  readonly discount_amount: number;
  readonly final_amount: number;
  readonly discount_percentage: number;
  readonly savings_fcfa: number;
}

// Stacked discounts (multiple discounts applied)
export interface StackedDiscounts {
  readonly original_amount: number;
  readonly total_discount_amount: number;
  readonly final_amount: number;
  readonly total_savings_fcfa: number;
  readonly applied_discounts: AppliedDiscount[];
  readonly stacking_order: string[];
}

// Pricing calculation with discounts
export interface PricingCalculation {
  readonly base_price_fcfa: number;
  readonly base_price_usd: number;
  readonly discounts: StackedDiscounts | null;
  readonly final_price_fcfa: number;
  readonly final_price_usd: number;
  readonly currency: 'FCFA' | 'USD';
  readonly billing_period: 'monthly' | 'quarterly' | 'annually';
  readonly tax_amount?: number;
  readonly total_amount: number;
}

// Discount validation response
export interface DiscountValidationResult {
  readonly valid: boolean;
  readonly discount?: DiscountDetail;
  readonly error_message?: string;
  readonly suggestions?: string[];
  readonly estimated_savings?: {
    readonly fcfa: number;
    readonly percentage: number;
  };
}

// Bulk discount structure
export interface BulkDiscountTier {
  readonly min_quantity: number;
  readonly max_quantity?: number;
  readonly discount_percentage: number;
  readonly description: string;
}

export interface BulkDiscount extends DiscountInfo {
  readonly tiers: BulkDiscountTier[];
  readonly applies_to: 'workspaces' | 'sites' | 'users' | 'storage_gb';
}

// Seasonal/promotional discount
export interface PromotionalDiscount extends DiscountInfo {
  readonly promotion_name: string;
  readonly banner_text?: string;
  readonly urgency_message?: string;
  readonly countdown_ends_at?: string;
  readonly auto_apply: boolean;
  readonly target_audience: 'new_users' | 'existing_users' | 'churned_users' | 'all';
}

// User discount eligibility
export interface UserDiscountEligibility {
  readonly user_id: number;
  readonly available_discounts: DiscountDetail[];
  readonly auto_applied_discounts: string[];
  readonly recommended_discounts: DiscountDetail[];
  readonly total_lifetime_savings: number;
  readonly current_tier_discounts: DiscountDetail[];
}

// Discount analytics
export interface DiscountAnalytics {
  readonly discount_code: string;
  readonly total_usage: number;
  readonly total_revenue_impact: number;
  readonly average_order_value: number;
  readonly conversion_rate: number;
  readonly user_retention_impact: number;
  readonly popular_combinations: string[];
}

// Constants for discount limits (from Django backend)
export const DISCOUNT_LIMITS = {
  MAX_STACKED_DISCOUNTS: 3,
  MAX_TOTAL_DISCOUNT_PERCENTAGE: 80,
  MIN_ORDER_AMOUNT_FCFA: 1000,
  MAX_DISCOUNT_AMOUNT_FCFA: 50000,
} as const;