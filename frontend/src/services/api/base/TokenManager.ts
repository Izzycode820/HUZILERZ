/**
 * Token Manager - Secure token storage and management
 * Handles access tokens with expiry validation
 */

// ============================================================================
// Types
// ============================================================================

export interface TokenData {
  token: string
  expiresAt?: number
}

// ============================================================================
// Token Manager Class
// ============================================================================

export class TokenManager {
  private static instance: TokenManager
  private accessToken: string | null = null
  private tokenExpiry: number | null = null

  private constructor() {}

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager()
    }
    return TokenManager.instance
  }

  /**
   * Set access token with expiration
   */
  setToken(token: string, expiresIn?: number): void {
    this.accessToken = token
    this.tokenExpiry = expiresIn ? Date.now() + (expiresIn * 1000) : null
  }

  /**
   * Get current access token (validates expiry)
   */
  getToken(): string | null {
    if (this.isExpired()) {
      this.clearToken()
      return null
    }
    return this.accessToken
  }

  /**
   * Clear stored token
   */
  clearToken(): void {
    this.accessToken = null
    this.tokenExpiry = null
  }

  /**
   * Check if current token is expired
   */
  isExpired(): boolean {
    if (!this.tokenExpiry || !this.accessToken) return false
    return Date.now() >= this.tokenExpiry
  }

  /**
   * Get time until token expiry (in milliseconds)
   */
  getTimeUntilExpiry(): number {
    if (!this.tokenExpiry) return 0
    return Math.max(0, this.tokenExpiry - Date.now())
  }

  /**
   * Check if token exists (regardless of expiry)
   */
  hasToken(): boolean {
    return !!this.accessToken
  }
}

export default TokenManager.getInstance()