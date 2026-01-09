/**
 * Phone Store - Zustand 2024 Best Practices
 * Manages phone verification and phone change flows
 * Refactored to match authStore pattern with success handlers
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
    PhoneVerificationResponse,
    PhoneVerificationConfirmResponse,
    PhoneChangeResponse,
    PhoneChangeConfirmResponse,
    PhoneVerificationStatus
} from '../../types/authentication/phone'

// ============================================================================
// Phone Store State Interface
// ============================================================================

interface PhoneStoreState {
    // Phone Verification Flow
    verificationStatus: PhoneVerificationStatus | null
    verificationInProgress: boolean
    pendingPhoneNumber: string | null
    verificationError: string | null

    // Phone Change Flow
    phoneChangeInProgress: boolean
    pendingPhoneChange: string | null
    phoneChangeSuccess: boolean
    phoneChangeError: string | null

    // UI State
    isLoading: boolean
    error: string | null

    // Success Handlers (matching authStore pattern)
    setVerificationRequestSuccess: (response: PhoneVerificationResponse, phoneNumber: string) => void
    setVerificationConfirmSuccess: (response: PhoneVerificationConfirmResponse) => void
    setPhoneChangeRequestSuccess: (response: PhoneChangeResponse, newPhone: string) => void
    setPhoneChangeConfirmSuccess: (response: PhoneChangeConfirmResponse) => void
    setVerificationStatus: (status: PhoneVerificationStatus | null) => void

    // UI State Actions
    setLoading: (loading: boolean) => void
    setError: (error: string | null) => void
    clearError: () => void

    // Flow Control
    setVerificationInProgress: (inProgress: boolean) => void
    setPhoneChangeInProgress: (inProgress: boolean) => void
    resetVerificationFlow: () => void
    resetPhoneChangeFlow: () => void

    // Helper Methods
    isPhoneVerified: () => boolean
}

// ============================================================================
// Create Phone Store
// ============================================================================

export const usePhoneStore = create<PhoneStoreState>()(
    subscribeWithSelector(
        immer((set, get) => ({
            // ========================================================================
            // Initial State
            // ========================================================================
            verificationStatus: null,
            verificationInProgress: false,
            pendingPhoneNumber: null,
            verificationError: null,
            phoneChangeInProgress: false,
            pendingPhoneChange: null,
            phoneChangeSuccess: false,
            phoneChangeError: null,
            isLoading: false,
            error: null,

            // ========================================================================
            // Success Handlers (matching authStore pattern)
            // ========================================================================

            setVerificationRequestSuccess: (response, phoneNumber) => {
                set((state) => {
                    state.verificationInProgress = true
                    state.pendingPhoneNumber = phoneNumber
                    state.verificationError = null
                    state.error = null
                })
            },

            setVerificationConfirmSuccess: (response) => {
                set((state) => {
                    state.verificationInProgress = false
                    state.pendingPhoneNumber = null
                    state.verificationError = null
                    state.error = null
                    // Update verification status if we have it
                    if (state.verificationStatus) {
                        state.verificationStatus.phone_verified = true
                    }
                })
            },

            setPhoneChangeRequestSuccess: (response, newPhone) => {
                set((state) => {
                    state.phoneChangeInProgress = true
                    state.pendingPhoneChange = newPhone
                    state.phoneChangeError = null
                    state.phoneChangeSuccess = false
                    state.error = null
                })
            },

            setPhoneChangeConfirmSuccess: (response) => {
                set((state) => {
                    state.phoneChangeInProgress = false
                    state.phoneChangeSuccess = true
                    state.pendingPhoneChange = null
                    state.phoneChangeError = null
                    state.error = null
                    // Update verification status with new phone
                    if (state.verificationStatus && response.phone_number) {
                        state.verificationStatus.phone_number = response.phone_number
                        state.verificationStatus.phone_verified = true
                    }
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
                        state.phoneChangeInProgress = false
                    }
                })
            },

            clearError: () => {
                set((state) => {
                    state.error = null
                    state.verificationError = null
                    state.phoneChangeError = null
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

            setPhoneChangeInProgress: (inProgress) => {
                set((state) => {
                    state.phoneChangeInProgress = inProgress
                    if (inProgress) {
                        state.phoneChangeError = null
                        state.phoneChangeSuccess = false
                    }
                })
            },

            resetVerificationFlow: () => {
                set((state) => {
                    state.verificationInProgress = false
                    state.pendingPhoneNumber = null
                    state.verificationError = null
                })
            },

            resetPhoneChangeFlow: () => {
                set((state) => {
                    state.phoneChangeInProgress = false
                    state.pendingPhoneChange = null
                    state.phoneChangeError = null
                    state.phoneChangeSuccess = false
                })
            },

            // ========================================================================
            // Helper Methods
            // ========================================================================

            isPhoneVerified: () => {
                const { verificationStatus } = get()
                return verificationStatus?.phone_verified === true
            }
        }))
    )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const phoneSelectors = {
    // Core selectors
    verificationStatus: (state: PhoneStoreState) => state.verificationStatus,
    verificationInProgress: (state: PhoneStoreState) => state.verificationInProgress,
    verificationError: (state: PhoneStoreState) => state.verificationError,
    pendingPhoneNumber: (state: PhoneStoreState) => state.pendingPhoneNumber,
    phoneChangeInProgress: (state: PhoneStoreState) => state.phoneChangeInProgress,
    phoneChangeSuccess: (state: PhoneStoreState) => state.phoneChangeSuccess,
    phoneChangeError: (state: PhoneStoreState) => state.phoneChangeError,
    pendingPhoneChange: (state: PhoneStoreState) => state.pendingPhoneChange,
    isLoading: (state: PhoneStoreState) => state.isLoading,
    error: (state: PhoneStoreState) => state.error,

    // Computed selectors
    isPhoneVerified: (state: PhoneStoreState) => state.verificationStatus?.phone_verified === true,
    phoneNumber: (state: PhoneStoreState) => state.verificationStatus?.phone_number || null,
    hasAnyError: (state: PhoneStoreState) =>
        !!(state.error || state.verificationError || state.phoneChangeError),
    hasAnyInProgress: (state: PhoneStoreState) =>
        state.verificationInProgress || state.phoneChangeInProgress || state.isLoading,
    hasPendingVerification: (state: PhoneStoreState) =>
        state.verificationStatus?.has_pending_verification === true
}

// ============================================================================
// Default Export
// ============================================================================

export default usePhoneStore
