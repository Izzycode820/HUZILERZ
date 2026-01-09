/**
 * Payment Hook - 2024 Best Practices with Zustand
 * Custom hook layer for payment store - provides clean interface and performance
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 * Aligned with backend payments/views.py and webhook-driven payment flow
 */

import { useCallback, useEffect } from 'react'
import { usePaymentStore, paymentSelectors } from '../../stores/payment/paymentStore'
import type {
  PaymentStatusResponse,
  PaymentProvider,
  SelectedPaymentMethod
} from '../../types/payment/payment'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UsePaymentReturn {
  // State selectors (performance optimized)
  isPolling: boolean
  currentPaymentId: string | null
  paymentStatus: PaymentStatusResponse | null
  isLoading: boolean
  error: string | null

  // Computed state (derived from payment status)
  paymentStatusValue: ReturnType<typeof paymentSelectors.paymentStatusValue>
  isPaymentPending: boolean
  isPaymentSuccess: boolean
  isPaymentFailed: boolean
  isPaymentExpired: boolean

  // Actions (stable references)
  checkPaymentStatus: (paymentIntentId: string) => Promise<PaymentStatusResponse>
  startPolling: (
    paymentIntentId: string,
    onSuccess?: (payment: PaymentStatusResponse) => void,
    onError?: (error: string) => void
  ) => void
  stopPolling: () => void
  clearError: () => void
  clearPaymentStatus: () => void
}

// ============================================================================
// Main Payment Hook
// ============================================================================

export function usePayment(): UsePaymentReturn {
  // Selective store subscriptions (performance optimized)
  const isPolling = usePaymentStore(paymentSelectors.isPolling)
  const currentPaymentId = usePaymentStore(paymentSelectors.currentPaymentId)
  const paymentStatus = usePaymentStore(paymentSelectors.paymentStatus)
  const isLoading = usePaymentStore(paymentSelectors.isLoading)
  const error = usePaymentStore(paymentSelectors.error)
  const paymentStatusValue = usePaymentStore(paymentSelectors.paymentStatusValue)
  const isPaymentPending = usePaymentStore(paymentSelectors.isPaymentPending)
  const isPaymentSuccess = usePaymentStore(paymentSelectors.isPaymentSuccess)
  const isPaymentFailed = usePaymentStore(paymentSelectors.isPaymentFailed)
  const isPaymentExpired = usePaymentStore(paymentSelectors.isPaymentExpired)

  // Store actions (use stable selectors for performance)
  const checkPaymentStatusAction = usePaymentStore(paymentSelectors.checkPaymentStatus)
  const startPollingAction = usePaymentStore(paymentSelectors.startPolling)
  const stopPollingAction = usePaymentStore(paymentSelectors.stopPolling)
  const clearErrorAction = usePaymentStore(paymentSelectors.clearError)
  const clearPaymentStatusAction = usePaymentStore(paymentSelectors.clearPaymentStatus)

  // ============================================================================
  // Stable Action Implementations (useCallback for performance)
  // ============================================================================

  const checkPaymentStatus = useCallback(
    async (paymentIntentId: string): Promise<PaymentStatusResponse> => {
      return checkPaymentStatusAction(paymentIntentId)
    },
    [checkPaymentStatusAction]
  )

  const startPolling = useCallback(
    (
      paymentIntentId: string,
      onSuccess?: (payment: PaymentStatusResponse) => void,
      onError?: (error: string) => void
    ) => {
      startPollingAction(paymentIntentId, onSuccess, onError)
    },
    [startPollingAction]
  )

  const stopPolling = useCallback(() => {
    stopPollingAction()
  }, [stopPollingAction])

  const clearError = useCallback(() => {
    clearErrorAction()
  }, [clearErrorAction])

  const clearPaymentStatus = useCallback(() => {
    clearPaymentStatusAction()
  }, [clearPaymentStatusAction])

  // ============================================================================
  // Cleanup Effect - Stop polling on unmount
  // ============================================================================

  useEffect(() => {
    return () => {
      if (isPolling) {
        stopPollingAction()
      }
    }
  }, [isPolling, stopPollingAction])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    isPolling,
    currentPaymentId,
    paymentStatus,
    isLoading,
    error,

    // Computed state
    paymentStatusValue,
    isPaymentPending,
    isPaymentSuccess,
    isPaymentFailed,
    isPaymentExpired,

    // Actions (stable references)
    checkPaymentStatus,
    startPolling,
    stopPolling,
    clearError,
    clearPaymentStatus,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for payment status only - minimal re-renders
 * Use when you only need to check payment status value
 */
export function usePaymentStatus() {
  return {
    paymentStatus: usePaymentStore(paymentSelectors.paymentStatus),
    paymentStatusValue: usePaymentStore(paymentSelectors.paymentStatusValue),
    isPaymentPending: usePaymentStore(paymentSelectors.isPaymentPending),
    isPaymentSuccess: usePaymentStore(paymentSelectors.isPaymentSuccess),
    isPaymentFailed: usePaymentStore(paymentSelectors.isPaymentFailed),
    isPaymentExpired: usePaymentStore(paymentSelectors.isPaymentExpired),
  }
}

/**
 * Hook for payment polling control only - no reactive state
 * Use when you only need to control polling operations
 */
export function usePaymentPolling() {
  const startPolling = usePaymentStore(paymentSelectors.startPolling)
  const stopPolling = usePaymentStore(paymentSelectors.stopPolling)
  const isPolling = usePaymentStore(paymentSelectors.isPolling)
  const currentPaymentId = usePaymentStore(paymentSelectors.currentPaymentId)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isPolling) {
        stopPolling()
      }
    }
  }, [isPolling, stopPolling])

  return {
    startPolling,
    stopPolling,
    isPolling,
    currentPaymentId,
  }
}

