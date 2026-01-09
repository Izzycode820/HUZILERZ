/**
 * Phone Hook - 2024 Best Practices with Zustand
 * Custom hook layer for phone store - handles verification and phone change
 * Refactored to match useAuth pattern with success handlers
 */

import { useCallback } from 'react'
import { usePhoneStore, phoneSelectors } from '../../stores/authentication/phoneStore'
import phoneService from '../../services/authentication/phone'
import type {
    PhoneVerificationRequest,
    PhoneVerificationResponse,
    PhoneVerificationConfirmRequest,
    PhoneVerificationConfirmResponse,
    PhoneChangeRequest,
    PhoneChangeResponse,
    PhoneChangeConfirmRequest,
    PhoneChangeConfirmResponse,
    PhoneVerificationStatus
} from '../../types/authentication/phone'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UsePhoneReturn {
    // State selectors (performance optimized)
    verificationStatus: PhoneVerificationStatus | null
    verificationInProgress: boolean
    isLoading: boolean
    error: string | null
    pendingPhoneNumber: string | null

    // Computed state
    isPhoneVerified: boolean
    phoneNumber: string | null
    phoneChangeSuccess: boolean
    pendingPhoneChange: string | null

    // Actions (stable references)
    requestVerificationCode: (data: PhoneVerificationRequest) => Promise<PhoneVerificationResponse>
    verifyCode: (data: PhoneVerificationConfirmRequest) => Promise<PhoneVerificationConfirmResponse>
    requestPhoneChange: (data: PhoneChangeRequest) => Promise<PhoneChangeResponse>
    confirmPhoneChange: (data: PhoneChangeConfirmRequest) => Promise<PhoneChangeConfirmResponse>
    getVerificationStatus: () => Promise<PhoneVerificationStatus | null>
    clearError: () => void
    resetVerificationFlow: () => void
    resetPhoneChangeFlow: () => void
}

// ============================================================================
// Main Phone Hook
// ============================================================================

