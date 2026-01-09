/**
 * Core Authentication Store - Zustand 2024 Best Practices
 * Manages user authentication state, tokens, and core auth flow
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  UserData,
  LoginResponse,
  RefreshTokenResponse,
  LeaveWorkspaceResponse,
  SubscriptionData,
  WorkspaceAuthContext
} from '../../types/authentication'
import authService from '../../services/authentication/auth'
import { extractSubscriptionFromJWT } from '../../utils/jwt'
import { CapabilitiesManager } from '../../utils/capabilities'
import { useSubscriptionStore } from '../subscription/subscriptionStore'
import { useWorkspaceStore } from './workspaceStore'

// ============================================================================
// Token Refresh Race Condition Prevention
// ============================================================================

let refreshPromise: Promise<RefreshTokenResponse> | null = null

// ============================================================================
// Auth Store State Interface
// ============================================================================

interface AuthStoreState {
  // Core Authentication State
  user: UserData | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Token Management
  token: string | null
  tokenExpiresAt: number | null

  // User Context
  subscription: SubscriptionData | null
  workspace: WorkspaceAuthContext | null
  capabilities: Record<string, any> | null // Full capabilities from API

  // Session Info
  lastActivity: number | null
  isSessionValid: boolean

  // Initialization State (for session restoration)
  isInitialized: boolean

  // Actions
  setLoginSuccess: (response: LoginResponse) => void
  setLogoutSuccess: () => void
  setRefreshSuccess: (response: RefreshTokenResponse) => void
  setLeaveSuccess: (response: LeaveWorkspaceResponse) => void
  setUser: (user: UserData) => void
  updateUser: (updates: Partial<UserData>) => void
  setSubscription: (subscription: SubscriptionData | null) => void
  setWorkspace: (workspace: WorkspaceAuthContext | null) => void
  setCapabilities: (capabilities: Record<string, any> | null) => void
  syncCapabilities: () => Promise<void>
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  setToken: (token: string, expiresIn?: number) => void
  clearTokens: () => void
  updateLastActivity: () => void
  setInitialized: (initialized: boolean) => void
  initializeSession: () => Promise<void>

  // Computed/Helper Methods
  isTokenExpired: () => boolean
  getTimeUntilExpiry: () => number | null
  hasPermission: (permission: string) => boolean
  can: (feature: string) => boolean
  refreshTokenSafe: () => Promise<RefreshTokenResponse>
}

// ============================================================================
// Create Auth Store with 2024 Best Practices
// ============================================================================

export const useAuthStore = create<AuthStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      token: null,
      tokenExpiresAt: null,
      subscription: null,
      workspace: null,
      capabilities: null,
      lastActivity: null,
      isSessionValid: false,
      isInitialized: false,

      // ========================================================================
      // Authentication Actions
      // ========================================================================

      setLoginSuccess: (response) => {
        set((state) => {
          const accessToken = response.tokens?.access_token

          state.user = response.user || null
          state.isAuthenticated = !!(response.user && accessToken)
          state.isLoading = false
          state.error = null
          state.token = accessToken || null
          state.tokenExpiresAt = response.tokens?.expires_in
            ? Date.now() + (response.tokens.expires_in * 1000)
            : null

          // Extract subscription from JWT (industry standard - Auth0, Firebase, Stripe pattern)
          const subscription = accessToken ? extractSubscriptionFromJWT(accessToken) : null
          state.subscription = subscription

          // Sync subscription to subscriptionStore (keeps all stores in sync)
          useSubscriptionStore.getState().syncFromAuth(subscription)

          // Sync capabilities (fetch if version mismatch)
          if (subscription && response.user) {
            get().syncCapabilities()
          }

          // Workspace from response only (NO JWT extraction - v3.0)
          // Login typically doesn't set workspace context
          // User must explicitly switch to a workspace after login
          state.workspace = response.workspace || null

          // Track workspace context if present
          if (state.workspace?.id) {
            WorkspaceContextManager.setCurrentWorkspace(state.workspace.id)
          } else {
            WorkspaceContextManager.clearWorkspace()
          }

          state.lastActivity = Date.now()
          state.isSessionValid = true
        })
      },

      setLogoutSuccess: () => {
        const userId = get().user?.id

        set((state) => {
          state.user = null
          state.isAuthenticated = false
          state.isLoading = false
          state.error = null
          state.token = null
          state.tokenExpiresAt = null
          state.subscription = null
          state.workspace = null
          state.capabilities = null
          state.lastActivity = null
          state.isSessionValid = false
        })

        // Clear capabilities cache
        if (userId) {
          CapabilitiesManager.clear(userId)
        }

        // Clear workspace context on logout
        WorkspaceContextManager.clearWorkspace()

        // Notify other tabs about logout
        if (typeof window !== 'undefined') {
          localStorage.setItem('auth-logout', Date.now().toString())
          localStorage.removeItem('auth-logout')
        }
      },

      setRefreshSuccess: (response) => {
        set((state) => {
          const accessToken = response.tokens?.access_token
          const expiresIn = response.tokens?.expires_in

          if (accessToken) {
            state.token = accessToken
            state.tokenExpiresAt = expiresIn
              ? Date.now() + (expiresIn * 1000)
              : null

            // Extract subscription from JWT on refresh
            state.subscription = extractSubscriptionFromJWT(accessToken)

            // Sync subscription to subscriptionStore (keeps all stores in sync)
            useSubscriptionStore.getState().syncFromAuth(state.subscription)

            // Sync capabilities (fetch if version mismatch)
            if (state.subscription && state.user) {
              get().syncCapabilities()
            }

            // Workspace context preserved in Zustand (v3.0 - Header-Based Context)
            // Refresh tokens extend sessions, they don't change authorization scope
            // Workspace stays unchanged unless user explicitly switches
            // NO changes to state.workspace - it remains as-is
          }

          if (response.user && state.user) {
            // Merge refresh user data with existing user data
            Object.assign(state.user, response.user)
          }

          state.lastActivity = Date.now()
        })
      },

      setLeaveSuccess: (response) => {
        set((state) => {
          // v3.0 - NO token regeneration on leave workspace
          // Backend just logs the event, frontend clears workspace context

          // Clear workspace context (user left workspace)
          state.workspace = null

          // Sync to workspaceStore - clear currentWorkspace
          useWorkspaceStore.getState().setCurrentWorkspace(null)

          // Clear localStorage tracking
          WorkspaceContextManager.clearWorkspace()

          state.lastActivity = Date.now()
        })
      },

      // ========================================================================
      // User Management Actions
      // ========================================================================

      setUser: (user) => {
        set((state) => {
          state.user = user
        })
      },

      updateUser: (updates) => {
        set((state) => {
          if (state.user) {
            Object.assign(state.user, updates)
          }
        })
      },

      setSubscription: (subscription) => {
        set((state) => {
          state.subscription = subscription
          if (state.user && subscription) {
            state.user.subscription = subscription
          }
        })
      },

      setWorkspace: (workspace) => {
        set((state) => {
          state.workspace = workspace
          // Track workspace context for refresh flow
          if (workspace?.id) {
            WorkspaceContextManager.setCurrentWorkspace(workspace.id)
          } else {
            WorkspaceContextManager.clearWorkspace()
          }
        })
      },

      setCapabilities: (capabilities) => {
        set((state) => {
          state.capabilities = capabilities
        })
      },

      syncCapabilities: async () => {
        const { subscription, user } = get()
        if (!subscription || !user) return

        try {
          const capabilities = await CapabilitiesManager.getCapabilities(subscription, user.id)
          set((state) => {
            state.capabilities = capabilities
          })
        } catch (error) {
          console.error('Failed to sync capabilities:', error)
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
      // Token Management Actions
      // ========================================================================

      setToken: (token, expiresIn) => {
        set((state) => {
          state.token = token
          state.tokenExpiresAt = expiresIn
            ? Date.now() + (expiresIn * 1000)
            : null
          state.isAuthenticated = !!token
        })
      },

      clearTokens: () => {
        set((state) => {
          state.token = null
          state.tokenExpiresAt = null
          state.isAuthenticated = false
        })
      },

      updateLastActivity: () => {
        set((state) => {
          state.lastActivity = Date.now()
        })
      },

      setInitialized: (initialized) => {
        set((state) => {
          state.isInitialized = initialized
        })
      },

      initializeSession: async () => {
        // Already initialized, skip
        if (get().isInitialized) return

        try {
          // Try to restore session from refresh token cookie
          const response = await authService.refreshToken()

          if (response.tokens?.access_token) {
            // Session restored successfully - setRefreshSuccess extracts subscription from JWT
            get().setRefreshSuccess(response)

            // If we got user data, update the store
            if (response.user) {
              const fullUserData: UserData = {
                ...response.user,
                bio: '',
                phone_verified: false,
                two_factor_enabled: false,
                preferred_auth_method: 'password',
                security_notifications: true,
                created_at: new Date().toISOString(),
                // Subscription comes from JWT (already set by setRefreshSuccess)
                subscription: get().subscription!
              }
              get().setUser(fullUserData)
            }

            // Initialize workspace store from JWT if workspace context exists
            const workspace = get().workspace
            if (workspace?.id) {
              useWorkspaceStore.getState().setCurrentWorkspace(workspace)
            }

            set((state) => {
              state.isAuthenticated = true
              state.isSessionValid = true
            })
          }
        } catch {
          // No valid refresh token or session expired - this is normal
          console.log('No valid session to restore')
        } finally {
          // Mark as initialized regardless of success
          get().setInitialized(true)
        }
      },

      // ========================================================================
      // Computed/Helper Methods
      // ========================================================================

      isTokenExpired: () => {
        const { tokenExpiresAt } = get()
        if (!tokenExpiresAt) return true
        return Date.now() >= tokenExpiresAt
      },

      getTimeUntilExpiry: () => {
        const { tokenExpiresAt } = get()
        if (!tokenExpiresAt) return null
        const timeLeft = tokenExpiresAt - Date.now()
        return timeLeft > 0 ? timeLeft : 0
      },

      hasPermission: (permission) => {
        const { workspace } = get()
        return workspace?.permissions?.includes(permission) ?? false
      },

      can: (feature) => {
        const { capabilities } = get()
        return !!capabilities?.[feature]
      },

      refreshTokenSafe: async () => {
        if (refreshPromise) return refreshPromise

        refreshPromise = authService.refreshToken()
        try {
          const result = await refreshPromise
          get().setRefreshSuccess(result)
          return result
        } finally {
          refreshPromise = null
        }
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance (2024 Best Practice)
// ============================================================================

export const authSelectors = {
  // Core selectors
  isAuthenticated: (state: AuthStoreState) => state.isAuthenticated,
  isInitialized: (state: AuthStoreState) => state.isInitialized,
  user: (state: AuthStoreState) => state.user,
  workspace: (state: AuthStoreState) => state.workspace,
  subscription: (state: AuthStoreState) => state.subscription,
  capabilities: (state: AuthStoreState) => state.capabilities,
  isLoading: (state: AuthStoreState) => state.isLoading,
  error: (state: AuthStoreState) => state.error,
  token: (state: AuthStoreState) => state.token,

  // Computed selectors
  isFullyAuthenticated: (state: AuthStoreState) =>
    state.isAuthenticated && state.user !== null,
  hasActiveSubscription: (state: AuthStoreState) =>
    state.subscription?.status === 'active',
  isTrialUser: (state: AuthStoreState) =>
    state.subscription?.tier === 'free' || false,
  userDisplayName: (state: AuthStoreState) =>
    state.user ? `${state.user.first_name} ${state.user.last_name}` : null,
  currentWorkspaceName: (state: AuthStoreState) =>
    state.workspace?.name || null,

  // Trial selectors (O(1) performance)
  trial: (state: AuthStoreState) => state.subscription?.trial || null,
  isTrialEligible: (state: AuthStoreState) =>
    state.subscription?.trial?.eligible ?? false,
  hasUsedTrial: (state: AuthStoreState) =>
    state.subscription?.trial?.used_trial ?? false,
  isOnActiveTrial: (state: AuthStoreState) => {
    const trial = state.subscription?.trial;
    if (!trial?.current_tier) return false;
    if (!trial?.expires_at) return false;
    return new Date(trial.expires_at) > new Date();
  },
  trialDaysRemaining: (state: AuthStoreState) =>
    state.subscription?.trial?.days_remaining ?? null,
  canUpgradeTrial: (state: AuthStoreState) =>
    state.subscription?.trial?.can_upgrade ?? false,

  // Workspace limit selectors (from capabilities API)
  maxWorkspaces: (state: AuthStoreState) =>
    state.capabilities?.max_workspaces ?? 1,
  deploymentAllowed: (state: AuthStoreState) =>
    state.capabilities?.deployment_allowed ?? false,
  customDomainsLimit: (state: AuthStoreState) =>
    state.capabilities?.custom_domains ?? 0,
  storageGb: (state: AuthStoreState) =>
    state.capabilities?.storage_gb ?? 0,
  bandwidthGb: (state: AuthStoreState) =>
    state.capabilities?.bandwidth_gb ?? 0,
}

// ============================================================================
// Cross-Tab Sync Setup
// ============================================================================

if (typeof window !== 'undefined') {
  const handleStorageChange = (e: StorageEvent) => {
    if (e.key === 'auth-logout' && e.newValue) {
      useAuthStore.getState().setLogoutSuccess()
    }
  }

  window.addEventListener('storage', handleStorageChange)
}

// ============================================================================
// Workspace Context Tracking (Cross-Tab Sync Safe)
// ============================================================================

/**
 * Workspace Context Manager - Industry Standard for Multi-Tenant Apps
 *
 * v3.0 - Header-Based Workspace Context (Shopify/Stripe/Linear Pattern):
 * - Workspace sent via X-Workspace-Id header per-request (NOT in JWT)
 * - Zustand maintains workspace state across refreshes
 * - localStorage provides persistence across page reloads
 * - Eliminates context drift, race conditions, and stale workspace bugs
 *
 * Security Note: workspace_id is a non-sensitive UUID reference, safe for localStorage
 * NEVER store tokens or PII here - only context identifiers
 *
 * Benefits:
 * - No stale workspace context (header always current) ✅
 * - No token re-issuance on switch (just update state) ✅
 * - Instant workspace switching (no race conditions) ✅
 * - Cross-tab synchronization (user switches workspace, all tabs update) ✅
 * - Survives page refresh (better UX than sessionStorage) ✅
 */
