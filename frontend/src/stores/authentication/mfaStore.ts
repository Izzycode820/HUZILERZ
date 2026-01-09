/**
 * MFA (Multi-Factor Authentication) Zustand Store
 * Manages TOTP setup, verification flows, and backup codes
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  MFAStatus,
  MFAChallenge,
  MFAChallengeRequest,
  MFAChallengeResponse,
} from '../../types/authentication'
import type {
  TOTPDevice,
  BackupCodesStats,
  TOTPSetupResponse,
  MFAVerifyResponse,
  MFASetupStep,
  MFAVerificationFlow,
  MFASetupFlow,
  BackupCodesRegenerateResponse,
} from '../../types/authentication/mfa'

// ============================================================================
// Store State Interface
// ============================================================================

interface MFAStoreState {
  // MFA Status
  mfaStatus: MFAStatus | null
  isLoading: boolean
  error: string | null

  // TOTP Device
  totpDevice: TOTPDevice | null

  // Backup Codes
  backupCodesStats: BackupCodesStats | null
  generatedBackupCodes: string[] | null
  backupCodesVisible: boolean

  // Setup Flow State
  setupFlow: MFASetupFlow

  // Verification Flow State
  verificationFlow: MFAVerificationFlow

  // UI State
  showSetupModal: boolean
  showVerificationModal: boolean
  showBackupCodesModal: boolean

  // Last Update (for cross-tab sync)
  lastUpdate: number
}

interface MFAStoreActions {
  // MFA Status Management
  setMFAStatus: (status: MFAStatus) => void
  refreshMFAStatus: () => Promise<void>

  // TOTP Setup Flow
  startTOTPSetup: () => void
  setTOTPSetupData: (data: TOTPSetupResponse['data']) => void
  confirmTOTPSetup: (backupCodes: string[]) => void
  completeTOTPSetup: () => void
  cancelTOTPSetup: () => void

  // MFA Verification Flow
  startMFAVerification: (challengeId?: string) => void
  setMFAVerificationResult: (result: MFAVerifyResponse) => void
  completeMFAVerification: () => void
  cancelMFAVerification: () => void

  // Backup Codes Management
  setBackupCodes: (codes: string[]) => void
  setBackupCodesStats: (stats: BackupCodesStats) => void
  setBackupCodesRegenerateResult: (result: BackupCodesRegenerateResponse) => void
  hideBackupCodes: () => void

  // Device Management
  setTOTPDevice: (device: TOTPDevice) => void
  lockTOTPDevice: () => void
  unlockTOTPDevice: () => void

  // UI State Management
  setShowSetupModal: (show: boolean) => void
  setShowVerificationModal: (show: boolean) => void
  setShowBackupCodesModal: (show: boolean) => void
  setSetupStep: (step: MFASetupStep) => void

  // Error and Loading
  setError: (error: string | null) => void
  clearError: () => void
  setLoading: (loading: boolean) => void

  // Utilities
  isMFAEnabled: () => boolean
  canUseMFA: () => boolean
  hasBackupCodes: () => boolean
  getSecurityScore: () => number

  // Reset
  reset: () => void
}

export type MFAStore = MFAStoreState & MFAStoreActions

// ============================================================================
// Initial State
// ============================================================================

const initialSetupFlow: MFASetupFlow = {
  currentStep: 'setup',
  setupData: null,
  backupCodes: null,
  isLoading: false,
  error: null,
}

const initialVerificationFlow: MFAVerificationFlow = {
  isRequired: false,
  challengeId: undefined,
  challengeType: undefined,
  attemptsRemaining: 3,
  isLoading: false,
  error: null,
}

const initialState: MFAStoreState = {
  mfaStatus: null,
  isLoading: false,
  error: null,
  totpDevice: null,
  backupCodesStats: null,
  generatedBackupCodes: null,
  backupCodesVisible: false,
  setupFlow: initialSetupFlow,
  verificationFlow: initialVerificationFlow,
  showSetupModal: false,
  showVerificationModal: false,
  showBackupCodesModal: false,
  lastUpdate: Date.now(),
}

// ============================================================================
// Zustand Store
// ============================================================================

export const useMFAStore = create<MFAStore>()(
  persist(
    (set, get) => ({
      // Initial State
      ...initialState,

      // ========================================================================
      // MFA Status Management
      // ========================================================================

      setMFAStatus: (status) => {
        set({
          mfaStatus: status,
          totpDevice: status.totp_device,
          backupCodesStats: status.backup_codes,
          lastUpdate: Date.now(),
        })
      },

      refreshMFAStatus: async () => {
        // This will be implemented by services layer
        set({ isLoading: true })
        // The actual API call will be in the service layer
      },

      // ========================================================================
      // TOTP Setup Flow
      // ========================================================================

      startTOTPSetup: () => {
        set({
          setupFlow: {
            ...initialSetupFlow,
            currentStep: 'setup',
          },
          showSetupModal: true,
          error: null,
          lastUpdate: Date.now(),
        })
      },

      setTOTPSetupData: (data) => {
        set({
          setupFlow: {
            ...get().setupFlow,
            currentStep: 'scan',
            setupData: data,
            isLoading: false,
            error: null,
          },
          lastUpdate: Date.now(),
        })
      },

      confirmTOTPSetup: (backupCodes) => {
        set({
          setupFlow: {
            ...get().setupFlow,
            currentStep: 'backup-codes',
            backupCodes,
            isLoading: false,
            error: null,
          },
          generatedBackupCodes: backupCodes,
          backupCodesVisible: true,
          lastUpdate: Date.now(),
        })
      },

      completeTOTPSetup: () => {
        set({
          setupFlow: {
            ...get().setupFlow,
            currentStep: 'complete',
          },
          showSetupModal: false,
          generatedBackupCodes: null,
          backupCodesVisible: false,
          lastUpdate: Date.now(),
        })
      },

      cancelTOTPSetup: () => {
        set({
          setupFlow: initialSetupFlow,
          showSetupModal: false,
          generatedBackupCodes: null,
          backupCodesVisible: false,
          error: null,
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // MFA Verification Flow
      // ========================================================================

      startMFAVerification: (challengeId) => {
        set({
          verificationFlow: {
            isRequired: true,
            challengeId,
            challengeType: 'totp',
            attemptsRemaining: 3,
            isLoading: false,
            error: null,
          },
          showVerificationModal: true,
          lastUpdate: Date.now(),
        })
      },

      setMFAVerificationResult: (result) => {
        const current = get().verificationFlow

        if (result.success) {
          set({
            verificationFlow: {
              ...current,
              isLoading: false,
              error: null,
            },
            lastUpdate: Date.now(),
          })
        } else {
          set({
            verificationFlow: {
              ...current,
              attemptsRemaining: Math.max(0, current.attemptsRemaining - 1),
              isLoading: false,
              error: result.message || 'Verification failed',
            },
            lastUpdate: Date.now(),
          })
        }
      },

      completeMFAVerification: () => {
        set({
          verificationFlow: initialVerificationFlow,
          showVerificationModal: false,
          lastUpdate: Date.now(),
        })
      },

      cancelMFAVerification: () => {
        set({
          verificationFlow: initialVerificationFlow,
          showVerificationModal: false,
          error: null,
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Backup Codes Management
      // ========================================================================

      setBackupCodes: (codes) => {
        set({
          generatedBackupCodes: codes,
          backupCodesVisible: true,
          lastUpdate: Date.now(),
        })
      },

      setBackupCodesStats: (stats) => {
        set({
          backupCodesStats: stats,
          lastUpdate: Date.now(),
        })
      },

      setBackupCodesRegenerateResult: (result) => {
        if (result.success && result.data) {
          set({
            generatedBackupCodes: result.data.backup_codes,
            backupCodesVisible: true,
            showBackupCodesModal: true,
            lastUpdate: Date.now(),
          })
        }
      },

      hideBackupCodes: () => {
        set({
          generatedBackupCodes: null,
          backupCodesVisible: false,
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Device Management
      // ========================================================================

      setTOTPDevice: (device) => {
        set({
          totpDevice: device,
          lastUpdate: Date.now(),
        })
      },

      lockTOTPDevice: () => {
        const current = get().totpDevice
        if (current) {
          set({
            totpDevice: {
              ...current,
              is_locked: true,
              lockout_until: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30 minutes
            },
            lastUpdate: Date.now(),
          })
        }
      },

      unlockTOTPDevice: () => {
        const current = get().totpDevice
        if (current) {
          set({
            totpDevice: {
              ...current,
              is_locked: false,
              lockout_until: undefined,
              failure_count: 0,
            },
            lastUpdate: Date.now(),
          })
        }
      },

      // ========================================================================
      // UI State Management
      // ========================================================================

      setShowSetupModal: (show) => {
        set({
          showSetupModal: show,
          lastUpdate: Date.now(),
        })
      },

      setShowVerificationModal: (show) => {
        set({
          showVerificationModal: show,
          lastUpdate: Date.now(),
        })
      },

      setShowBackupCodesModal: (show) => {
        set({
          showBackupCodesModal: show,
          lastUpdate: Date.now(),
        })
      },

      setSetupStep: (step) => {
        set({
          setupFlow: {
            ...get().setupFlow,
            currentStep: step,
          },
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Error and Loading
      // ========================================================================

      setError: (error) => {
        set({
          error,
          isLoading: false,
          lastUpdate: Date.now(),
        })
      },

      clearError: () => {
        set({
          error: null,
          setupFlow: {
            ...get().setupFlow,
            error: null,
          },
          verificationFlow: {
            ...get().verificationFlow,
            error: null,
          },
          lastUpdate: Date.now(),
        })
      },

      setLoading: (loading) => {
        set({
          isLoading: loading,
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Utilities
      // ========================================================================

      isMFAEnabled: () => {
        return get().mfaStatus?.mfa_enabled ?? false
      },

      canUseMFA: () => {
        const { totpDevice } = get()
        if (!totpDevice) return false
        return Boolean(totpDevice.is_confirmed && totpDevice.is_active && !totpDevice.is_locked)
      },

      hasBackupCodes: () => {
        const { backupCodesStats } = get()
        return (backupCodesStats?.unused ?? 0) > 0
      },

      getSecurityScore: () => {
        return get().mfaStatus?.security_score ?? 0
      },

      // ========================================================================
      // Reset
      // ========================================================================

      reset: () => {
        set({
          ...initialState,
          lastUpdate: Date.now(),
        })
      },
    }),
    {
      name: 'huzilerz-mfa-store',
      partialize: (state) => ({
        // Only persist non-sensitive UI state
        mfaStatus: state.mfaStatus,
        totpDevice: state.totpDevice,
        backupCodesStats: state.backupCodesStats,
        // Don't persist actual backup codes or sensitive setup data
        setupFlow: {
          currentStep: state.setupFlow.currentStep,
          isLoading: false,
          error: null,
          setupData: null,
          backupCodes: null,
        },
        verificationFlow: initialVerificationFlow,
        showSetupModal: false,
        showVerificationModal: false,
        showBackupCodesModal: false,
        backupCodesVisible: false,
        generatedBackupCodes: null,
      }),
    }
  )
)

// ============================================================================
// Selectors (for performance optimization)
// ============================================================================

export const mfaSelectors = {
  isMFAEnabled: (state: MFAStore) => state.isMFAEnabled(),
  canUseMFA: (state: MFAStore) => state.canUseMFA(),
  hasBackupCodes: (state: MFAStore) => state.hasBackupCodes(),
  securityScore: (state: MFAStore) => state.getSecurityScore(),
  setupStep: (state: MFAStore) => state.setupFlow.currentStep,
  isSetupInProgress: (state: MFAStore) => state.showSetupModal,
  isVerificationRequired: (state: MFAStore) => state.verificationFlow.isRequired,
  attemptsRemaining: (state: MFAStore) => state.verificationFlow.attemptsRemaining,
  totpDevice: (state: MFAStore) => state.totpDevice,
  backupCodesStats: (state: MFAStore) => state.backupCodesStats,
  isLoading: (state: MFAStore) => state.isLoading,
  error: (state: MFAStore) => state.error,
}

// ============================================================================
// Cross-tab Synchronization
// ============================================================================

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === 'huzilerz-mfa-store') {
      const store = useMFAStore.getState()
      const newData = e.newValue ? JSON.parse(e.newValue) : null

      if (newData?.state?.lastUpdate > store.lastUpdate) {
        // Sync MFA status from other tab
        if (newData.state.mfaStatus) store.setMFAStatus(newData.state.mfaStatus)
        if (newData.state.totpDevice) store.setTOTPDevice(newData.state.totpDevice)
        if (newData.state.backupCodesStats) store.setBackupCodesStats(newData.state.backupCodesStats)
      }
    }
  })
}

// ============================================================================
// Store Instance Export
// ============================================================================

export default useMFAStore