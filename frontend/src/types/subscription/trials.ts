import { z } from 'zod';

/**
 * Trial Management Types
 * Types matching exact backend trial API responses
 */

// Trial status from backend
export const TrialStatus = {
  ACTIVE: 'active',
  PENDING_PAYMENT: 'pending_payment',
  EXPIRED: 'expired',
  CONVERTED: 'converted',
  CANCELLED: 'cancelled',
} as const;

export type TrialStatusType = typeof TrialStatus[keyof typeof TrialStatus];

// Trial tier types
export const TrialTier = {
  BEGINNING: 'beginning',
  PRO: 'pro',
  ENTERPRISE: 'enterprise',
} as const;

export type TrialTierType = typeof TrialTier[keyof typeof TrialTier];

/**
 * Create Trial Request
 * POST /api/subscriptions/trials/create/
 */
export const TrialCreateSchema = z.object({
  tier: z.enum(['beginning', 'pro', 'enterprise']),
});

export interface TrialCreateRequest {
  readonly tier: TrialTierType;
}

/**
 * Create Trial Response
 * Backend response after creating trial
 */
export interface TrialCreateResponse {
  readonly success: boolean;
  readonly message: string;
  readonly trial: {
    readonly id: number;
    readonly tier: TrialTierType;
    readonly status: TrialStatusType;
    readonly amount_due: number;
    readonly requires_payment: boolean;
  };
  readonly next_steps: {
    readonly action: 'initiate_payment';
    readonly endpoint: '/payment/initiate/';
    readonly payment_type: 'trial';
    readonly amount: number;
  };
}

/**
 * Upgrade Trial Request
 * POST /api/subscriptions/trials/upgrade/
 */
export const TrialUpgradeSchema = z.object({
  target_tier: z.enum(['beginning', 'pro', 'enterprise']),
});

export interface TrialUpgradeRequest {
  readonly target_tier: TrialTierType;
}

/**
 * Upgrade Trial Response
 * Returns differential pricing for upgrade
 */
export interface TrialUpgradeResponse {
  readonly success: boolean;
  readonly message: string;
  readonly upgrade: {
    readonly trial_id: number;
    readonly current_tier: TrialTierType;
    readonly target_tier: TrialTierType;
    readonly status: TrialStatusType;
    readonly upgrade_cost: number;
    readonly requires_payment: boolean;
  };
  readonly next_steps: {
    readonly action: 'initiate_payment';
    readonly endpoint: '/payment/initiate/';
    readonly payment_type: 'trial';
    readonly amount: number;
  };
}

/**
 * Trial Status Response
 * GET /api/subscriptions/trials/status/
 */
export interface TrialStatusResponse {
  readonly success: boolean;
  readonly trial: {
    readonly id: number;
    readonly tier: TrialTierType;
    readonly status: TrialStatusType;
    readonly amount_paid: number;
    readonly started_at: string;
    readonly expires_at: string;
    readonly days_remaining: number;
    readonly can_upgrade: boolean;
    readonly next_tier_options: TrialTierType[];
    readonly upgrade_history: Array<{
      readonly from_tier: TrialTierType;
      readonly to_tier: TrialTierType;
      readonly amount_paid: number;
      readonly upgraded_at: string;
    }>;
  } | null;
}

/**
 * Trial Pricing Configuration
 * Based on backend trial pricing (30-day period)
 */
export const TrialPricing = {
  beginning: 2000,
  pro: 5000,
  enterprise: 10000,
} as const;

/**
 * Calculate upgrade cost between trial tiers
 */
export function calculateTrialUpgradeCost(
  currentTier: TrialTierType,
  targetTier: TrialTierType
): number {
  return TrialPricing[targetTier] - TrialPricing[currentTier];
}

/**
 * Type guard to check if trial is active
 */
export function isTrialActive(status: TrialStatusType): boolean {
  return status === TrialStatus.ACTIVE;
}

/**
 * Type guard to check if trial requires payment
 */
export function trialRequiresPayment(status: TrialStatusType): boolean {
  return status === TrialStatus.PENDING_PAYMENT;
}

/**
 * Type guard to check if trial can be upgraded
 */
export function canUpgradeTrial(currentTier: TrialTierType, targetTier: TrialTierType): boolean {
  const tierOrder: TrialTierType[] = ['beginning', 'pro', 'enterprise'];
  return tierOrder.indexOf(targetTier) > tierOrder.indexOf(currentTier);
}