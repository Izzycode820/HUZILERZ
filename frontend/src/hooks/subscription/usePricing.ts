/**
 * Pricing Hook - 2024 Best Practices with Zustand
 * Custom hook layer for pricing store - handles standard and trial pricing
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { usePricingStore, pricingSelectors } from '../../stores/subscription/pricingStore'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UsePricingReturn {
  // State selectors (performance optimized)
  standardPricing: ReturnType<typeof pricingSelectors.standardPricing>
  trialPricing: ReturnType<typeof pricingSelectors.trialPricing>
  isLoading: boolean
  error: string | null

  // Computed state
  hasStandardPricing: boolean
  hasTrialPricing: boolean
  hasPricing: boolean
  freePlan: ReturnType<typeof pricingSelectors.freePlan>
  beginningPlan: ReturnType<typeof pricingSelectors.beginningPlan>
  proPlan: ReturnType<typeof pricingSelectors.proPlan>
  enterprisePlan: ReturnType<typeof pricingSelectors.enterprisePlan>
  beginningTrialPrice: ReturnType<typeof pricingSelectors.beginningTrialPrice>
  proTrialPrice: ReturnType<typeof pricingSelectors.proTrialPrice>
  enterpriseTrialPrice: ReturnType<typeof pricingSelectors.enterpriseTrialPrice>

  // Actions (stable references)
  getStandardPricing: () => Promise<void>
  getTrialPricing: () => void
  clearError: () => void
  clearPricing: () => void
}

// ============================================================================
// Main Pricing Hook
// ============================================================================

export function usePricing(): UsePricingReturn {
  // Selective store subscriptions (performance optimized)
  const standardPricing = usePricingStore(pricingSelectors.standardPricing)
  const trialPricing = usePricingStore(pricingSelectors.trialPricing)
  const isLoading = usePricingStore(pricingSelectors.isLoading)
  const error = usePricingStore(pricingSelectors.error)
  const hasStandardPricing = usePricingStore(pricingSelectors.hasStandardPricing)
  const hasTrialPricing = usePricingStore(pricingSelectors.hasTrialPricing)
  const hasPricing = usePricingStore(pricingSelectors.hasPricing)
  const freePlan = usePricingStore(pricingSelectors.freePlan)
  const beginningPlan = usePricingStore(pricingSelectors.beginningPlan)
  const proPlan = usePricingStore(pricingSelectors.proPlan)
  const enterprisePlan = usePricingStore(pricingSelectors.enterprisePlan)
  const beginningTrialPrice = usePricingStore(pricingSelectors.beginningTrialPrice)
  const proTrialPrice = usePricingStore(pricingSelectors.proTrialPrice)
  const enterpriseTrialPrice = usePricingStore(pricingSelectors.enterpriseTrialPrice)

  // Store actions (use stable selectors for performance)
  const getStandardPricing = usePricingStore(pricingSelectors.getStandardPricing)
  const getTrialPricing = usePricingStore(pricingSelectors.getTrialPricing)
  const clearError = usePricingStore(pricingSelectors.clearError)
  const clearPricing = usePricingStore(pricingSelectors.clearPricing)

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    standardPricing,
    trialPricing,
    isLoading,
    error,

    // Computed state
    hasStandardPricing,
    hasTrialPricing,
    hasPricing,
    freePlan,
    beginningPlan,
    proPlan,
    enterprisePlan,
    beginningTrialPrice,
    proTrialPrice,
    enterpriseTrialPrice,

    // Actions (stable)
    getStandardPricing,
    getTrialPricing,
    clearError,
    clearPricing,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for standard pricing only - minimal re-renders
 */
export function useStandardPricing() {
  return {
    standardPricing: usePricingStore(pricingSelectors.standardPricing),
    freePlan: usePricingStore(pricingSelectors.freePlan),
    beginningPlan: usePricingStore(pricingSelectors.beginningPlan),
    proPlan: usePricingStore(pricingSelectors.proPlan),
    enterprisePlan: usePricingStore(pricingSelectors.enterprisePlan),
    isLoading: usePricingStore(pricingSelectors.isLoading),
  }
}

/**
 * Hook for trial pricing only - minimal re-renders
 */
export function useTrialPricing() {
  return {
    trialPricing: usePricingStore(pricingSelectors.trialPricing),
    beginningTrialPrice: usePricingStore(pricingSelectors.beginningTrialPrice),
    proTrialPrice: usePricingStore(pricingSelectors.proTrialPrice),
    enterpriseTrialPrice: usePricingStore(pricingSelectors.enterpriseTrialPrice),
  }
}

/**
 * Hook for pricing actions only - no reactive state
 */
export function usePricingActions() {
  const clearError = usePricingStore(pricingSelectors.clearError)
  const clearPricing = usePricingStore(pricingSelectors.clearPricing)

  return { clearError, clearPricing }
}

// ============================================================================
// Default Export
// ============================================================================

export default usePricing