/**
 * Hook for payment actions only - no reactive polling state
 * Use when you only need to trigger payment operations
 */
export function usePaymentActions() {
  const checkPaymentStatus = usePaymentStore(paymentSelectors.checkPaymentStatus)
  const startPolling = usePaymentStore(paymentSelectors.startPolling)
  const stopPolling = usePaymentStore(paymentSelectors.stopPolling)
  const clearError = usePaymentStore(paymentSelectors.clearError)
  const clearPaymentStatus = usePaymentStore(paymentSelectors.clearPaymentStatus)

  const isLoading = usePaymentStore(paymentSelectors.isLoading)
  const error = usePaymentStore(paymentSelectors.error)

  return {
    // Actions
    checkPaymentStatus,
    startPolling,
    stopPolling,
    clearError,
    clearPaymentStatus,

    // Minimal state for action feedback
    isLoading,
    error,
  }
}

/**
 * Hook for error handling only - minimal re-renders
 * Use in error boundaries or error display components
 */
export function usePaymentError() {
  return {
    error: usePaymentStore(paymentSelectors.error),
    clearError: usePaymentStore(paymentSelectors.clearError),
  }
}

// ============================================================================
// Platform Payment Methods Hooks
// ============================================================================

export interface UsePlatformPaymentMethodsReturn {
  // State
  platformMethods: PaymentProvider[]
  selectedPaymentMethod: SelectedPaymentMethod | null
  isLoadingMethods: boolean
  methodsError: string | null

  // Computed state
  hasPaymentMethods: boolean
  recommendedMethod: PaymentProvider | null
  selectedProvider: string | null

  // Actions (stable references)
  fetchPlatformMethods: (purpose?: string) => Promise<void>
  selectPaymentMethod: (method: SelectedPaymentMethod) => void
  clearSelectedMethod: () => void
}

/**
 * Hook for platform payment methods - comprehensive interface
 * Use in checkout pages and payment modals
 * Auto-fetches methods on mount if not already loaded
 */
