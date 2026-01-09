/**
 * OAuth2 Store - Zustand 2024 Best Practices
 * Manages OAuth2 authentication flows, providers, and state
 * Works directly with OAuth2Service and comprehensive types
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  OAuth2Provider,
  OAuth2InitiateRequest,
  OAuth2InitiateResponse,
  OAuth2CallbackRequest,
  OAuth2CallbackResponse,
  OAuth2TokenRefreshRequest,
  OAuth2TokenRefreshResponse
} from '../../types/authentication/oauth2'

// ============================================================================
// OAuth2 Store State Interface
// ============================================================================

interface OAuth2StoreState {
  // Providers Data
  availableProviders: OAuth2Provider[]
  providersLoaded: boolean

  // OAuth2 Flow State
  currentProvider: string | null
  authorizationUrl: string | null
  state: string | null
  codeVerifier: string | null
  redirectUri: string | null
  scopes: string[]

  // Authentication Flow
  isInitiating: boolean
  isAuthenticating: boolean
  isLinking: boolean
  isUnlinking: string | null
  isRefreshing: boolean

  // Flow Results
  authenticationResult: OAuth2CallbackResponse | null
  linkingResult: any | null

  // UI State
  isLoading: boolean
  error: string | null
  flowInProgress: boolean

  // Session Management
  lastProviderUsed: string | null
  authStartedAt: number | null
  flowTimeout: number | null

  // Actions
  setAvailableProviders: (providers: OAuth2Provider[]) => void
  setCurrentProvider: (provider: string | null) => void
  setAuthorizationFlow: (data: {
    authorizationUrl: string
    state: string
    codeVerifier: string
    redirectUri: string
    scopes: string[]
  }) => void
  setIsInitiating: (initiating: boolean) => void
  setIsAuthenticating: (authenticating: boolean) => void
  setIsLinking: (linking: boolean) => void
  setIsUnlinking: (provider: string | null) => void
  setIsRefreshing: (refreshing: boolean) => void
  setAuthenticationResult: (result: OAuth2CallbackResponse | null) => void
  setLinkingResult: (result: any | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  startFlow: (provider: string) => void
  completeFlow: (result: OAuth2CallbackResponse) => void
  cancelFlow: () => void
  clearFlowData: () => void
  setFlowTimeout: (timeout: number | null) => void

  // Helper Methods
  getProviderByName: (name: string) => OAuth2Provider | null
  isProviderAvailable: (name: string) => boolean
  hasValidState: (receivedState: string) => boolean
  isFlowExpired: () => boolean
  getTimeRemaining: () => number | null
  canInitiateFlow: () => boolean
  getProviderDisplayInfo: (provider: string) => any
}

// ============================================================================
// Create OAuth2 Store
// ============================================================================

export const useOAuth2Store = create<OAuth2StoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      availableProviders: [],
      providersLoaded: false,
      currentProvider: null,
      authorizationUrl: null,
      state: null,
      codeVerifier: null,
      redirectUri: null,
      scopes: [],
      isInitiating: false,
      isAuthenticating: false,
      isLinking: false,
      isUnlinking: null,
      isRefreshing: false,
      authenticationResult: null,
      linkingResult: null,
      isLoading: false,
      error: null,
      flowInProgress: false,
      lastProviderUsed: null,
      authStartedAt: null,
      flowTimeout: null,

      // ========================================================================
      // Provider Management Actions
      // ========================================================================

      setAvailableProviders: (providers) => {
        set((state) => {
          state.availableProviders = providers as any
          state.providersLoaded = true
        })
      },

      setCurrentProvider: (provider) => {
        set((state) => {
          state.currentProvider = provider
          if (provider) {
            state.lastProviderUsed = provider
          }
        })
      },

      // ========================================================================
      // OAuth2 Flow Actions
      // ========================================================================

      setAuthorizationFlow: (data) => {
        set((state) => {
          state.authorizationUrl = data.authorizationUrl
          state.state = data.state
          state.codeVerifier = data.codeVerifier
          state.redirectUri = data.redirectUri
          state.scopes = data.scopes
          state.flowInProgress = true
          state.authStartedAt = Date.now()
          state.error = null
        })
      },

      setIsInitiating: (initiating) => {
        set((state) => {
          state.isInitiating = initiating
          if (initiating) {
            state.error = null
          }
        })
      },

      setIsAuthenticating: (authenticating) => {
        set((state) => {
          state.isAuthenticating = authenticating
          if (authenticating) {
            state.error = null
            state.authenticationResult = null
          }
        })
      },

      setIsLinking: (linking) => {
        set((state) => {
          state.isLinking = linking
          if (linking) {
            state.error = null
            state.linkingResult = null
          }
        })
      },

      setIsUnlinking: (provider) => {
        set((state) => {
          state.isUnlinking = provider
          if (provider) {
            state.error = null
          }
        })
      },

      setIsRefreshing: (refreshing) => {
        set((state) => {
          state.isRefreshing = refreshing
          if (refreshing) {
            state.error = null
          }
        })
      },

      setAuthenticationResult: (result) => {
        set((state) => {
          state.authenticationResult = result
        })
      },

      setLinkingResult: (result) => {
        set((state) => {
          state.linkingResult = result
        })
      },

      // ========================================================================
      // Flow Management Actions
      // ========================================================================

      startFlow: (provider) => {
        set((state) => {
          state.currentProvider = provider
          state.flowInProgress = true
          state.authStartedAt = Date.now()
          state.flowTimeout = Date.now() + (10 * 60 * 1000) // 10 minutes
          state.error = null
          state.authenticationResult = null
          state.linkingResult = null
        })
      },

      completeFlow: (result) => {
        set((state) => {
          state.authenticationResult = result
          state.isInitiating = false
          state.isAuthenticating = false
          state.isLinking = false
          state.flowInProgress = false
          state.error = null
        })
      },

      cancelFlow: () => {
        set((state) => {
          state.flowInProgress = false
          state.isInitiating = false
          state.isAuthenticating = false
          state.isLinking = false
          state.currentProvider = null
          state.authorizationUrl = null
          state.state = null
          state.codeVerifier = null
          state.redirectUri = null
          state.scopes = []
          state.authStartedAt = null
          state.flowTimeout = null
        })
      },

      clearFlowData: () => {
        set((state) => {
          state.authorizationUrl = null
          state.state = null
          state.codeVerifier = null
          state.redirectUri = null
          state.scopes = []
          state.authenticationResult = null
          state.linkingResult = null
          state.flowInProgress = false
          state.authStartedAt = null
          state.flowTimeout = null
        })
      },

      setFlowTimeout: (timeout) => {
        set((state) => {
          state.flowTimeout = timeout
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
            state.isInitiating = false
            state.isAuthenticating = false
            state.isLinking = false
            state.isRefreshing = false
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      getProviderByName: (name) => {
        const { availableProviders } = get()
        return availableProviders.find(p => p.name === name) || null
      },

      isProviderAvailable: (name) => {
        const { availableProviders } = get()
        return availableProviders.some(p => p.name === name && p.configured)
      },

      hasValidState: (receivedState) => {
        const { state } = get()
        return state === receivedState
      },

      isFlowExpired: () => {
        const { flowTimeout } = get()
        if (!flowTimeout) return false
        return Date.now() > flowTimeout
      },

      getTimeRemaining: () => {
        const { flowTimeout } = get()
        if (!flowTimeout) return null
        const remaining = flowTimeout - Date.now()
        return remaining > 0 ? remaining : 0
      },

      canInitiateFlow: () => {
        const { flowInProgress, isInitiating, isAuthenticating, isLinking, isRefreshing } = get()
        return !flowInProgress && !isInitiating && !isAuthenticating && !isLinking && !isRefreshing
      },

      getProviderDisplayInfo: (provider) => {
        const providerInfo: Record<string, any> = {
          google: {
            displayName: 'Google',
            icon: '🇬',
            color: '#4285f4',
            description: 'Sign in with your Google account'
          },
          apple: {
            displayName: 'Apple',
            icon: '🍎',
            color: '#000000',
            description: 'Sign in with your Apple ID'
          }
        }

        return providerInfo[provider] || {
          displayName: provider,
          icon: '🔐',
          color: '#6b7280',
          description: `Sign in with ${provider}`
        }
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const oauth2Selectors = {
  // Core selectors
  availableProviders: (state: OAuth2StoreState) => state.availableProviders,
  providersLoaded: (state: OAuth2StoreState) => state.providersLoaded,
  currentProvider: (state: OAuth2StoreState) => state.currentProvider,
  authorizationUrl: (state: OAuth2StoreState) => state.authorizationUrl,
  flowInProgress: (state: OAuth2StoreState) => state.flowInProgress,
  isInitiating: (state: OAuth2StoreState) => state.isInitiating,
  isAuthenticating: (state: OAuth2StoreState) => state.isAuthenticating,
  isLinking: (state: OAuth2StoreState) => state.isLinking,
  isUnlinking: (state: OAuth2StoreState) => state.isUnlinking,
  isRefreshing: (state: OAuth2StoreState) => state.isRefreshing,
  authenticationResult: (state: OAuth2StoreState) => state.authenticationResult,
  linkingResult: (state: OAuth2StoreState) => state.linkingResult,
  isLoading: (state: OAuth2StoreState) => state.isLoading,
  error: (state: OAuth2StoreState) => state.error,

  // Computed selectors
  enabledProviders: (state: OAuth2StoreState) =>
    state.availableProviders.filter(p => p.configured),
  hasProviders: (state: OAuth2StoreState) =>
    state.availableProviders.length > 0,
  hasEnabledProviders: (state: OAuth2StoreState) =>
    state.availableProviders.some(p => p.configured),
  currentProviderInfo: (state: OAuth2StoreState) => {
    if (!state.currentProvider) return null
    return state.availableProviders.find(p => p.name === state.currentProvider) || null
  },
  hasAnyActivity: (state: OAuth2StoreState) =>
    state.isInitiating || state.isAuthenticating || state.isLinking ||
    !!state.isUnlinking || state.isRefreshing || state.isLoading,

  // Flow status selectors
  isFlowActive: (state: OAuth2StoreState) =>
    state.flowInProgress && !state.isFlowExpired(),
  canStartFlow: (state: OAuth2StoreState) =>
    !state.flowInProgress && !state.isInitiating && !state.isAuthenticating &&
    !state.isLinking && !state.isRefreshing,
  flowTimeRemaining: (state: OAuth2StoreState) => {
    if (!state.flowTimeout) return null
    const remaining = state.flowTimeout - Date.now()
    return remaining > 0 ? remaining : 0
  },

  // Provider-specific selectors
  googleProvider: (state: OAuth2StoreState) =>
    state.availableProviders.find(p => p.name === 'google'),
  appleProvider: (state: OAuth2StoreState) =>
    state.availableProviders.find(p => p.name === 'apple'),
  supportedProviders: (state: OAuth2StoreState) =>
    state.availableProviders.map(p => p.name),

  // Results selectors
  hasAuthenticationResult: (state: OAuth2StoreState) =>
    !!state.authenticationResult,
  hasLinkingResult: (state: OAuth2StoreState) =>
    !!state.linkingResult,
  isAuthenticationSuccessful: (state: OAuth2StoreState) =>
    state.authenticationResult?.success === true,
  isLinkingSuccessful: (state: OAuth2StoreState) =>
    state.linkingResult?.success === true,

  // State management selectors
  hasValidFlowState: (state: OAuth2StoreState) =>
    !!(state.state && state.codeVerifier && state.authorizationUrl),
  lastProviderUsed: (state: OAuth2StoreState) => state.lastProviderUsed,
  authStartedAt: (state: OAuth2StoreState) => state.authStartedAt
}

// ============================================================================
// Default Export
// ============================================================================

export default useOAuth2Store