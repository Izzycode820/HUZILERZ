/**
 * Payment Store - Zustand 2024 Best Practices
 * Manages payment status polling for webhook-driven payments
 * Aligned with backend payments/views.py
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  PaymentStatusResponse,
  PaymentProvider,
  SelectedPaymentMethod
} from '../../types/payment/payment'
import paymentService from '../../services/payment/payment'

// ============================================================================
// Payment Store State Interface
// ============================================================================

interface PaymentStoreState {
  // Polling State
  isPolling: boolean
  currentPaymentId: string | null
  pollingIntervalId: NodeJS.Timeout | null
  paymentStatus: PaymentStatusResponse | null

  // Platform Payment Methods State
  platformMethods: PaymentProvider[]
  selectedPaymentMethod: SelectedPaymentMethod | null
  isLoadingMethods: boolean
  methodsError: string | null

  // UI State
  isLoading: boolean
  error: string | null

  // Actions - Payment Status Polling
  checkPaymentStatus: (paymentIntentId: string) => Promise<PaymentStatusResponse>
  startPolling: (paymentIntentId: string, onSuccess?: (payment: PaymentStatusResponse) => void, onError?: (error: string) => void) => void
  stopPolling: () => void

  // Actions - Platform Payment Methods
  fetchPlatformMethods: (purpose?: string) => Promise<void>
  selectPaymentMethod: (method: SelectedPaymentMethod) => void
  clearSelectedMethod: () => void

  // UI Actions
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearPaymentStatus: () => void
}

// ============================================================================
// Polling Configuration
// ============================================================================

const POLLING_INTERVALS = [1000, 2000, 3000, 5000] // First 4 attempts with escalating intervals
const DEFAULT_POLLING_INTERVAL = 5000 // 5 seconds after initial attempts
const MAX_POLLING_DURATION = 30 * 60 * 1000 // 30 minutes (matches backend payment expiration)

// ============================================================================
// Create Payment Store
// ============================================================================

export const usePaymentStore = create<PaymentStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      isPolling: false,
      currentPaymentId: null,
      pollingIntervalId: null,
      paymentStatus: null,

      // Platform Payment Methods State
      platformMethods: [],
      selectedPaymentMethod: null,
      isLoadingMethods: false,
      methodsError: null,

      isLoading: false,
      error: null,

      // ========================================================================
      // Payment Actions
      // ========================================================================

      checkPaymentStatus: async (paymentIntentId) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await paymentService.checkPaymentStatus(paymentIntentId)

          set((state) => {
            state.paymentStatus = response
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const errorMessage = error?.response?.data?.error || error.message || 'Failed to check payment status'

          set((state) => {
            state.error = errorMessage
            state.isLoading = false
          })
          throw error
        }
      },

      startPolling: (paymentIntentId, onSuccess, onError) => {
        const state = get()

        // Stop any existing polling
        if (state.pollingIntervalId) {
          clearInterval(state.pollingIntervalId)
        }

        set((state) => {
          state.isPolling = true
          state.currentPaymentId = paymentIntentId
          state.error = null
        })

        let attemptCount = 0
        const startTime = Date.now()

        const poll = async () => {
          const currentState = get()

          // Check if polling was stopped
          if (!currentState.isPolling) {
            return
          }

          // Check timeout (30 minutes)
          if (Date.now() - startTime > MAX_POLLING_DURATION) {
            get().stopPolling()
            const timeoutError = 'Payment polling timeout (30 minutes)'
            set((state) => {
              state.error = timeoutError
            })
            onError?.(timeoutError)
            return
          }

          try {
            const response = await paymentService.checkPaymentStatus(paymentIntentId)

            set((state) => {
              state.paymentStatus = response
            })

            // Check for final states
            if (response.status === 'success') {
              get().stopPolling()
              onSuccess?.(response)
              return
            }

            if (response.status === 'failed' || response.status === 'cancelled') {
              get().stopPolling()
              const failureMessage = response.failure_reason || 'Payment failed'
              set((state) => {
                state.error = failureMessage
              })
              onError?.(failureMessage)
              return
            }

            if (response.is_expired) {
              get().stopPolling()
              const expiredError = 'Payment expired'
              set((state) => {
                state.error = expiredError
              })
              onError?.(expiredError)
              return
            }

            // Continue polling for pending/created states
            attemptCount++
          } catch (error: any) {
            const errorMessage = error?.response?.data?.error || error.message || 'Failed to check payment status'

            // Don't stop polling on network errors, just log
            console.error('Polling error:', errorMessage)

            // Only stop and notify on critical errors (404, 403, etc.)
            if (error?.response?.status === 404 || error?.response?.status === 403) {
              get().stopPolling()
              set((state) => {
                state.error = errorMessage
              })
              onError?.(errorMessage)
            }
          }
        }

        // Start polling immediately
        poll()

        // Set up interval with progressive delays
        const getInterval = (attempt: number): number => {
          return POLLING_INTERVALS[attempt] || DEFAULT_POLLING_INTERVAL
        }

        let currentInterval = getInterval(0)
        let intervalId = setInterval(() => {
          poll()
          attemptCount++
          const newInterval = getInterval(attemptCount)
          if (newInterval !== currentInterval) {
            currentInterval = newInterval
            clearInterval(intervalId)
            intervalId = setInterval(poll, currentInterval)
            set((state) => {
              state.pollingIntervalId = intervalId
            })
          }
        }, currentInterval)

        set((state) => {
          state.pollingIntervalId = intervalId
        })
      },

      stopPolling: () => {
        const state = get()

        if (state.pollingIntervalId) {
          clearInterval(state.pollingIntervalId)
        }

        set((state) => {
          state.isPolling = false
          state.pollingIntervalId = null
          state.currentPaymentId = null
        })
      },

      // ========================================================================
      // Platform Payment Methods Actions
      // ========================================================================

      fetchPlatformMethods: async (purpose = 'subscription') => {
        set((state) => {
          state.isLoadingMethods = true
          state.methodsError = null
        })

        try {
          const response = await paymentService.getPlatformPaymentMethods(purpose)

          set((state) => {
            state.platformMethods = response.methods
            state.isLoadingMethods = false

            // Auto-select recommended method if none selected
            if (!state.selectedPaymentMethod && response.methods.length > 0) {
              const recommended = response.methods.find(m => m.recommended) || response.methods[0]
              state.selectedPaymentMethod = {
                provider: recommended.provider,
                displayName: recommended.display_name,
                mode: recommended.modes[0] || 'ussd'
              }
            }
          })
        } catch (error: any) {
          const errorMessage = error?.response?.data?.error || error.message || 'Failed to fetch payment methods'

          set((state) => {
            state.methodsError = errorMessage
            state.isLoadingMethods = false
          })

          throw error
        }
      },

      selectPaymentMethod: (method) => {
        set((state) => {
          state.selectedPaymentMethod = method
        })
      },

      clearSelectedMethod: () => {
        set((state) => {
          state.selectedPaymentMethod = null
        })
      },

      // ========================================================================
      // UI State Actions
      // ========================================================================

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading
        })
      },

      setError: (error) => {
        set((state) => {
          state.error = error
          if (error) {
            state.isLoading = false
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      clearPaymentStatus: () => {
        set((state) => {
          state.paymentStatus = null
          state.error = null
        })
      },
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const paymentSelectors = {
  // Core selectors - Polling
  isPolling: (state: PaymentStoreState) => state.isPolling,
  currentPaymentId: (state: PaymentStoreState) => state.currentPaymentId,
  paymentStatus: (state: PaymentStoreState) => state.paymentStatus,
  isLoading: (state: PaymentStoreState) => state.isLoading,
  error: (state: PaymentStoreState) => state.error,

  // Core selectors - Payment Methods
  platformMethods: (state: PaymentStoreState) => state.platformMethods,
  selectedPaymentMethod: (state: PaymentStoreState) => state.selectedPaymentMethod,
  isLoadingMethods: (state: PaymentStoreState) => state.isLoadingMethods,
  methodsError: (state: PaymentStoreState) => state.methodsError,

  // Computed selectors - Polling
  paymentStatusValue: (state: PaymentStoreState) => state.paymentStatus?.status,
  isPaymentPending: (state: PaymentStoreState) =>
    state.paymentStatus?.status === 'pending' || state.paymentStatus?.status === 'created',
  isPaymentSuccess: (state: PaymentStoreState) => state.paymentStatus?.status === 'success',
  isPaymentFailed: (state: PaymentStoreState) =>
    state.paymentStatus?.status === 'failed' || state.paymentStatus?.status === 'cancelled',
  isPaymentExpired: (state: PaymentStoreState) => state.paymentStatus?.is_expired || false,

  // Computed selectors - Payment Methods
  hasPaymentMethods: (state: PaymentStoreState) => state.platformMethods.length > 0,
  recommendedMethod: (state: PaymentStoreState) => state.platformMethods.find(m => m.recommended) || null,
  selectedProvider: (state: PaymentStoreState) => state.selectedPaymentMethod?.provider || null,

  // Action selectors (stable references) - Polling
  checkPaymentStatus: (state: PaymentStoreState) => state.checkPaymentStatus,
  startPolling: (state: PaymentStoreState) => state.startPolling,
  stopPolling: (state: PaymentStoreState) => state.stopPolling,
  clearError: (state: PaymentStoreState) => state.clearError,
  clearPaymentStatus: (state: PaymentStoreState) => state.clearPaymentStatus,

  // Action selectors (stable references) - Payment Methods
  fetchPlatformMethods: (state: PaymentStoreState) => state.fetchPlatformMethods,
  selectPaymentMethod: (state: PaymentStoreState) => state.selectPaymentMethod,
  clearSelectedMethod: (state: PaymentStoreState) => state.clearSelectedMethod,
}

// ============================================================================
// Export
// ============================================================================

export default usePaymentStore
