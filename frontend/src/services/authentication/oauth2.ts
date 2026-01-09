/**
 * OAuth2 Service - Enterprise OAuth2 Authentication
 * Aligned with backend oauth2_views.py endpoints (Google, Apple)
 */

import BaseService from '../base/BaseService'
import { apiClient } from '../api/client'
import type {
  OAuth2Provider,
  OAuth2ProvidersResponse,
  OAuth2InitiateRequest,
  OAuth2InitiateResponse,
  OAuth2CallbackRequest,
  OAuth2CallbackResponse,
  OAuth2TokenRefreshRequest,
  OAuth2TokenRefreshResponse
} from '../../types/authentication/oauth2'

// ============================================================================
// OAuth2 Service (Matches Backend endpoints exactly)
// ============================================================================

export class OAuth2Service extends BaseService {
  constructor() {
    super('auth')
  }

  /**
   * Get available OAuth2 providers
   * Backend: GET /api/auth/oauth2/providers/
   */
  async getProviders(): Promise<OAuth2Provider[]> {
    const response = await this.getPublic<OAuth2ProvidersResponse>('/oauth2/providers/')
    return response.providers || []
  }

  /**
   * Initiate OAuth2 authentication flow
   * Backend: POST /api/auth/oauth2/initiate/
   */
  async initiate(data: OAuth2InitiateRequest): Promise<OAuth2InitiateResponse['data']> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['provider'])

    const cleanedData = this.cleanData({
      provider: data.provider,
      redirect_uri: data.redirect_uri,
      state: data.state,
      scopes: data.scopes
    } as Record<string, unknown>)

    const response = await this.postPublic<OAuth2InitiateResponse>('/oauth2/initiate/', cleanedData)

    if (!response.success || !response.data) {
      throw new Error('Failed to initiate OAuth2 flow')
    }

    return response.data
  }

  /**
   * Handle OAuth2 callback and complete authentication
   * Backend: POST /api/auth/oauth2/callback/
   */
  async handleCallback(data: OAuth2CallbackRequest): Promise<OAuth2CallbackResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['state'])

    // Either code or error must be present
    if (!data.code && !data.error) {
      throw new Error('Either authorization code or error must be provided')
    }

    // Handle OAuth2 errors
    if (data.error) {
      throw new Error(this.getOAuth2ErrorMessage(data.error, data.error_description))
    }

    const cleanedData = this.cleanData({
      provider: data.provider,
      code: data.code,
      state: data.state
    } as Record<string, unknown>)

    const response = await this.postPublic<OAuth2CallbackResponse>('/oauth2/callback/', cleanedData)

    if (!response.success) {
      throw new Error(response.message || 'OAuth2 authentication failed')
    }

    // Store token after successful authentication
    if (response.access_token) {
      apiClient.setAuthToken(response.access_token, response.expires_in)
    }

    return response
  }

  /**
   * Refresh OAuth2 token
   * Backend: POST /api/auth/oauth2/refresh/
   */
  async refreshToken(data: OAuth2TokenRefreshRequest): Promise<OAuth2TokenRefreshResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['provider', 'refresh_token'])

    const cleanedData = this.cleanData({
      provider: data.provider,
      refresh_token: data.refresh_token
    } as Record<string, unknown>)

    return this.postPublic<OAuth2TokenRefreshResponse>('/oauth2/refresh/', cleanedData)
  }

  /**
   * Link OAuth2 account to existing user
   * Backend: POST /api/auth/oauth2/link/
   */
  async linkAccount(data: OAuth2CallbackRequest): Promise<{
    success: boolean
    message: string
    linked_provider: string
  }> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['state'])

    if (!data.code && !data.error) {
      throw new Error('Either authorization code or error must be provided')
    }

    if (data.error) {
      throw new Error(this.getOAuth2ErrorMessage(data.error, data.error_description))
    }

    const cleanedData = this.cleanData({
      provider: data.provider,
      code: data.code,
      state: data.state
    } as Record<string, unknown>)

    return this.post('/oauth2/link/', cleanedData)
  }

  /**
   * Unlink OAuth2 account
   * Backend: DELETE /api/auth/oauth2/unlink/{provider}/
   */
  async unlinkAccount(provider: string): Promise<{
    success: boolean
    message: string
  }> {
    this.validateRequired({ provider }, ['provider'])
    return this.delete(`/oauth2/unlink/${provider}/`)
  }

  // ============================================================================
  // Private Helper Methods
  // ============================================================================

  /**
   * Validate redirect URI format and security
   */
  private validateRedirectURI(redirectUri: string): void {
    try {
      const url = new URL(redirectUri)

      // Must be HTTPS in production or localhost for development
      if (!url.protocol.startsWith('https:') &&
        !url.hostname.includes('localhost') &&
        !url.hostname.includes('127.0.0.1')) {
        throw new Error('Redirect URI must use HTTPS or be localhost')
      }

      // Check length
      if (redirectUri.length > 2000) {
        throw new Error('Redirect URI is too long')
      }

    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error('Invalid redirect URI format')
      }
      throw error
    }
  }

  /**
   * Get user-friendly error message for OAuth2 errors
   */
  private getOAuth2ErrorMessage(error: string, description?: string): string {
    const errorMessages: Record<string, string> = {
      'access_denied': 'Authentication was cancelled by the user',
      'invalid_request': 'Invalid authentication request',
      'unsupported_response_type': 'Authentication method not supported',
      'invalid_scope': 'Invalid permissions requested',
      'server_error': 'Authentication server error. Please try again.',
      'temporarily_unavailable': 'Authentication service temporarily unavailable',
      'user_cancelled_authorize': 'Authentication was cancelled',
      'invalid_client': 'Invalid application configuration'
    }

    const message = errorMessages[error] || 'OAuth2 authentication failed'
    return description ? `${message}: ${description}` : message
  }
}

