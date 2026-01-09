/**
 * Authentication Services Index
 * Centralized export for all authentication-related services
 */

// ============================================================================
// Core Services
// ============================================================================
export { default as AuthService, TokenManager } from './auth'
export {
  default as MFAService,
  MFAChallengeService,
  MFAUtils
} from './mfa'
export {
  default as EmailService,
  EmailValidationUtils,
  EmailSecurityUtils
} from './email'
export {
  default as PhoneService,
  PhoneValidationUtils,
  PhoneSecurityUtils
} from './phone'
export {
  default as OAuth2Service,
  OAuth2StateManager,
  OAuth2Utils
} from './oauth2'
export {
  default as SessionsService,
  SessionUtils
} from './sessions'
export {
  default as WorkspaceService,
  WorkspacePermissions,
  WorkspaceContextManager
} from './workspace'

// ============================================================================
// API Infrastructure
// ============================================================================
export { apiClient, APIError } from '../api/client'
export {
  API_CONFIG,
  API_BASE,
  getBaseHeaders,
  getAuthHeaders,
  getEndpointURL,
  buildURL
} from '../api/config'

// ============================================================================
// Service Utilities (for hooks layer)
// ============================================================================

// Import services for internal use
import AuthService, { TokenManager } from './auth'
import EmailService from './email'
import MFAService from './mfa'
import SessionsService from './sessions'
import { OAuth2StateManager } from './oauth2'
import { APIError } from '../api/client'

export class ServiceManager {
  /**
   * Initialize services after successful login
   */
  static async initializeAfterLogin(token: string, expiresIn?: number): Promise<void> {
    // Set token in API client
    TokenManager.setAccessToken(token, expiresIn)

    // Note: Workspace initialization would be handled by workspace services
    // This service only handles core authentication
  }

  /**
   * Clean up services on logout
   */
  static cleanup(): void {
    TokenManager.clearAccessToken()
    OAuth2StateManager.clearState()
  }

  /**
   * Check if services are properly initialized
   */
  static isInitialized(): boolean {
    return !!TokenManager.getAccessToken()
  }

  /**
   * Get health status of all services
   */
  static async getServicesHealth(): Promise<{
    auth: boolean
    email: boolean
    mfa: boolean
    sessions: boolean
  }> {
    const health = {
      auth: false,
      email: false,
      mfa: false,
      sessions: false,
    }

    try {
      // Test auth service
      await AuthService.getCurrentUser()
      health.auth = true
    } catch {
      health.auth = false
    }

    try {
      // Test email service
      await EmailService.getVerificationStatus()
      health.email = true
    } catch {
      health.email = false
    }

    try {
      // Test MFA service
      await MFAService.getStatus()
      health.mfa = true
    } catch {
      health.mfa = false
    }

    try {
      // Test sessions service
      await SessionsService.getActiveSessions()
      health.sessions = true
    } catch {
      health.sessions = false
    }

    return health
  }
}

// ============================================================================
// Service Error Handler
// ============================================================================

export class ServiceErrorHandler {
  /**
   * Handle authentication errors consistently
   */
  static handleAuthError(error: unknown): {
    message: string
    code: string
    shouldLogout: boolean
  } {
    if (error instanceof APIError) {
      switch (error.status) {
        case 401:
          return {
            message: 'Your session has expired. Please login again.',
            code: 'SESSION_EXPIRED',
            shouldLogout: true,
          }
        case 403:
          return {
            message: 'You do not have permission to perform this action.',
            code: 'INSUFFICIENT_PERMISSIONS',
            shouldLogout: false,
          }
        case 429:
          return {
            message: 'Too many attempts. Please wait before trying again.',
            code: 'RATE_LIMITED',
            shouldLogout: false,
          }
        default:
          return {
            message: error.message || 'An unexpected error occurred.',
            code: 'API_ERROR',
            shouldLogout: false,
          }
      }
    }

    // Handle standard Error instances
    if (error instanceof Error) {
      return {
        message: error.message || 'An unexpected error occurred.',
        code: 'GENERAL_ERROR',
        shouldLogout: false,
      }
    }

    return {
      message: 'A network error occurred. Please check your connection.',
      code: 'NETWORK_ERROR',
      shouldLogout: false,
    }
  }

  /**
   * Handle MFA-specific errors
   */
  static handleMFAError(error: unknown): {
    message: string
    code: string
    canRetry: boolean
    attemptsRemaining?: number
  } {
    if (error instanceof APIError) {
      const details = error.details as any

      if (error.status === 400 && details?.code === 'INVALID_TOTP_CODE') {
        return {
          message: 'Invalid verification code. Please try again.',
          code: 'INVALID_CODE',
          canRetry: true,
          attemptsRemaining: details.attempts_remaining,
        }
      }

      if (error.status === 429 && details?.code === 'MFA_RATE_LIMITED') {
        return {
          message: 'Too many failed attempts. Please wait before trying again.',
          code: 'RATE_LIMITED',
          canRetry: false,
        }
      }
    }

    // Handle standard Error instances
    if (error instanceof Error) {
      return {
        message: error.message || 'MFA verification failed. Please try again.',
        code: 'MFA_ERROR',
        canRetry: true,
      }
    }

    return {
      message: 'MFA verification failed. Please try again.',
      code: 'MFA_ERROR',
      canRetry: true,
    }
  }
}

// ============================================================================
// Export Types (for hooks)
// ============================================================================

export type ServiceManagerType = typeof ServiceManager
export type ServiceErrorHandlerType = typeof ServiceErrorHandler