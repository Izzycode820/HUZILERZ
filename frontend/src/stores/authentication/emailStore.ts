/**
 * Email Store - Zustand 2024 Best Practices
 * Manages email verification, password reset, and email change flows
 * Refactored to match authStore pattern with success handlers
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  EmailVerificationResponse,
  PasswordResetResponse,
  EmailChangeResponse,
  EmailVerificationStatus
} from '../../types/authentication/email'

// ============================================================================
// Email Store State Interface
// ============================================================================

interface EmailStoreState {
  // Email Verification Flow
  verificationStatus: EmailVerificationStatus | null
  verificationInProgress: boolean
  verificationError: string | null

  // Password Reset Flow
  passwordResetInProgress: boolean
  passwordResetSuccess: boolean
  passwordResetError: string | null

  // Email Change Flow
  emailChangeInProgress: boolean
  pendingEmailChange: string | null
  emailChangeSuccess: boolean
  emailChangeError: string | null

  // UI State
  isLoading: boolean
  error: string | null

  // Success Handlers (matching authStore pattern)
  setVerificationRequestSuccess: (response: EmailVerificationResponse) => void
  setVerificationConfirmSuccess: (response: EmailVerificationResponse) => void
  setPasswordResetRequestSuccess: (response: PasswordResetResponse) => void
  setPasswordResetConfirmSuccess: (response: PasswordResetResponse) => void
  setEmailChangeRequestSuccess: (response: EmailChangeResponse, newEmail: string) => void
  setEmailChangeConfirmSuccess: (response: EmailChangeResponse) => void
  setVerificationStatus: (status: EmailVerificationStatus | null) => void

  // UI State Actions
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void

  // Flow Control
  setVerificationInProgress: (inProgress: boolean) => void
  setPasswordResetInProgress: (inProgress: boolean) => void
  setEmailChangeInProgress: (inProgress: boolean) => void
  resetVerificationFlow: () => void
  resetPasswordResetFlow: () => void
  resetEmailChangeFlow: () => void

  // Helper Methods
  isEmailVerified: () => boolean
}

// ============================================================================
// Create Email Store
// ============================================================================

export const useEmailStore = create<EmailStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      verificationStatus: null,
      verificationInProgress: false,
      verificationError: null,
      passwordResetInProgress: false,
      passwordResetSuccess: false,
      passwordResetError: null,
      emailChangeInProgress: false,
      pendingEmailChange: null,
      emailChangeSuccess: false,
      emailChangeError: null,
      isLoading: false,
      error: null,

      // ========================================================================
      // Success Handlers (matching authStore pattern)
      // ========================================================================

      setVerificationRequestSuccess: (response) => {
        set((state) => {
          state.verificationInProgress = true
          state.verificationError = null
          state.error = null
        })
      },

      setVerificationConfirmSuccess: (response) => {
        set((state) => {
          state.verificationInProgress = false
          state.verificationError = null
          state.error = null
          // Update verification status if we have it
          if (state.verificationStatus) {
            state.verificationStatus.is_email_verified = true
          }
        })
      },

      setPasswordResetRequestSuccess: (response) => {
        set((state) => {
          state.passwordResetInProgress = true
          state.passwordResetError = null
          state.passwordResetSuccess = false
          state.error = null
        })
      },

      setPasswordResetConfirmSuccess: (response) => {
        set((state) => {
          state.passwordResetInProgress = false
          state.passwordResetSuccess = true
          state.passwordResetError = null
          state.error = null
        })
      },

      setEmailChangeRequestSuccess: (response, newEmail) => {
        set((state) => {
          state.emailChangeInProgress = true
          state.pendingEmailChange = newEmail
          state.emailChangeError = null
          state.emailChangeSuccess = false
          state.error = null
        })
      },

      setEmailChangeConfirmSuccess: (response) => {
        set((state) => {
          state.emailChangeInProgress = false
          state.emailChangeSuccess = true
          state.pendingEmailChange = null
          state.emailChangeError = null
          state.error = null
        })
      },

      setVerificationStatus: (status) => {
        set((state) => {
          state.verificationStatus = status
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
            state.verificationInProgress = false
            state.passwordResetInProgress = false
            state.emailChangeInProgress = false
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
          state.verificationError = null
          state.passwordResetError = null
          state.emailChangeError = null
        })
      },

      // ========================================================================
      // Flow Control Actions
      // ========================================================================

      setVerificationInProgress: (inProgress) => {
        set((state) => {
          state.verificationInProgress = inProgress
          if (inProgress) {
            state.verificationError = null
          }
        })
      },

      setPasswordResetInProgress: (inProgress) => {
        set((state) => {
          state.passwordResetInProgress = inProgress
          if (inProgress) {
            state.passwordResetError = null
            state.passwordResetSuccess = false
          }
        })
      },

      setEmailChangeInProgress: (inProgress) => {
        set((state) => {
          state.emailChangeInProgress = inProgress
          if (inProgress) {
            state.emailChangeError = null
            state.emailChangeSuccess = false
          }
        })
      },

      resetVerificationFlow: () => {
        set((state) => {
          state.verificationInProgress = false
          state.verificationError = null
        })
      },

      resetPasswordResetFlow: () => {
        set((state) => {
          state.passwordResetInProgress = false
          state.passwordResetError = null
          state.passwordResetSuccess = false
        })
      },

      resetEmailChangeFlow: () => {
        set((state) => {
          state.emailChangeInProgress = false
          state.pendingEmailChange = null
          state.emailChangeError = null
          state.emailChangeSuccess = false
        })
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      isEmailVerified: () => {
        const { verificationStatus } = get()
        return verificationStatus?.is_email_verified === true
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const emailSelectors = {
  // Core selectors
  verificationStatus: (state: EmailStoreState) => state.verificationStatus,
  verificationInProgress: (state: EmailStoreState) => state.verificationInProgress,
  verificationError: (state: EmailStoreState) => state.verificationError,
  passwordResetInProgress: (state: EmailStoreState) => state.passwordResetInProgress,
  passwordResetSuccess: (state: EmailStoreState) => state.passwordResetSuccess,
  passwordResetError: (state: EmailStoreState) => state.passwordResetError,
  emailChangeInProgress: (state: EmailStoreState) => state.emailChangeInProgress,
  emailChangeSuccess: (state: EmailStoreState) => state.emailChangeSuccess,
  emailChangeError: (state: EmailStoreState) => state.emailChangeError,
  pendingEmailChange: (state: EmailStoreState) => state.pendingEmailChange,
  isLoading: (state: EmailStoreState) => state.isLoading,
  error: (state: EmailStoreState) => state.error,

  // Computed selectors
  isEmailVerified: (state: EmailStoreState) => state.verificationStatus?.is_email_verified === true,
  hasAnyError: (state: EmailStoreState) =>
    !!(state.error || state.verificationError || state.passwordResetError || state.emailChangeError),
  hasAnyInProgress: (state: EmailStoreState) =>
    state.verificationInProgress || state.passwordResetInProgress || state.emailChangeInProgress || state.isLoading,

  // Status selectors
  verificationStatusText: (state: EmailStoreState) => {
    if (!state.verificationStatus) return 'Unknown'
    if (state.verificationStatus.is_email_verified) return 'Verified'
    return 'Not Verified'
  }
}

// ============================================================================
// Default Export
// ============================================================================

export default useEmailStore