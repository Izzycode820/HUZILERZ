/**
 * Subscription Authentication Context Types
 * Feature bitmap system aligned with backend JWTSubscriptionService
 */

import type { SubscriptionData } from './auth';

// ============================================================================
// Feature Bitmap System (O(1) checks)
// ============================================================================

// Aligned with backend FEATURE_BITMAP
export const FEATURE_BITMAP = {
  deployment: 1,           // 2^0 = 1
  analytics: 2,            // 2^1 = 2
  custom_domains: 4,       // 2^2 = 4
  white_label: 8,          // 2^3 = 8
  dedicated_support: 16,   // 2^4 = 16
  multiple_workspaces: 32, // 2^5 = 32
  advanced_analytics: 64,  // 2^6 = 64
  bulk_operations: 128,    // 2^7 = 128
} as const;

export type FeatureBitmap = number;

/**
 * O(1) feature checking function aligned with backend
 */
export const hasFeature = (bitmap: FeatureBitmap, feature: keyof typeof FEATURE_BITMAP): boolean =>
  Boolean(bitmap & FEATURE_BITMAP[feature]);

// ============================================================================
// Subscription Claims from JWT (uses auth.ts SubscriptionData as source of truth)
// ============================================================================

// Use SubscriptionData from auth.ts to avoid duplication
export type SubscriptionAuthClaims = SubscriptionData;

// REMOVED: Old boolean-based feature access - replaced with bitmap system

// ============================================================================
// Hook Return Types for Auth Context
// ============================================================================

export interface UseSubscriptionAuthReturn {
  subscription: SubscriptionAuthClaims | null;
  isLoading: boolean;
  error: string | null;
  hasFeature: (featureName: FeatureKey) => boolean; // Uses feature name, not bitmap
  hasAllFeatures: (features: FeatureKey[]) => boolean;
  hasAnyFeature: (features: FeatureKey[]) => boolean;
  getEnabledFeatures: () => FeatureKey[];
  isActiveSubscription: () => boolean;
  clearError: () => void;
}

export const SUBSCRIPTION_TYPES = {
  FREE: 'free',
  BEGINNING: 'beginning', // Aligned with backend
  PRO: 'pro',
  ENTERPRISE: 'enterprise',
} as const;

export const SUBSCRIPTION_STATUS = {
  ACTIVE: 'active',
  GRACE_PERIOD: 'grace_period', // Aligned with backend
  INACTIVE: 'inactive',
  EXPIRED: 'expired',
} as const;

export type SubscriptionType = typeof SUBSCRIPTION_TYPES[keyof typeof SUBSCRIPTION_TYPES];
export type SubscriptionStatusType = typeof SUBSCRIPTION_STATUS[keyof typeof SUBSCRIPTION_STATUS];
export type FeatureKey = keyof typeof FEATURE_BITMAP;