/**
 * OAuth2 Hook - 2024 Best Practices with Zustand
 * Custom hook layer for OAuth2 store - handles provider authentication flows
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { useOAuth2Store, oauth2Selectors } from '../../stores/authentication/oauth2Store'
import oauth2Service from '../../services/authentication/oauth2'
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
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseOAuth2Return {
  // State selectors (performance optimized)
  availableProviders: OAuth2Provider[]
  providersLoaded: boolean
  currentProvider: string | null
  authorizationUrl: string | null
  flowInProgress: boolean
  isInitiating: boolean
  isAuthenticating: boolean
  isLinking: boolean
  isUnlinking: string | null
  isRefreshing: boolean
  authenticationResult: OAuth2CallbackResponse | null
  linkingResult: unknown | null
  isLoading: boolean
  error: string | null

  // Computed state
  enabledProviders: OAuth2Provider[]
  hasProviders: boolean
  hasEnabledProviders: boolean
  currentProviderInfo: OAuth2Provider | null
  hasAnyActivity: boolean
  isFlowActive: boolean
  canStartFlow: boolean
  flowTimeRemaining: number | null
  hasAuthenticationResult: boolean
  hasLinkingResult: boolean
  isAuthenticationSuccessful: boolean
  isLinkingSuccessful: boolean

  // Actions (stable references)
  loadProviders: () => Promise<OAuth2Provider[]>
  initiateFlow: (request: OAuth2InitiateRequest) => Promise<OAuth2InitiateResponse>
  handleCallback: (request: OAuth2CallbackRequest) => Promise<OAuth2CallbackResponse>
  linkAccount: (request: OAuth2InitiateRequest) => Promise<OAuth2InitiateResponse>
  unlinkAccount: (provider: string) => Promise<unknown>
  refreshTokens: (request: OAuth2TokenRefreshRequest) => Promise<OAuth2TokenRefreshResponse>
  cancelFlow: () => void
  clearError: () => void
  clearResults: () => void

  // Helper methods
  getProviderByName: (name: string) => OAuth2Provider | null
  isProviderAvailable: (name: string) => boolean
  hasValidState: (receivedState: string) => boolean
  isFlowExpired: () => boolean
  getTimeRemaining: () => number | null
  canInitiateFlow: () => boolean
  getProviderDisplayInfo: (provider: string) => unknown
}

// ============================================================================
// Main OAuth2 Hook
// ============================================================================

export function useOAuth2(): UseOAuth2Return {
  // Selective store subscriptions (performance optimized)
  const availableProviders = useOAuth2Store(oauth2Selectors.availableProviders)
  const providersLoaded = useOAuth2Store(oauth2Selectors.providersLoaded)
  const currentProvider = useOAuth2Store(oauth2Selectors.currentProvider)
  const authorizationUrl = useOAuth2Store(oauth2Selectors.authorizationUrl)
  const flowInProgress = useOAuth2Store(oauth2Selectors.flowInProgress)
  const isInitiating = useOAuth2Store(oauth2Selectors.isInitiating)
  const isAuthenticating = useOAuth2Store(oauth2Selectors.isAuthenticating)
  const isLinking = useOAuth2Store(oauth2Selectors.isLinking)
  const isUnlinking = useOAuth2Store(oauth2Selectors.isUnlinking)
  const isRefreshing = useOAuth2Store(oauth2Selectors.isRefreshing)
  const authenticationResult = useOAuth2Store(oauth2Selectors.authenticationResult)
  const linkingResult = useOAuth2Store(oauth2Selectors.linkingResult)
  const isLoading = useOAuth2Store(oauth2Selectors.isLoading)
  const error = useOAuth2Store(oauth2Selectors.error)
  const enabledProviders = useOAuth2Store(oauth2Selectors.enabledProviders)
  const hasProviders = useOAuth2Store(oauth2Selectors.hasProviders)
  const hasEnabledProviders = useOAuth2Store(oauth2Selectors.hasEnabledProviders)
  const currentProviderInfo = useOAuth2Store(oauth2Selectors.currentProviderInfo)
  const hasAnyActivity = useOAuth2Store(oauth2Selectors.hasAnyActivity)
  const isFlowActive = useOAuth2Store(oauth2Selectors.isFlowActive)
  const canStartFlow = useOAuth2Store(oauth2Selectors.canStartFlow)
  const flowTimeRemaining = useOAuth2Store(oauth2Selectors.flowTimeRemaining)
  const hasAuthenticationResult = useOAuth2Store(oauth2Selectors.hasAuthenticationResult)
  const hasLinkingResult = useOAuth2Store(oauth2Selectors.hasLinkingResult)
  const isAuthenticationSuccessful = useOAuth2Store(oauth2Selectors.isAuthenticationSuccessful)
  const isLinkingSuccessful = useOAuth2Store(oauth2Selectors.isLinkingSuccessful)

  // Store actions (direct references for performance)
  const setAvailableProviders = useOAuth2Store(state => state.setAvailableProviders)
  const setCurrentProvider = useOAuth2Store(state => state.setCurrentProvider)
  const setAuthorizationFlow = useOAuth2Store(state => state.setAuthorizationFlow)
  const setIsInitiating = useOAuth2Store(state => state.setIsInitiating)
  const setIsAuthenticating = useOAuth2Store(state => state.setIsAuthenticating)
  const setIsLinking = useOAuth2Store(state => state.setIsLinking)
  const setIsUnlinking = useOAuth2Store(state => state.setIsUnlinking)
  const setIsRefreshing = useOAuth2Store(state => state.setIsRefreshing)
  const setAuthenticationResult = useOAuth2Store(state => state.setAuthenticationResult)
  const setLinkingResult = useOAuth2Store(state => state.setLinkingResult)
  const setLoading = useOAuth2Store(state => state.setLoading)
  const setError = useOAuth2Store(state => state.setError)
  const clearError = useOAuth2Store(state => state.clearError)
  const startFlow = useOAuth2Store(state => state.startFlow)
  const completeFlow = useOAuth2Store(state => state.completeFlow)
  const cancelFlow = useOAuth2Store(state => state.cancelFlow)
  const clearFlowData = useOAuth2Store(state => state.clearFlowData)
  const getProviderByName = useOAuth2Store(state => state.getProviderByName)
  const isProviderAvailable = useOAuth2Store(state => state.isProviderAvailable)
  const hasValidState = useOAuth2Store(state => state.hasValidState)
  const isFlowExpired = useOAuth2Store(state => state.isFlowExpired)
  const getTimeRemaining = useOAuth2Store(state => state.getTimeRemaining)
  const canInitiateFlow = useOAuth2Store(state => state.canInitiateFlow)
  const getProviderDisplayInfo = useOAuth2Store(state => state.getProviderDisplayInfo)

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const loadProviders = useCallback(async (): Promise<OAuth2Provider[]> => {
    try {
      setLoading(true)
      setError(null)

      const providers = await oauth2Service.getProviders()
      setAvailableProviders(providers)
      return providers
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load OAuth2 providers'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setAvailableProviders])

  const initiateFlow = useCallback(async (request: OAuth2InitiateRequest): Promise<OAuth2InitiateResponse> => {
    try {
      setIsInitiating(true)
      setError(null)

      // Check if provider is available
      if (!isProviderAvailable(request.provider)) {
        throw new Error(`Provider ${request.provider} is not available`)
      }

      // Start flow tracking
      startFlow(request.provider)

      const response = await oauth2Service.initiate(request)

      if (response) {
        setAuthorizationFlow({
          authorizationUrl: response.authorization_url,
          state: response.state,
          codeVerifier: '',
          redirectUri: '',
          scopes: []
        })

        return {
          success: true,
          data: {
            authorization_url: response.authorization_url,
            state: response.state,
            provider: response.provider,
            expires_in: response.expires_in
          }
        } as OAuth2InitiateResponse
      }

      throw new Error('OAuth2 flow initiation failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'OAuth2 flow initiation failed'
      setError(errorMessage)
      cancelFlow()
      throw error
    } finally {
      setIsInitiating(false)
    }
  }, [setIsInitiating, setError, isProviderAvailable, startFlow, setAuthorizationFlow, cancelFlow])

  const handleCallback = useCallback(async (request: OAuth2CallbackRequest): Promise<OAuth2CallbackResponse> => {
    try {
      setIsAuthenticating(true)
      setError(null)

      // Validate state parameter
      if (request.state && !hasValidState(request.state)) {
        throw new Error('Invalid OAuth2 state parameter')
      }

      // Check if flow has expired
      if (isFlowExpired()) {
        throw new Error('OAuth2 flow has expired')
      }

      const response = await oauth2Service.handleCallback(request)

      if (response.success) {
        completeFlow(response)
        return response
      }

      throw new Error(response.message || 'OAuth2 callback handling failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'OAuth2 callback handling failed'
      setError(errorMessage)
      cancelFlow()
      throw error
    } finally {
      setIsAuthenticating(false)
    }
  }, [setIsAuthenticating, setError, hasValidState, isFlowExpired, completeFlow, cancelFlow])

  const linkAccount = useCallback(async (request: OAuth2InitiateRequest): Promise<OAuth2InitiateResponse> => {
    try {
      setIsLinking(true)
      setError(null)

      // Check if provider is available
      if (!isProviderAvailable(request.provider)) {
        throw new Error(`Provider ${request.provider} is not available for linking`)
      }

      // Start flow tracking
      startFlow(request.provider)

      const response = await oauth2Service.linkAccount({
        provider: request.provider,
        code: '',
        state: request.state || ''
      })

      if (response.success) {
        return {
          success: true,
          authorization_url: '',
          state: '',
          code_verifier: '',
          redirect_uri: '',
          scopes: []
        } as OAuth2InitiateResponse
      }

      throw new Error(response.message || 'Account linking failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Account linking failed'
      setError(errorMessage)
      cancelFlow()
      throw error
    } finally {
      setIsLinking(false)
    }
  }, [setIsLinking, setError, isProviderAvailable, startFlow, cancelFlow])

  const unlinkAccount = useCallback(async (provider: string): Promise<unknown> => {
    try {
      setIsUnlinking(provider)
      setError(null)

      const response = await oauth2Service.unlinkAccount(provider)

      if (response.success) {
        // Refresh providers list to update linked status
        await loadProviders()
        return response
      }

      throw new Error(response.message || 'Account unlinking failed')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Account unlinking failed'
      setError(errorMessage)
      throw error
    } finally {
      setIsUnlinking(null)
    }
  }, [setIsUnlinking, setError, loadProviders])

  const refreshTokens = useCallback(async (request: OAuth2TokenRefreshRequest): Promise<OAuth2TokenRefreshResponse> => {
    try {
      setIsRefreshing(true)
      setError(null)

      const response = await oauth2Service.refreshToken(request)

      return response
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Token refresh failed'
      setError(errorMessage)
      throw error
    } finally {
      setIsRefreshing(false)
    }
  }, [setIsRefreshing, setError])

  const clearResults = useCallback(() => {
    setAuthenticationResult(null)
    setLinkingResult(null)
    clearFlowData()
  }, [setAuthenticationResult, setLinkingResult, clearFlowData])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    availableProviders,
    providersLoaded,
    currentProvider,
    authorizationUrl,
    flowInProgress,
    isInitiating,
    isAuthenticating,
    isLinking,
    isUnlinking,
    isRefreshing,
    authenticationResult,
    linkingResult,
    isLoading,
    error,

    // Computed state
    enabledProviders,
    hasProviders,
    hasEnabledProviders,
    currentProviderInfo,
    hasAnyActivity,
    isFlowActive,
    canStartFlow,
    flowTimeRemaining,
    hasAuthenticationResult,
    hasLinkingResult,
    isAuthenticationSuccessful,
    isLinkingSuccessful,

    // Actions (stable)
    loadProviders,
    initiateFlow,
    handleCallback,
    linkAccount,
    unlinkAccount,
    refreshTokens,
    cancelFlow,
    clearError,
    clearResults,

    // Helper methods
    getProviderByName,
    isProviderAvailable,
    hasValidState,
    isFlowExpired,
    getTimeRemaining,
    canInitiateFlow,
    getProviderDisplayInfo
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for provider management only - minimal re-renders
 */