// ============================================================================
// OAuth2 State Management
// ============================================================================

export class OAuth2StateManager {
  private static readonly STATE_KEY = 'oauth2_state'
  private static readonly CODE_VERIFIER_KEY = 'oauth2_code_verifier'

  /**
   * Store OAuth2 state and PKCE verifier
   */
  static storeState(state: string, codeVerifier: string, provider: string): void {
    const stateData = {
      state,
      codeVerifier,
      provider,
      timestamp: Date.now()
    }

    try {
      sessionStorage.setItem(this.STATE_KEY, JSON.stringify(stateData))
    } catch (error) {
      console.warn('Failed to store OAuth2 state:', error)
    }
  }

  /**
   * Retrieve and validate OAuth2 state
   */
  static retrieveAndValidateState(receivedState: string): {
    isValid: boolean
    codeVerifier?: string
    provider?: string
  } {
    try {
      const stored = sessionStorage.getItem(this.STATE_KEY)
      if (!stored) {
        return { isValid: false }
      }

      const stateData = JSON.parse(stored)

      // Check state match
      if (stateData.state !== receivedState) {
        return { isValid: false }
      }

      // Check if not expired (5 minutes)
      const fiveMinutesAgo = Date.now() - (5 * 60 * 1000)
      if (stateData.timestamp < fiveMinutesAgo) {
        this.clearState()
        return { isValid: false }
      }

      return {
        isValid: true,
        codeVerifier: stateData.codeVerifier,
        provider: stateData.provider
      }

    } catch (error) {
      console.warn('Failed to validate OAuth2 state:', error)
      return { isValid: false }
    }
  }

  /**
   * Clear stored OAuth2 state
   */
  static clearState(): void {
    try {
      sessionStorage.removeItem(this.STATE_KEY)
    } catch (error) {
      console.warn('Failed to clear OAuth2 state:', error)
    }
  }
}

// ============================================================================
// OAuth2 Utilities
// ============================================================================

export class OAuth2Utils {
  /**
   * Generate secure random state parameter
   */
  static generateState(): string {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  /**
   * Extract error from OAuth2 callback URL
   */
  static extractCallbackData(url: string): OAuth2CallbackRequest {
    const urlObj = new URL(url)
    const params = urlObj.searchParams

    return {
      provider: params.get('provider') || '',
      code: params.get('code') || '',
      state: params.get('state') || '',
      error: params.get('error') || undefined,
      error_description: params.get('error_description') || undefined
    }
  }

  /**
   * Check if current URL is OAuth2 callback
   */
  static isOAuth2Callback(url: string = window.location.href): boolean {
    const urlObj = new URL(url)
    return urlObj.searchParams.has('state') &&
      (urlObj.searchParams.has('code') || urlObj.searchParams.has('error'))
  }

  /**
   * Get provider display information
   */
  static getProviderDisplayInfo(provider: string): {
    displayName: string
    icon: string
    color: string
    description: string
  } {
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

  /**
   * Validate OAuth2 redirect URI
   */
  static validateRedirectURI(uri: string): boolean {
    try {
      const url = new URL(uri)
      return url.protocol === 'https:' ||
        url.hostname === 'localhost' ||
        url.hostname === '127.0.0.1'
    } catch {
      return false
    }
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const oauth2Service = new OAuth2Service()
export default oauth2Service