/**
 * Email Hook - 2024 Best Practices with Zustand
 * Custom hook layer for email store - handles verification and email management
 * Refactored to match useAuth pattern with success handlers
 */

import { useCallback } from 'react'
import { useEmailStore, emailSelectors } from '../../stores/authentication/emailStore'
import emailService from '../../services/authentication/email'
import type {
  EmailVerificationRequest,
  EmailVerificationResponse,
  EmailVerificationConfirmRequest,
  PasswordResetRequest,
  PasswordResetResponse,
  PasswordResetConfirmRequest,
  EmailChangeRequest,
  EmailChangeResponse,
  EmailChangeConfirmRequest,
  EmailVerificationStatus
} from '../../types/authentication/email'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseEmailReturn {
  // State selectors (performance optimized)
  verificationStatus: ReturnType<typeof emailSelectors.verificationStatus>
  verificationInProgress: boolean
  isLoading: boolean
  error: string | null

  // Computed state
  isEmailVerified: boolean
  pendingEmailChange: string | null
  passwordResetSuccess: boolean
  emailChangeSuccess: boolean

  // Actions (stable references)
  requestVerificationCode: (data: EmailVerificationRequest) => Promise<EmailVerificationResponse>
  verifyCode: (data: EmailVerificationConfirmRequest) => Promise<EmailVerificationResponse>
  requestPasswordReset: (data: PasswordResetRequest) => Promise<PasswordResetResponse>
  confirmPasswordReset: (data: PasswordResetConfirmRequest) => Promise<PasswordResetResponse>
  requestEmailChange: (data: EmailChangeRequest) => Promise<EmailChangeResponse>
  confirmEmailChange: (data: EmailChangeConfirmRequest) => Promise<EmailChangeResponse>
  getVerificationStatus: () => Promise<EmailVerificationStatus>
  clearError: () => void
  resetVerificationFlow: () => void
  resetPasswordResetFlow: () => void
  resetEmailChangeFlow: () => void
}

// ============================================================================
// Main Email Hook
// ============================================================================

