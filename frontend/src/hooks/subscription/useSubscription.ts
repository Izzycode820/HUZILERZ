/**
 * Subscription Hook - 2024 Best Practices with Zustand
 * Custom hook layer for subscription store - provides clean interface and performance
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 * Aligned with backend subscription_views.py and PaymentService
 */

import { useCallback } from 'react'
import { useSubscriptionStore, subscriptionSelectors } from '../../stores/subscription/subscriptionStore'
import type {
  CreateSubscriptionRequest,
  CreateSubscriptionResponse,
  RenewSubscriptionRequest,
  RenewSubscriptionResponse,
  UpgradeSubscriptionRequest,
  UpgradeSubscriptionResponse,
  ScheduleDowngradeRequest,
  ScheduleDowngradeResponse,
  CancelSubscriptionRequest,
  CancelSubscriptionResponse,
  ResumeSubscriptionResponse,
  VoidPendingPaymentResponse,
  ReactivateSubscriptionResponse,
  RetrySubscriptionPaymentRequest,
  RetrySubscriptionPaymentResponse,
  SubscriptionError,
} from '../../types/subscription/subscription'
import type { SubscriptionData } from '../../types/authentication/auth'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseSubscriptionReturn {
  // State selectors (performance optimized)
  jwtSubscription: SubscriptionData | null
  isLoading: boolean
  error: SubscriptionError | null

  // Computed state (derived from JWT - minimal claims only)
  tier: ReturnType<typeof subscriptionSelectors.tier>
  status: ReturnType<typeof subscriptionSelectors.status>
  expiresAt: ReturnType<typeof subscriptionSelectors.expiresAt>
  capabilitiesVersion: ReturnType<typeof subscriptionSelectors.capabilitiesVersion>
  billingCycle: ReturnType<typeof subscriptionSelectors.billingCycle>
  currency: ReturnType<typeof subscriptionSelectors.currency>
  isActive: boolean

  // Actions (stable references)
  createSubscription: (request: CreateSubscriptionRequest) => Promise<CreateSubscriptionResponse>
  renewSubscription: (request: RenewSubscriptionRequest) => Promise<RenewSubscriptionResponse>
  upgradeSubscription: (request: UpgradeSubscriptionRequest) => Promise<UpgradeSubscriptionResponse>
  scheduleDowngrade: (request: ScheduleDowngradeRequest) => Promise<ScheduleDowngradeResponse>
  cancelActiveSubscription: (request?: CancelSubscriptionRequest) => Promise<CancelSubscriptionResponse>
  resumeSubscription: () => Promise<ResumeSubscriptionResponse>
  voidPendingPayment: (subscriptionId: string) => Promise<VoidPendingPaymentResponse>
  reactivateSubscription: () => Promise<ReactivateSubscriptionResponse>
  retrySubscriptionPayment: (request: RetrySubscriptionPaymentRequest) => Promise<RetrySubscriptionPaymentResponse>
  clearError: () => void
}

// ============================================================================
// Main Subscription Hook
// ============================================================================