export function usePlatformPaymentMethods(autoFetch: boolean = true, purpose: string = 'subscription'): UsePlatformPaymentMethodsReturn {
  // Selective store subscriptions (performance optimized)
  const platformMethods = usePaymentStore(paymentSelectors.platformMethods)
  const selectedPaymentMethod = usePaymentStore(paymentSelectors.selectedPaymentMethod)
  const isLoadingMethods = usePaymentStore(paymentSelectors.isLoadingMethods)
  const methodsError = usePaymentStore(paymentSelectors.methodsError)
  const hasPaymentMethods = usePaymentStore(paymentSelectors.hasPaymentMethods)
  const recommendedMethod = usePaymentStore(paymentSelectors.recommendedMethod)
  const selectedProvider = usePaymentStore(paymentSelectors.selectedProvider)

  // Store actions
  const fetchPlatformMethodsAction = usePaymentStore(paymentSelectors.fetchPlatformMethods)
  const selectPaymentMethodAction = usePaymentStore(paymentSelectors.selectPaymentMethod)
  const clearSelectedMethodAction = usePaymentStore(paymentSelectors.clearSelectedMethod)

  // Stable action implementations
  const fetchPlatformMethods = useCallback(
    async (fetchPurpose?: string): Promise<void> => {
      return fetchPlatformMethodsAction(fetchPurpose || purpose)
    },
    [fetchPlatformMethodsAction, purpose]
  )

  const selectPaymentMethod = useCallback(
    (method: SelectedPaymentMethod) => {
      selectPaymentMethodAction(method)
    },
    [selectPaymentMethodAction]
  )

  const clearSelectedMethod = useCallback(() => {
    clearSelectedMethodAction()
  }, [clearSelectedMethodAction])

  // Auto-fetch on mount if enabled and not already loaded
  useEffect(() => {
    if (autoFetch && !hasPaymentMethods && !isLoadingMethods) {
      fetchPlatformMethods(purpose)
    }
  }, [autoFetch, hasPaymentMethods, isLoadingMethods, fetchPlatformMethods, purpose])

  return {
    // State
    platformMethods,
    selectedPaymentMethod,
    isLoadingMethods,
    methodsError,

    // Computed state
    hasPaymentMethods,
    recommendedMethod,
    selectedProvider,

    // Actions
    fetchPlatformMethods,
    selectPaymentMethod,
    clearSelectedMethod,
  }
}

/**
 * Hook for payment method selection only - minimal re-renders
 * Use in payment method selector components
 */
export function usePaymentMethodSelection() {
  const selectedPaymentMethod = usePaymentStore(paymentSelectors.selectedPaymentMethod)
  const selectPaymentMethod = usePaymentStore(paymentSelectors.selectPaymentMethod)
  const clearSelectedMethod = usePaymentStore(paymentSelectors.clearSelectedMethod)
  const selectedProvider = usePaymentStore(paymentSelectors.selectedProvider)

  return {
    selectedPaymentMethod,
    selectPaymentMethod,
    clearSelectedMethod,
    selectedProvider,
  }
}

/**
 * Hook for payment methods list only - no selection state
 * Use in payment method display/listing components
 */
export function usePaymentMethodsList() {
  const platformMethods = usePaymentStore(paymentSelectors.platformMethods)
  const isLoadingMethods = usePaymentStore(paymentSelectors.isLoadingMethods)
  const methodsError = usePaymentStore(paymentSelectors.methodsError)
  const hasPaymentMethods = usePaymentStore(paymentSelectors.hasPaymentMethods)
  const recommendedMethod = usePaymentStore(paymentSelectors.recommendedMethod)

  return {
    platformMethods,
    isLoadingMethods,
    methodsError,
    hasPaymentMethods,
    recommendedMethod,
  }
}

/**
 * Hook for fetching payment methods only - no reactive state
 * Use when you only need to trigger fetch operations
 */
export function useFetchPaymentMethods() {
  const fetchPlatformMethods = usePaymentStore(paymentSelectors.fetchPlatformMethods)
  const isLoadingMethods = usePaymentStore(paymentSelectors.isLoadingMethods)
  const methodsError = usePaymentStore(paymentSelectors.methodsError)

  return {
    fetchPlatformMethods,
    isLoadingMethods,
    methodsError,
  }
}

// ============================================================================
// Default Export
// ============================================================================

export default usePayment