export const WorkspaceContextManager = {
  /**
   * Set current workspace context
   * Called when user switches to a workspace
   */
  setCurrentWorkspace: (workspaceId: string | null): void => {
    if (typeof window === 'undefined') return

    if (workspaceId) {
      localStorage.setItem('current_workspace_id', workspaceId)
      // Notify other tabs about workspace switch
      localStorage.setItem('workspace-switch', Date.now().toString())
      localStorage.removeItem('workspace-switch')
    } else {
      localStorage.removeItem('current_workspace_id')
    }
  },

  /**
   * Get current workspace context
   * Returns workspace_id if user is in a workspace, null otherwise
   */
  getCurrentWorkspace: (): string | null => {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('current_workspace_id')
  },

  /**
   * Clear workspace context
   * Called on logout or when user leaves workspace
   */
  clearWorkspace: (): void => {
    if (typeof window === 'undefined') return
    localStorage.removeItem('current_workspace_id')
  },

  /**
   * Check if user is currently in a workspace
   */
  hasWorkspaceContext: (): boolean => {
    return !!WorkspaceContextManager.getCurrentWorkspace()
  }
}

// ============================================================================
// Workspace Restoration (Race Condition Safe)
// ============================================================================

import workspaceService from '../../services/authentication/workspace'

let workspaceRestorePromise: Promise<WorkspaceAuthContext | null> | null = null

