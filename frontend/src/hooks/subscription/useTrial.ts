/**
 * Trial Hook - 2024 Best Practices with Zustand
 * Custom hook layer for trial store - handles trial management and upgrades
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { useShallow } from 'zustand/react/shallow'
import { useTrialStore, trialSelectors } from '../../stores/subscription/trialStore'
import type {
  TrialCreateRequest,
  TrialCreateResponse,
  TrialUpgradeRequest,
  TrialUpgradeResponse,
} from '../../types/subscription'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseTrialReturn {
  // State selectors (performance optimized)
  trial: ReturnType<typeof trialSelectors.trial>
  currentTrial: ReturnType<typeof trialSelectors.currentTrial>
  upgradeInfo: ReturnType<typeof trialSelectors.upgradeInfo>
  pricing: ReturnType<typeof trialSelectors.pricing>
  isLoading: boolean
  error: string | null

  // Computed state
  isActive: boolean
  requiresPayment: boolean
  isExpired: boolean
  isConverted: boolean
  tier: ReturnType<typeof trialSelectors.tier>
  daysRemaining: ReturnType<typeof trialSelectors.daysRemaining>
  canUpgrade: boolean
  nextTierOptions: ReturnType<typeof trialSelectors.nextTierOptions>
  hasTrial: boolean
  amountPaid: number
  upgradeHistory: ReturnType<typeof trialSelectors.upgradeHistory>

  // Actions (stable references)
  createTrial: (request: TrialCreateRequest) => Promise<TrialCreateResponse>
  upgradeTrial: (request: TrialUpgradeRequest) => Promise<TrialUpgradeResponse>
  getTrialStatus: () => Promise<void>
  getTrialPricing: () => Promise<void>
  clearError: () => void
  clearTrial: () => void

  // Helper methods
  getUpgradeCost: (targetTier: string) => number | null
  getNextTierOptions: () => string[]
}

// ============================================================================
// Main Trial Hook
// ============================================================================

export function useTrial(): UseTrialReturn {
  // Selective store subscriptions (performance optimized)
  const trial = useTrialStore(trialSelectors.trial)
  const currentTrial = useTrialStore(trialSelectors.currentTrial)
  const upgradeInfo = useTrialStore(trialSelectors.upgradeInfo)
  const pricing = useTrialStore(trialSelectors.pricing)
  const isLoading = useTrialStore(trialSelectors.isLoading)
  const error = useTrialStore(trialSelectors.error)
  const isActive = useTrialStore(trialSelectors.isActive)
  const requiresPayment = useTrialStore(trialSelectors.requiresPayment)
  const isExpired = useTrialStore(trialSelectors.isExpired)
  const isConverted = useTrialStore(trialSelectors.isConverted)
  const tier = useTrialStore(trialSelectors.tier)
  const daysRemaining = useTrialStore(trialSelectors.daysRemaining)
  const canUpgrade = useTrialStore(trialSelectors.canUpgrade)
  const nextTierOptions = useTrialStore(useShallow(trialSelectors.nextTierOptions))
  const hasTrial = useTrialStore(trialSelectors.hasTrial)
  const amountPaid = useTrialStore(trialSelectors.amountPaid)
  const upgradeHistory = useTrialStore(useShallow(trialSelectors.upgradeHistory))

  // Store actions (use stable selectors for performance)
  const createTrialAction = useTrialStore(trialSelectors.createTrial)
  const upgradeTrialAction = useTrialStore(trialSelectors.upgradeTrial)
  const getTrialStatusAction = useTrialStore(trialSelectors.getTrialStatus)
  const getTrialPricingAction = useTrialStore(trialSelectors.getTrialPricing)
  const clearError = useTrialStore(trialSelectors.clearError)
  const clearTrial = useTrialStore(trialSelectors.clearTrial)
  const getUpgradeCost = useTrialStore(trialSelectors.getUpgradeCost)
  const getNextTierOptions = useTrialStore(trialSelectors.getNextTierOptions)

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const createTrial = useCallback(async (request: TrialCreateRequest): Promise<TrialCreateResponse> => {
    return createTrialAction(request)
  }, [createTrialAction])

  const upgradeTrial = useCallback(async (request: TrialUpgradeRequest): Promise<TrialUpgradeResponse> => {
    return upgradeTrialAction(request)
  }, [upgradeTrialAction])

  const getTrialStatus = useCallback(async (): Promise<void> => {
    return getTrialStatusAction()
  }, [getTrialStatusAction])

  const getTrialPricing = useCallback(async (): Promise<void> => {
    return getTrialPricingAction()
  }, [getTrialPricingAction])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    trial,
    currentTrial,
    upgradeInfo,
    pricing,
    isLoading,
    error,

    // Computed state
    isActive,
    requiresPayment,
    isExpired,
    isConverted,
    tier,
    daysRemaining,
    canUpgrade,
    nextTierOptions,
    hasTrial,
    amountPaid,
    upgradeHistory,

    // Actions (stable)
    createTrial,
    upgradeTrial,
    getTrialStatus,
    getTrialPricing,
    clearError,
    clearTrial,

    // Helper methods
    getUpgradeCost,
    getNextTierOptions,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for trial status only - minimal re-renders
 */
export function useTrialStatus() {
  return {
    isActive: useTrialStore(trialSelectors.isActive),
    requiresPayment: useTrialStore(trialSelectors.requiresPayment),
    isExpired: useTrialStore(trialSelectors.isExpired),
    hasTrial: useTrialStore(trialSelectors.hasTrial),
    isLoading: useTrialStore(trialSelectors.isLoading),
  }
}

/**
 * Hook for trial data only - minimal re-renders
 */
export function useTrialData() {
  return {
    trial: useTrialStore(trialSelectors.trial),
    tier: useTrialStore(trialSelectors.tier),
    daysRemaining: useTrialStore(trialSelectors.daysRemaining),
    canUpgrade: useTrialStore(trialSelectors.canUpgrade),
    nextTierOptions: useTrialStore(trialSelectors.nextTierOptions),
  }
}

/**
 * Hook for trial actions only - no reactive state
 */
export function useTrialActions() {
  const clearError = useTrialStore(trialSelectors.clearError)
  const clearTrial = useTrialStore(trialSelectors.clearTrial)

  return { clearError, clearTrial }
}

// ============================================================================
// Default Export
// ============================================================================

export default useTrial