export function useOAuth2Providers() {
  return {
    availableProviders: useOAuth2Store(oauth2Selectors.availableProviders),
    providersLoaded: useOAuth2Store(oauth2Selectors.providersLoaded),
    enabledProviders: useOAuth2Store(oauth2Selectors.enabledProviders),
    hasProviders: useOAuth2Store(oauth2Selectors.hasProviders),
    hasEnabledProviders: useOAuth2Store(oauth2Selectors.hasEnabledProviders)
  }
}

/**
 * Hook for flow management only - minimal re-renders
 */
export function useOAuth2Flow() {
  return {
    currentProvider: useOAuth2Store(oauth2Selectors.currentProvider),
    flowInProgress: useOAuth2Store(oauth2Selectors.flowInProgress),
    isFlowActive: useOAuth2Store(oauth2Selectors.isFlowActive),
    canStartFlow: useOAuth2Store(oauth2Selectors.canStartFlow),
    flowTimeRemaining: useOAuth2Store(oauth2Selectors.flowTimeRemaining),
    authorizationUrl: useOAuth2Store(oauth2Selectors.authorizationUrl)
  }
}

/**
 * Hook for authentication status only - minimal re-renders
 */
export function useOAuth2Status() {
  return {
    isInitiating: useOAuth2Store(oauth2Selectors.isInitiating),
    isAuthenticating: useOAuth2Store(oauth2Selectors.isAuthenticating),
    isLinking: useOAuth2Store(oauth2Selectors.isLinking),
    isUnlinking: useOAuth2Store(oauth2Selectors.isUnlinking),
    isRefreshing: useOAuth2Store(oauth2Selectors.isRefreshing),
    hasAnyActivity: useOAuth2Store(oauth2Selectors.hasAnyActivity),
    isLoading: useOAuth2Store(oauth2Selectors.isLoading),
    error: useOAuth2Store(oauth2Selectors.error)
  }
}

// ============================================================================
// Default Export
// ============================================================================

export default useOAuth2