export function useSubscription(): UseSubscriptionReturn {
  // Selective store subscriptions (performance optimized)
  const jwtSubscription = useSubscriptionStore(subscriptionSelectors.jwtSubscription)
  const isLoading = useSubscriptionStore(subscriptionSelectors.isLoading)
  const error = useSubscriptionStore(subscriptionSelectors.error)
  const tier = useSubscriptionStore(subscriptionSelectors.tier)
  const status = useSubscriptionStore(subscriptionSelectors.status)
  const expiresAt = useSubscriptionStore(subscriptionSelectors.expiresAt)
  const capabilitiesVersion = useSubscriptionStore(subscriptionSelectors.capabilitiesVersion)
  const billingCycle = useSubscriptionStore(subscriptionSelectors.billingCycle)
  const currency = useSubscriptionStore(subscriptionSelectors.currency)
  const isActive = useSubscriptionStore(subscriptionSelectors.isActive)

  // Store actions (use stable selectors for performance)
  const createSubscriptionAction = useSubscriptionStore(subscriptionSelectors.createSubscription)
  const renewSubscriptionAction = useSubscriptionStore(subscriptionSelectors.renewSubscription)
  const upgradeSubscriptionAction = useSubscriptionStore(subscriptionSelectors.upgradeSubscription)
  const scheduleDowngradeAction = useSubscriptionStore(subscriptionSelectors.scheduleDowngrade)
  const cancelActiveSubscriptionAction = useSubscriptionStore(subscriptionSelectors.cancelActiveSubscription)
  const resumeSubscriptionAction = useSubscriptionStore(subscriptionSelectors.resumeSubscription)
  const voidPendingPaymentAction = useSubscriptionStore(subscriptionSelectors.voidPendingPayment)
  const reactivateSubscriptionAction = useSubscriptionStore(subscriptionSelectors.reactivateSubscription)
  const retrySubscriptionPaymentAction = useSubscriptionStore(subscriptionSelectors.retrySubscriptionPayment)
  const clearError = useSubscriptionStore(subscriptionSelectors.clearError)

  // ============================================================================
  // Stable Action Implementations (useCallback for performance)
  // ============================================================================

  const createSubscription = useCallback(async (request: CreateSubscriptionRequest): Promise<CreateSubscriptionResponse> => {
    return createSubscriptionAction(request)
  }, [createSubscriptionAction])

  const renewSubscription = useCallback(async (request: RenewSubscriptionRequest): Promise<RenewSubscriptionResponse> => {
    return renewSubscriptionAction(request)
  }, [renewSubscriptionAction])

  const upgradeSubscription = useCallback(async (request: UpgradeSubscriptionRequest): Promise<UpgradeSubscriptionResponse> => {
    return upgradeSubscriptionAction(request)
  }, [upgradeSubscriptionAction])

  const scheduleDowngrade = useCallback(async (request: ScheduleDowngradeRequest): Promise<ScheduleDowngradeResponse> => {
    return scheduleDowngradeAction(request)
  }, [scheduleDowngradeAction])

  const cancelActiveSubscription = useCallback(async (request?: CancelSubscriptionRequest): Promise<CancelSubscriptionResponse> => {
    return cancelActiveSubscriptionAction(request)
  }, [cancelActiveSubscriptionAction])

  const resumeSubscription = useCallback(async (): Promise<ResumeSubscriptionResponse> => {
    return resumeSubscriptionAction()
  }, [resumeSubscriptionAction])

  const voidPendingPayment = useCallback(async (subscriptionId: string): Promise<VoidPendingPaymentResponse> => {
    return voidPendingPaymentAction(subscriptionId)
  }, [voidPendingPaymentAction])

  const reactivateSubscription = useCallback(async (): Promise<ReactivateSubscriptionResponse> => {
    return reactivateSubscriptionAction()
  }, [reactivateSubscriptionAction])

  const retrySubscriptionPayment = useCallback(async (request: RetrySubscriptionPaymentRequest): Promise<RetrySubscriptionPaymentResponse> => {
    return retrySubscriptionPaymentAction(request)
  }, [retrySubscriptionPaymentAction])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    jwtSubscription,
    isLoading,
    error,

    // Computed state (from JWT - minimal claims only)
    tier,
    status,
    expiresAt,
    capabilitiesVersion,
    billingCycle,
    currency,
    isActive,

    // Actions (stable references)
    createSubscription,
    renewSubscription,
    upgradeSubscription,
    scheduleDowngrade,
    cancelActiveSubscription,
    resumeSubscription,
    voidPendingPayment,
    reactivateSubscription,
    retrySubscriptionPayment,
    clearError,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for subscription status only - minimal re-renders
 * Use when you only need to check subscription tier/status
 */
export function useSubscriptionStatus() {
  return {
    tier: useSubscriptionStore(subscriptionSelectors.tier),
    status: useSubscriptionStore(subscriptionSelectors.status),
    isActive: useSubscriptionStore(subscriptionSelectors.isActive),
    isLoading: useSubscriptionStore(subscriptionSelectors.isLoading),
  }
}

/**
 * Hook for subscription data only - minimal re-renders
 * Use when you need full subscription details
 */
export function useSubscriptionData() {
  return {
    jwtSubscription: useSubscriptionStore(subscriptionSelectors.jwtSubscription),
    tier: useSubscriptionStore(subscriptionSelectors.tier),
    status: useSubscriptionStore(subscriptionSelectors.status),
    expiresAt: useSubscriptionStore(subscriptionSelectors.expiresAt),
    capabilitiesVersion: useSubscriptionStore(subscriptionSelectors.capabilitiesVersion),
    billingCycle: useSubscriptionStore(subscriptionSelectors.billingCycle),
    currency: useSubscriptionStore(subscriptionSelectors.currency),
  }
}

/**
 * Hook for subscription actions only - no reactive state
 * Use when you only need to trigger subscription operations
 */
export function useSubscriptionActions() {
  const createSubscription = useSubscriptionStore(subscriptionSelectors.createSubscription)
  const renewSubscription = useSubscriptionStore(subscriptionSelectors.renewSubscription)
  const upgradeSubscription = useSubscriptionStore(subscriptionSelectors.upgradeSubscription)
  const scheduleDowngrade = useSubscriptionStore(subscriptionSelectors.scheduleDowngrade)
  const cancelActiveSubscription = useSubscriptionStore(subscriptionSelectors.cancelActiveSubscription)
  const resumeSubscription = useSubscriptionStore(subscriptionSelectors.resumeSubscription)
  const voidPendingPayment = useSubscriptionStore(subscriptionSelectors.voidPendingPayment)
  const reactivateSubscription = useSubscriptionStore(subscriptionSelectors.reactivateSubscription)
  const retrySubscriptionPayment = useSubscriptionStore(subscriptionSelectors.retrySubscriptionPayment)
  const clearError = useSubscriptionStore(subscriptionSelectors.clearError)

  const isLoading = useSubscriptionStore(subscriptionSelectors.isLoading)
  const error = useSubscriptionStore(subscriptionSelectors.error)

  return {
    // Actions
    createSubscription,
    renewSubscription,
    upgradeSubscription,
    scheduleDowngrade,
    cancelActiveSubscription,
    resumeSubscription,
    voidPendingPayment,
    reactivateSubscription,
    retrySubscriptionPayment,
    clearError,

    // Minimal state for action feedback
    isLoading,
    error,
  }
}

/**
 * Hook for error handling only - minimal re-renders
 * Use in error boundaries or error display components
 */
export function useSubscriptionError() {
  return {
    error: useSubscriptionStore(subscriptionSelectors.error),
    clearError: useSubscriptionStore(subscriptionSelectors.clearError),
  }
}

// ============================================================================
// Default Export
// ============================================================================

export default useSubscription