export function usePhone(): UsePhoneReturn {
    // Selective store subscriptions (performance optimized)
    const verificationStatus = usePhoneStore(phoneSelectors.verificationStatus)
    const verificationInProgress = usePhoneStore(phoneSelectors.verificationInProgress)
    const isLoading = usePhoneStore(phoneSelectors.isLoading)
    const error = usePhoneStore(phoneSelectors.error)
    const pendingPhoneNumber = usePhoneStore(phoneSelectors.pendingPhoneNumber)
    const isPhoneVerified = usePhoneStore(phoneSelectors.isPhoneVerified)
    const phoneNumber = usePhoneStore(phoneSelectors.phoneNumber)
    const phoneChangeSuccess = usePhoneStore(phoneSelectors.phoneChangeSuccess)
    const pendingPhoneChange = usePhoneStore(phoneSelectors.pendingPhoneChange)

    // Store success handlers (matching authStore pattern)
    const setVerificationRequestSuccess = usePhoneStore(state => state.setVerificationRequestSuccess)
    const setVerificationConfirmSuccess = usePhoneStore(state => state.setVerificationConfirmSuccess)
    const setPhoneChangeRequestSuccess = usePhoneStore(state => state.setPhoneChangeRequestSuccess)
    const setPhoneChangeConfirmSuccess = usePhoneStore(state => state.setPhoneChangeConfirmSuccess)
    const setVerificationStatus = usePhoneStore(state => state.setVerificationStatus)

    // UI State actions
    const setLoading = usePhoneStore(state => state.setLoading)
    const setError = usePhoneStore(state => state.setError)
    const clearError = usePhoneStore(state => state.clearError)
    const resetVerificationFlow = usePhoneStore(state => state.resetVerificationFlow)
    const resetPhoneChangeFlow = usePhoneStore(state => state.resetPhoneChangeFlow)

    // ============================================================================
    // Stable Action Implementations (matching useAuth pattern)
    // ============================================================================

    const requestVerificationCode = useCallback(async (data: PhoneVerificationRequest): Promise<PhoneVerificationResponse> => {
        try {
            setLoading(true)
            setError(null)

            const response = await phoneService.requestVerificationCode(data)

            if (response.success) {
                setVerificationRequestSuccess(response, data.phone_number)
                return response
            }

            throw new Error(response.message || 'Phone verification request failed')
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Phone verification request failed'
            setError(errorMessage)
            throw error
        } finally {
            setLoading(false)
        }
    }, [setLoading, setError, setVerificationRequestSuccess])

    const verifyCode = useCallback(async (data: PhoneVerificationConfirmRequest): Promise<PhoneVerificationConfirmResponse> => {
        try {
            setLoading(true)
            setError(null)

            const response = await phoneService.verifyCode(data)

            if (response.success) {
                setVerificationConfirmSuccess(response)
                return response
            }

            throw new Error(response.message || 'Code verification failed')
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Code verification failed'
            setError(errorMessage)
            throw error
        } finally {
            setLoading(false)
        }
    }, [setLoading, setError, setVerificationConfirmSuccess])

    const requestPhoneChange = useCallback(async (data: PhoneChangeRequest): Promise<PhoneChangeResponse> => {
        try {
            setLoading(true)
            setError(null)

            const response = await phoneService.requestPhoneChange(data)

            if (response.success) {
                setPhoneChangeRequestSuccess(response, data.new_phone_number)
                return response
            }

            throw new Error(response.message || 'Phone change request failed')
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Phone change request failed'
            setError(errorMessage)
            throw error
        } finally {
            setLoading(false)
        }
    }, [setLoading, setError, setPhoneChangeRequestSuccess])

    const confirmPhoneChange = useCallback(async (data: PhoneChangeConfirmRequest): Promise<PhoneChangeConfirmResponse> => {
        try {
            setLoading(true)
            setError(null)

            const response = await phoneService.confirmPhoneChange(data)

            if (response.success) {
                setPhoneChangeConfirmSuccess(response)
                return response
            }

            throw new Error(response.message || 'Phone change confirmation failed')
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Phone change confirmation failed'
            setError(errorMessage)
            throw error
        } finally {
            setLoading(false)
        }
    }, [setLoading, setError, setPhoneChangeConfirmSuccess])

    const getVerificationStatus = useCallback(async (): Promise<PhoneVerificationStatus | null> => {
        try {
            setLoading(true)
            setError(null)

            const response = await phoneService.getVerificationStatus()

            if (response.success) {
                const status: PhoneVerificationStatus = {
                    phone_verified: response.phone_verified || false,
                    phone_number: response.phone_number || null,
                    has_pending_verification: response.has_pending_verification || false,
                    pending_expires_at: response.pending_expires_at,
                    rate_limit: response.rate_limit
                }
                setVerificationStatus(status)
                return status
            }

            return null
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
        pendingPhoneNumber,

        // Computed state
        isPhoneVerified,
        phoneNumber,
        phoneChangeSuccess,
        pendingPhoneChange,

        // Actions (stable)
        requestVerificationCode,
        verifyCode,
        requestPhoneChange,
        confirmPhoneChange,
        getVerificationStatus,
        clearError,
        resetVerificationFlow,
        resetPhoneChangeFlow
    }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for verification status only - minimal re-renders
 */
export function usePhoneVerificationStatus() {
    return {
        verificationStatus: usePhoneStore(phoneSelectors.verificationStatus),
        isPhoneVerified: usePhoneStore(phoneSelectors.isPhoneVerified),
        verificationInProgress: usePhoneStore(phoneSelectors.verificationInProgress),
        phoneNumber: usePhoneStore(phoneSelectors.phoneNumber)
    }
}

/**
 * Hook for phone change functionality only - minimal re-renders
 */
export function usePhoneChange() {
    return {
        phoneChangeInProgress: usePhoneStore(phoneSelectors.phoneChangeInProgress),
        phoneChangeSuccess: usePhoneStore(phoneSelectors.phoneChangeSuccess),
        pendingPhoneChange: usePhoneStore(phoneSelectors.pendingPhoneChange)
    }
}

// ============================================================================
// Default Export
// ============================================================================

export default usePhone