export function useEmail(): UseEmailReturn {
  // Selective store subscriptions (performance optimized)
  const verificationStatus = useEmailStore(emailSelectors.verificationStatus)
  const verificationInProgress = useEmailStore(emailSelectors.verificationInProgress)
  const isLoading = useEmailStore(emailSelectors.isLoading)
  const error = useEmailStore(emailSelectors.error)
  const isEmailVerified = useEmailStore(emailSelectors.isEmailVerified)
  const pendingEmailChange = useEmailStore(emailSelectors.pendingEmailChange)
  const passwordResetSuccess = useEmailStore(emailSelectors.passwordResetSuccess)
  const emailChangeSuccess = useEmailStore(emailSelectors.emailChangeSuccess)

  // Store success handlers (matching authStore pattern)
  const setVerificationRequestSuccess = useEmailStore(state => state.setVerificationRequestSuccess)
  const setVerificationConfirmSuccess = useEmailStore(state => state.setVerificationConfirmSuccess)
  const setPasswordResetRequestSuccess = useEmailStore(state => state.setPasswordResetRequestSuccess)
  const setPasswordResetConfirmSuccess = useEmailStore(state => state.setPasswordResetConfirmSuccess)
  const setEmailChangeRequestSuccess = useEmailStore(state => state.setEmailChangeRequestSuccess)
  const setEmailChangeConfirmSuccess = useEmailStore(state => state.setEmailChangeConfirmSuccess)
  const setVerificationStatus = useEmailStore(state => state.setVerificationStatus)

  // UI State actions
  const setLoading = useEmailStore(state => state.setLoading)
  const setError = useEmailStore(state => state.setError)
  const clearError = useEmailStore(state => state.clearError)
  const resetVerificationFlow = useEmailStore(state => state.resetVerificationFlow)
  const resetPasswordResetFlow = useEmailStore(state => state.resetPasswordResetFlow)
  const resetEmailChangeFlow = useEmailStore(state => state.resetEmailChangeFlow)

  // ============================================================================
  // Stable Action Implementations (matching useAuth pattern)
  // ============================================================================

  const requestVerificationCode = useCallback(async (data: EmailVerificationRequest): Promise<EmailVerificationResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await emailService.requestVerificationCode(data)

      if (response.success) {
        setVerificationRequestSuccess(response)
        return response
      }

      throw new Error(response.error || 'Email verification request failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Email verification request failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setVerificationRequestSuccess])

  const verifyCode = useCallback(async (data: EmailVerificationConfirmRequest): Promise<EmailVerificationResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await emailService.verifyCode(data)

      if (response.success) {
        setVerificationConfirmSuccess(response)
        return response
      }

      throw new Error(response.error || 'Code verification failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Code verification failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setVerificationConfirmSuccess])

  const requestPasswordReset = useCallback(async (data: PasswordResetRequest): Promise<PasswordResetResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await emailService.requestPasswordReset(data)

      if (response.success) {
        setPasswordResetRequestSuccess(response)
        return response
      }

      throw new Error(response.error || 'Password reset request failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset request failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setPasswordResetRequestSuccess])

  const confirmPasswordReset = useCallback(async (data: PasswordResetConfirmRequest): Promise<PasswordResetResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await emailService.confirmPasswordReset(data)

      if (response.success) {
        setPasswordResetConfirmSuccess(response)
        return response
      }

      throw new Error(response.error || 'Password reset confirmation failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset confirmation failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setPasswordResetConfirmSuccess])

  const requestEmailChange = useCallback(async (data: EmailChangeRequest): Promise<EmailChangeResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await emailService.requestEmailChange(data)

      if (response.success) {
        setEmailChangeRequestSuccess(response, data.new_email)
        return response
      }

      throw new Error(response.error || 'Email change request failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Email change request failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setEmailChangeRequestSuccess])

  const confirmEmailChange = useCallback(async (data: EmailChangeConfirmRequest): Promise<EmailChangeResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await emailService.confirmEmailChange(data)

      if (response.success) {
        setEmailChangeConfirmSuccess(response)
        return response
      }

      throw new Error(response.error || 'Email change confirmation failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Email change confirmation failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setEmailChangeConfirmSuccess])

  const getVerificationStatus = useCallback(async (): Promise<EmailVerificationStatus> => {
    try {
      setLoading(true)
      setError(null)

      const response = await emailService.getVerificationStatus()
      setVerificationStatus(response)
      return response
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get verification status'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setVerificationStatus])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    verificationStatus,
    verificationInProgress,
    isLoading,
    error,

    // Computed state
    isEmailVerified,
    pendingEmailChange,
    passwordResetSuccess,
    emailChangeSuccess,

    // Actions (stable)
    requestVerificationCode,
    verifyCode,
    requestPasswordReset,
    confirmPasswordReset,
    requestEmailChange,
    confirmEmailChange,
    getVerificationStatus,
    clearError,
    resetVerificationFlow,
    resetPasswordResetFlow,
    resetEmailChangeFlow
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for verification status only - minimal re-renders
 */
export function useEmailVerificationStatus() {
  return {
    verificationStatus: useEmailStore(emailSelectors.verificationStatus),
    isEmailVerified: useEmailStore(emailSelectors.isEmailVerified),
    verificationInProgress: useEmailStore(emailSelectors.verificationInProgress)
  }
}

/**
 * Hook for password reset functionality only - minimal re-renders
 */
export function usePasswordReset() {
  return {
    passwordResetInProgress: useEmailStore(emailSelectors.passwordResetInProgress),
    passwordResetSuccess: useEmailStore(emailSelectors.passwordResetSuccess),
    passwordResetError: useEmailStore(emailSelectors.passwordResetError)
  }
}

/**
 * Hook for email change functionality only - minimal re-renders
 */
export function useEmailChange() {
  return {
    emailChangeInProgress: useEmailStore(emailSelectors.emailChangeInProgress),
    emailChangeSuccess: useEmailStore(emailSelectors.emailChangeSuccess),
    pendingEmailChange: useEmailStore(emailSelectors.pendingEmailChange)
  }
}

// ============================================================================
// Default Export
// ============================================================================

export default useEmail