/**
 * Restore workspace context safely (prevents multiple parallel calls)
 * Uses same promise-queuing pattern as refreshTokenSafe
 *
 * @param workspaceId - Workspace ID to restore
 * @returns WorkspaceAuthContext if successful, null if failed
 *
 * When to use:
 * - After successful login when intent has workspaceId
 * - On page refresh to restore previous workspace context
 */
export async function restoreWorkspaceSafe(workspaceId: string): Promise<WorkspaceAuthContext | null> {
  // Already restoring - return existing promise (prevents race condition)
  if (workspaceRestorePromise) {
    console.log('[Auth] Workspace restore already in progress, waiting...')
    return workspaceRestorePromise
  }

  workspaceRestorePromise = (async () => {
    try {
      console.log('[Auth] Restoring workspace:', workspaceId)

      const response = await workspaceService.switchWorkspace(workspaceId)

      if (response.success && response.workspace && response.membership) {
        const workspaceContext: WorkspaceAuthContext = {
          id: response.workspace.id,
          name: response.workspace.name,
          type: response.workspace.type,
          status: response.workspace.status,
          role: response.membership.role,
          permissions: response.membership.permissions,
          is_default: false
        }

        // Update both stores
        useAuthStore.getState().setWorkspace(workspaceContext)

        console.log('✅ Workspace restored:', workspaceContext.name)
        return workspaceContext
      }

      // Restoration failed (user lost access, workspace deleted, etc.)
      console.warn('[Auth] Workspace restoration failed - clearing context')
      WorkspaceContextManager.clearWorkspace()
      return null
    } catch (error) {
      console.error('[Auth] Workspace restoration error:', error)
      WorkspaceContextManager.clearWorkspace()
      return null
    }
  })()

  try {
    return await workspaceRestorePromise
  } finally {
    workspaceRestorePromise = null
  }
}

/**
 * Check if workspace restoration is in progress
 */
export function isRestoringWorkspace(): boolean {
  return workspaceRestorePromise !== null
}

// ============================================================================
// Store Instance and Default Export
// ============================================================================

export default useAuthStore