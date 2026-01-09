/**
 * Subscription Store - Zustand 2024 Best Practices
 * Manages subscription state, status, and operations
 * Aligned with backend subscription_views.py
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
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
import subscriptionService from '../../services/subscription/subscription'

// ============================================================================
// Subscription Store State Interface
// ============================================================================

interface SubscriptionStoreState {
  // UI State
  isLoading: boolean
  error: SubscriptionError | null

  // Actions - Subscription Management
  createSubscription: (request: CreateSubscriptionRequest) => Promise<CreateSubscriptionResponse>
  renewSubscription: (request: RenewSubscriptionRequest) => Promise<RenewSubscriptionResponse>
  upgradeSubscription: (request: UpgradeSubscriptionRequest) => Promise<UpgradeSubscriptionResponse>
  scheduleDowngrade: (request: ScheduleDowngradeRequest) => Promise<ScheduleDowngradeResponse>
  cancelActiveSubscription: (request?: CancelSubscriptionRequest) => Promise<CancelSubscriptionResponse>
  resumeSubscription: () => Promise<ResumeSubscriptionResponse>
  voidPendingPayment: (subscriptionId: string) => Promise<VoidPendingPaymentResponse>
  reactivateSubscription: () => Promise<ReactivateSubscriptionResponse>
  retrySubscriptionPayment: (request: RetrySubscriptionPaymentRequest) => Promise<RetrySubscriptionPaymentResponse>

  // UI Actions
  setLoading: (loading: boolean) => void
  setError: (error: SubscriptionError | null) => void
  clearError: () => void

  // Sync Actions (Industry standard: Auth0, Firebase, Stripe pattern)
  syncFromAuth: (jwtSubscription: SubscriptionData | null) => void

  // JWT Subscription Data (synced from auth)
  jwtSubscription: SubscriptionData | null
}

// ============================================================================
// Create Subscription Store
// ============================================================================

export const useSubscriptionStore = create<SubscriptionStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      isLoading: false,
      error: null,
      jwtSubscription: null,

      // ========================================================================
      // Subscription Actions
      // ========================================================================

      createSubscription: async (request) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.createSubscription(request)

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to create subscription',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      renewSubscription: async (request) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.renewSubscription(request)

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to renew subscription',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      upgradeSubscription: async (request) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.upgradeSubscription(request)

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to upgrade subscription',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      scheduleDowngrade: async (request) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.scheduleDowngrade(request)

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to schedule downgrade',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      cancelActiveSubscription: async (request) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.cancelActiveSubscription(request)

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to cancel subscription',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      resumeSubscription: async () => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.resumeSubscription()

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to resume subscription',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      voidPendingPayment: async (subscriptionId) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.voidPendingPayment(subscriptionId)

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to void pending payment',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      reactivateSubscription: async () => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.reactivateSubscription()

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to reactivate subscription',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
      },

      retrySubscriptionPayment: async (request) => {
        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await subscriptionService.retrySubscriptionPayment(request)

          set((state) => {
            state.isLoading = false
          })

          return response
        } catch (error: any) {
          const subscriptionError: SubscriptionError = {
            error: error?.response?.data?.error || error.message || 'Failed to retry payment',
            error_code: error?.response?.data?.error_code,
            ...error?.response?.data
          }

          set((state) => {
            state.error = subscriptionError
            state.isLoading = false
          })
          throw error
        }
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

      // ========================================================================
      // Sync Actions - Industry Standard Pattern (Auth0, Firebase, Stripe)
      // ========================================================================

      syncFromAuth: (jwtSubscription) => {
        set((state) => {
          state.jwtSubscription = jwtSubscription
        })
      },
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const subscriptionSelectors = {
  // Core selectors
  isLoading: (state: SubscriptionStoreState) => state.isLoading,
  error: (state: SubscriptionStoreState) => state.error,
  jwtSubscription: (state: SubscriptionStoreState) => state.jwtSubscription,

  // Computed selectors from JWT (minimal claims only)
  tier: (state: SubscriptionStoreState) => state.jwtSubscription?.tier,
  status: (state: SubscriptionStoreState) => state.jwtSubscription?.status,
  expiresAt: (state: SubscriptionStoreState) => state.jwtSubscription?.expires_at,
  capabilitiesVersion: (state: SubscriptionStoreState) => state.jwtSubscription?.capabilities_version,
  billingCycle: (state: SubscriptionStoreState) => state.jwtSubscription?.billing_cycle,
  currency: (state: SubscriptionStoreState) => state.jwtSubscription?.currency,
  isActive: (state: SubscriptionStoreState) => state.jwtSubscription?.status === 'active',

  // Action selectors (stable references)
  createSubscription: (state: SubscriptionStoreState) => state.createSubscription,
  renewSubscription: (state: SubscriptionStoreState) => state.renewSubscription,
  upgradeSubscription: (state: SubscriptionStoreState) => state.upgradeSubscription,
  scheduleDowngrade: (state: SubscriptionStoreState) => state.scheduleDowngrade,
  cancelActiveSubscription: (state: SubscriptionStoreState) => state.cancelActiveSubscription,
  resumeSubscription: (state: SubscriptionStoreState) => state.resumeSubscription,
  voidPendingPayment: (state: SubscriptionStoreState) => state.voidPendingPayment,
  reactivateSubscription: (state: SubscriptionStoreState) => state.reactivateSubscription,
  retrySubscriptionPayment: (state: SubscriptionStoreState) => state.retrySubscriptionPayment,
  clearError: (state: SubscriptionStoreState) => state.clearError,
  syncFromAuth: (state: SubscriptionStoreState) => state.syncFromAuth,
}

// ============================================================================
// Export
// ============================================================================

export default useSubscriptionStore
