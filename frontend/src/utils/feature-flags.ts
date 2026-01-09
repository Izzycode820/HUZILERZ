import { FEATURE_BITMAP, type FeatureBitmap, type FeatureKey } from '../types/authentication/subscription';

/**
 * Feature Flag Utilities
 * Aligned with backend JWTSubscriptionService for O(1) feature checking
 */

/**
 * Check if a feature is enabled using bitmap (O(1) operation)
 * @param bitmap - Feature bitmap from JWT subscription claims
 * @param feature - Feature key to check
 * @returns boolean indicating if feature is enabled
 */
export function hasFeature(bitmap: FeatureBitmap, feature: FeatureKey): boolean {
  return Boolean(bitmap & FEATURE_BITMAP[feature]);
}

/**
 * Check multiple features at once
 * @param bitmap - Feature bitmap from JWT subscription claims
 * @param features - Array of feature keys to check
 * @returns boolean indicating if ALL features are enabled
 */
export function hasAllFeatures(bitmap: FeatureBitmap, features: FeatureKey[]): boolean {
  return features.every(feature => hasFeature(bitmap, feature));
}

/**
 * Check if any of the specified features are enabled
 * @param bitmap - Feature bitmap from JWT subscription claims
 * @param features - Array of feature keys to check
 * @returns boolean indicating if ANY feature is enabled
 */
export function hasAnyFeature(bitmap: FeatureBitmap, features: FeatureKey[]): boolean {
  return features.some(feature => hasFeature(bitmap, feature));
}

/**
 * Get list of all enabled features from bitmap
 * @param bitmap - Feature bitmap from JWT subscription claims
 * @returns Array of enabled feature keys
 */
export function getEnabledFeatures(bitmap: FeatureBitmap): FeatureKey[] {
  const enabledFeatures: FeatureKey[] = [];

  for (const [featureName, bitValue] of Object.entries(FEATURE_BITMAP)) {
    if (bitmap & bitValue) {
      enabledFeatures.push(featureName as FeatureKey);
    }
  }

  return enabledFeatures;
}

/**
 * Create a feature bitmap from an array of feature names
 * @param features - Array of feature keys to enable
 * @returns Feature bitmap with specified features enabled
 */
export function createFeatureBitmap(features: FeatureKey[]): FeatureBitmap {
  return features.reduce((bitmap, feature) => bitmap | FEATURE_BITMAP[feature], 0);
}

/**
 * Feature gate component utility
 * @param bitmap - Feature bitmap from JWT subscription claims
 * @param feature - Feature key to check
 * @param children - Content to render if feature is enabled
 * @param fallback - Content to render if feature is disabled
 * @returns JSX element or null
 */
export function withFeatureGate<T>(
  bitmap: FeatureBitmap,
  feature: FeatureKey,
  children: T,
  fallback?: T
): T | null {
  return hasFeature(bitmap, feature) ? children : (fallback ?? null);
}