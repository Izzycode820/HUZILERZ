/**
 * API Error Handler - Centralized error handling and classification
 */

import { ERROR_MESSAGES, STATUS_CODE_MESSAGES } from '../config'

// ============================================================================
// Error Types
// ============================================================================

export class APIError extends Error {
  public readonly status: number
  public readonly code?: string
  public readonly details?: unknown
  public readonly endpoint?: string

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: unknown,
    endpoint?: string
  ) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.code = code
    this.details = details
    this.endpoint = endpoint
  }

  // Error type checks
  get isNetworkError(): boolean {
    return !this.status || this.status === 0
  }

  get isAuthError(): boolean {
    return this.status === 401 || this.status === 403
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500
  }

  get isServerError(): boolean {
    return this.status >= 500
  }

  get isRetryable(): boolean {
    return this.status === 408 || this.status === 429 || this.status >= 500
  }
}

// ============================================================================
// Error Factory Methods
// ============================================================================

export class ErrorFactory {
  /**
   * Create error from HTTP response
   */
  static fromResponse(response: Response, endpoint: string, details?: unknown): APIError {
    const message = STATUS_CODE_MESSAGES[response.status] || 'Unknown error occurred'
    return new APIError(message, response.status, undefined, details, endpoint)
  }

  /**
   * Create network error
   */
  static networkError(endpoint: string): APIError {
    return new APIError(ERROR_MESSAGES.NETWORK_ERROR, 0, 'NETWORK_ERROR', undefined, endpoint)
  }

  /**
   * Create timeout error
   */
  static timeoutError(endpoint: string): APIError {
    return new APIError(ERROR_MESSAGES.TIMEOUT_ERROR, 408, 'TIMEOUT_ERROR', undefined, endpoint)
  }

  /**
   * Create authentication error
   */
  static authError(message: string = ERROR_MESSAGES.UNAUTHORIZED): APIError {
    return new APIError(message, 401, 'AUTH_ERROR')
  }
}

// ============================================================================
// Error Handler Class
// ============================================================================

export class ErrorHandler {
  /**
   * Handle fetch errors and convert to APIError
   */
  static async handleResponse(response: Response, endpoint: string): Promise<unknown> {
    try {
      const contentType = response.headers.get('content-type')
      const isJson = contentType?.includes('application/json')

      let responseData: unknown
      if (isJson) {
        responseData = await response.json()
      } else {
        responseData = { message: await response.text() }
      }

      if (response.ok) {
        return responseData
      }

      // Check if this is a discriminated union error (has error_code field)
      // These errors should be thrown as-is so type guards can identify them
      if (
        responseData &&
        typeof responseData === 'object' &&
        'error_code' in responseData
      ) {
        // Throw discriminated union error directly
        // Components can use type guards (isPaidSubscriptionExistsError, etc.)
        throw responseData
      }

      throw ErrorFactory.fromResponse(response, endpoint, responseData)
    } catch (error) {
      if (error instanceof APIError) {
        throw error
      }
      // Re-throw discriminated union errors
      if (error && typeof error === 'object' && 'error_code' in error) {
        throw error
      }
      throw new APIError('Failed to process response', response.status)
    }
  }

  /**
   * Handle fetch/network errors
   */
  static handleNetworkError(error: Error, endpoint: string): APIError {
    if (error.name === 'AbortError') {
      return ErrorFactory.timeoutError(endpoint)
    }

    return ErrorFactory.networkError(endpoint)
  }

  /**
   * Should retry this error?
   */
  static shouldRetry(error: APIError, attempt: number, maxAttempts: number): boolean {
    if (attempt >= maxAttempts) return false
    if (!error.isRetryable) return false

    // Don't retry auth errors
    if (error.isAuthError) return false

    return true
  }

  /**
   * Get retry delay based on attempt
   */
  static getRetryDelay(attempt: number, baseDelay: number = 1000): number {
    return Math.min(baseDelay * Math.pow(2, attempt - 1), 10000)
  }
}

export default ErrorHandler