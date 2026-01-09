/**
 * Payment Hook - 2024 Best Practices with Zustand
 * Custom hook layer for payment store - handles payment processing and status
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { usePaymentStore, paymentSelectors } from '../../stores/subscription/paymentStore'
import type {
  PaymentInitiationRequest,
  PaymentInitiationResponse,
  PaymentStatusResponse,
} from '../../types/subscription'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UsePaymentReturn {
  // State selectors (performance optimized)
  currentPayment: ReturnType<typeof paymentSelectors.currentPayment>
  paymentStatus: ReturnType<typeof paymentSelectors.paymentStatus>
  paymentMethods: ReturnType<typeof paymentSelectors.paymentMethods>
  isLoading: boolean
  error: string | null

  // Computed state
  hasPaymentInProgress: boolean
  paymentId: ReturnType<typeof paymentSelectors.paymentId>
  paymentReference: ReturnType<typeof paymentSelectors.paymentReference>
  paymentAmount: ReturnType<typeof paymentSelectors.paymentAmount>
  paymentLink: ReturnType<typeof paymentSelectors.paymentLink>

  // Actions (stable references)
  initiatePayment: (request: PaymentInitiationRequest) => Promise<PaymentInitiationResponse>
  checkPaymentStatus: (paymentId: string) => Promise<void>
  getPaymentMethods: () => Promise<void>
  pollPaymentStatus: (paymentId: string, maxAttempts?: number) => Promise<PaymentStatusResponse>
  clearError: () => void
  clearPayment: () => void

  // Helper methods
  isPaymentPending: () => boolean
  isPaymentComplete: () => boolean
  isPaymentFailed: () => boolean
}

// ============================================================================
// Main Payment Hook
// ============================================================================

export function usePayment(): UsePaymentReturn {
  // Selective store subscriptions (performance optimized)
  const currentPayment = usePaymentStore(paymentSelectors.currentPayment)
  const paymentStatus = usePaymentStore(paymentSelectors.paymentStatus)
  const paymentMethods = usePaymentStore(paymentSelectors.paymentMethods)
  const isLoading = usePaymentStore(paymentSelectors.isLoading)
  const error = usePaymentStore(paymentSelectors.error)
  const hasPaymentInProgress = usePaymentStore(paymentSelectors.hasPaymentInProgress)
  const paymentId = usePaymentStore(paymentSelectors.paymentId)
  const paymentReference = usePaymentStore(paymentSelectors.paymentReference)
  const paymentAmount = usePaymentStore(paymentSelectors.paymentAmount)
  const paymentLink = usePaymentStore(paymentSelectors.paymentLink)

  // Store actions (direct references for performance)
  const initiatePaymentAction = usePaymentStore(state => state.initiatePayment)
  const checkPaymentStatusAction = usePaymentStore(state => state.checkPaymentStatus)
  const getPaymentMethodsAction = usePaymentStore(state => state.getPaymentMethods)
  const pollPaymentStatusAction = usePaymentStore(state => state.pollPaymentStatus)
  const clearError = usePaymentStore(state => state.clearError)
  const clearPayment = usePaymentStore(state => state.clearPayment)
  const isPaymentPending = usePaymentStore(state => state.isPaymentPending)
  const isPaymentComplete = usePaymentStore(state => state.isPaymentComplete)
  const isPaymentFailed = usePaymentStore(state => state.isPaymentFailed)

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const initiatePayment = useCallback(async (request: PaymentInitiationRequest): Promise<PaymentInitiationResponse> => {
    return initiatePaymentAction(request)
  }, [initiatePaymentAction])

  const checkPaymentStatus = useCallback(async (paymentId: string): Promise<void> => {
    return checkPaymentStatusAction(paymentId)
  }, [checkPaymentStatusAction])

  const getPaymentMethods = useCallback(async (): Promise<void> => {
    return getPaymentMethodsAction()
  }, [getPaymentMethodsAction])

  const pollPaymentStatus = useCallback(async (paymentId: string, maxAttempts?: number): Promise<PaymentStatusResponse> => {
    return pollPaymentStatusAction(paymentId, maxAttempts)
  }, [pollPaymentStatusAction])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    currentPayment,
    paymentStatus,
    paymentMethods,
    isLoading,
    error,

    // Computed state
    hasPaymentInProgress,
    paymentId,
    paymentReference,
    paymentAmount,
    paymentLink,

    // Actions (stable)
    initiatePayment,
    checkPaymentStatus,
    getPaymentMethods,
    pollPaymentStatus,
    clearError,
    clearPayment,

    // Helper methods
    isPaymentPending,
    isPaymentComplete,
    isPaymentFailed,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for payment status only - minimal re-renders
 */
export function usePaymentStatus() {
  return {
    paymentStatus: usePaymentStore(paymentSelectors.paymentStatus),
    hasPaymentInProgress: usePaymentStore(paymentSelectors.hasPaymentInProgress),
    isLoading: usePaymentStore(paymentSelectors.isLoading),
  }
}

/**
 * Hook for current payment details only - minimal re-renders
 */
export function usePaymentDetails() {
  return {
    currentPayment: usePaymentStore(paymentSelectors.currentPayment),
    paymentId: usePaymentStore(paymentSelectors.paymentId),
    paymentReference: usePaymentStore(paymentSelectors.paymentReference),
    paymentAmount: usePaymentStore(paymentSelectors.paymentAmount),
    paymentLink: usePaymentStore(paymentSelectors.paymentLink),
  }
}

/**
 * Hook for payment actions only - no reactive state
 */
export function usePaymentActions() {
  const clearError = usePaymentStore(state => state.clearError)
  const clearPayment = usePaymentStore(state => state.clearPayment)

  return { clearError, clearPayment }
}

// ============================================================================
// Default Export
// ============================================================================

export default usePayment