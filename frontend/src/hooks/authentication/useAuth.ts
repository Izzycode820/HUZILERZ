/**
 * Authentication Hook - 2024 Best Practices with Zustand
 * Custom hook layer for auth store - provides clean interface and performance
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { useAuthStore, authSelectors } from '../../stores/authentication/authStore'
import authService from '../../services/authentication/auth'
import type {
  LoginRequest,
  RegisterRequest,
  LoginResponse,
  RegisterResponse
} from '../../types/authentication/auth'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseAuthReturn {
  // State selectors (performance optimized)
  isAuthenticated: boolean
  isFullyAuthenticated: boolean
  user: ReturnType<typeof authSelectors.user>
  workspace: ReturnType<typeof authSelectors.workspace>
  subscription: ReturnType<typeof authSelectors.subscription>
  capabilities: ReturnType<typeof authSelectors.capabilities>
  isLoading: boolean
  error: string | null

  // Computed state
  userDisplayName: string | null
  hasActiveSubscription: boolean
  isTrialUser: boolean

  // Trial helpers (from JWT claims)
  isTrialEligible: boolean
  hasUsedTrial: boolean
  isOnActiveTrial: boolean
  trial: ReturnType<typeof authSelectors.trial>
  trialDaysRemaining: number | null
  canUpgradeTrial: boolean

  // Workspace/subscription limit helpers (from capabilities)
  maxWorkspaces: number
  deploymentAllowed: boolean
  customDomainsLimit: number
  storageGb: number
  bandwidthGb: number

  // Actions (stable references)
  login: (credentials: LoginRequest) => Promise<LoginResponse>
  register: (userData: RegisterRequest) => Promise<RegisterResponse>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  updateUser: (updates: Partial<import('../../types/authentication/auth').UserData>) => void
  clearError: () => void
  updateLastActivity: () => void

  // Capabilities helper
  can: (feature: string) => boolean
}

// ============================================================================
// Main Authentication Hook
// ============================================================================

export function useAuth(): UseAuthReturn {
  // Selective store subscriptions (performance optimized)
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const isFullyAuthenticated = useAuthStore(authSelectors.isFullyAuthenticated)
  const user = useAuthStore(authSelectors.user)
  const workspace = useAuthStore(authSelectors.workspace)
  const subscription = useAuthStore(authSelectors.subscription)
  const capabilities = useAuthStore(authSelectors.capabilities)
  const isLoading = useAuthStore(authSelectors.isLoading)
  const error = useAuthStore(authSelectors.error)
  const userDisplayName = useAuthStore(authSelectors.userDisplayName)
  const hasActiveSubscription = useAuthStore(authSelectors.hasActiveSubscription)
  const isTrialUser = useAuthStore(authSelectors.isTrialUser)

  // Trial selectors (from JWT claims)
  const isTrialEligible = useAuthStore(authSelectors.isTrialEligible)
  const hasUsedTrial = useAuthStore(authSelectors.hasUsedTrial)
  const isOnActiveTrial = useAuthStore(authSelectors.isOnActiveTrial)
  const trial = useAuthStore(authSelectors.trial)
  const trialDaysRemaining = useAuthStore(authSelectors.trialDaysRemaining)
  const canUpgradeTrial = useAuthStore(authSelectors.canUpgradeTrial)

  // Workspace/subscription limit selectors (from capabilities)
  const maxWorkspaces = useAuthStore(authSelectors.maxWorkspaces)
  const deploymentAllowed = useAuthStore(authSelectors.deploymentAllowed)
  const customDomainsLimit = useAuthStore(authSelectors.customDomainsLimit)
  const storageGb = useAuthStore(authSelectors.storageGb)
  const bandwidthGb = useAuthStore(authSelectors.bandwidthGb)

  // Store actions (direct references for performance)
  const setLoginSuccess = useAuthStore((state: any) => state.setLoginSuccess)
  const setLogoutSuccess = useAuthStore((state: any) => state.setLogoutSuccess)
  const setRefreshSuccess = useAuthStore((state: any) => state.setRefreshSuccess)
  // UI State actions
  const setLoading = useAuthStore((state: any) => state.setLoading)
  const setError = useAuthStore((state: any) => state.setError)
  const clearError = useAuthStore((state: any) => state.clearError)
  const resetAuthFlow = useAuthStore((state: any) => state.resetAuthFlow)
  const setMfaRequired = useAuthStore((state: any) => state.setMfaRequired)
  const setContextRestored = useAuthStore((state: any) => state.setContextRestored)
  const setLoggingIn = useAuthStore((state: any) => state.setLoggingIn)
  const updateLastActivity = useAuthStore((state: any) => state.updateLastActivity)
  const updateUser = useAuthStore((state: any) => state.updateUser)
  const can = useAuthStore((state: any) => state.can)

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const login = useCallback(async (credentials: LoginRequest): Promise<LoginResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await authService.login(credentials)

      if (response.tokens?.access_token) {
        setLoginSuccess(response)
        return response
      }

      throw new Error(response.error || 'Login failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setLoginSuccess])

  const register = useCallback(async (userData: RegisterRequest): Promise<RegisterResponse> => {
    try {
      setLoading(true)
      setError(null)

      const response = await authService.register(userData)

      if (response.tokens?.access_token) {
        // Convert RegisterResponse to LoginResponse format for store
        const loginResponse: LoginResponse = {
          success: true,
          user: response.user,
          tokens: response.tokens,
          workspace: undefined
        }
        setLoginSuccess(loginResponse)
        return response
      }

      throw new Error(response.error || 'Registration failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setLoginSuccess])

  const logout = useCallback(async (): Promise<void> => {
    try {
      setLoading(true)

      // Call logout service (handles token cleanup)
      await authService.logout()

      // Update store state
      setLogoutSuccess()
    } catch (error) {
      // Even if logout fails, clear local state
      setLogoutSuccess()
      console.warn('Logout service failed, but local state cleared:', error)
    } finally {
      setLoading(false)
    }
  }, [setLoading, setLogoutSuccess])

  const refreshToken = useCallback(async (): Promise<void> => {
    try {
      const response = await authService.refreshToken()

      if (response.tokens?.access_token) {
        setRefreshSuccess(response)
      } else {
        throw new Error('Token refresh failed')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Token refresh failed'
      setError(errorMessage)
      // On refresh failure, logout user
      setLogoutSuccess()
      throw error
    }
  }, [setRefreshSuccess, setError, setLogoutSuccess])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    isAuthenticated,
    isFullyAuthenticated,
    user,
    workspace,
    subscription,
    capabilities,
    isLoading,
    error,

    // Computed state
    userDisplayName,
    hasActiveSubscription,
    isTrialUser,

    // Trial helpers
    isTrialEligible,
    hasUsedTrial,
    isOnActiveTrial,
    trial,
    trialDaysRemaining,
    canUpgradeTrial,

    // Workspace/subscription limit helpers
    maxWorkspaces,
    deploymentAllowed,
    customDomainsLimit,
    storageGb,
    bandwidthGb,

    // Actions (stable)
    login,
    register,
    logout,
    refreshToken,
    updateUser,
    clearError,
    updateLastActivity,

    // Capabilities helper
    can
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for authentication status only - minimal re-renders
 */
export function useAuthStatus() {
  return {
    isAuthenticated: useAuthStore(authSelectors.isAuthenticated),
    isFullyAuthenticated: useAuthStore(authSelectors.isFullyAuthenticated),
    isLoading: useAuthStore(authSelectors.isLoading)
  }
}

/**
 * Hook for user data only - minimal re-renders
 */
export function useAuthUser() {
  return {
    user: useAuthStore(authSelectors.user),
    userDisplayName: useAuthStore(authSelectors.userDisplayName),
    subscription: useAuthStore(authSelectors.subscription),
    hasActiveSubscription: useAuthStore(authSelectors.hasActiveSubscription),
    isTrialUser: useAuthStore(authSelectors.isTrialUser)
  }
}

/**
 * Hook for auth actions only - no reactive state
 */
export function useAuthActions() {
  const clearError = useAuthStore((state: any) => state.clearError)
  const updateActivity = useAuthStore((state: any) => state.updateLastActivity)

  return { clearError, updateActivity }
}

// ============================================================================
// Default Export
// ============================================================================

export default useAuth