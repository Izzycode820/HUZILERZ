/**
 * Base HTTP Client - Core HTTP functionality for all services
 */

import TokenManager from './TokenManager'
import { ErrorHandler, APIError, ErrorFactory } from './ErrorHandler'
import { API_CONFIG, getBaseHeaders, getAuthHeaders, getRequestConfig } from '../config'

// ============================================================================
// Types
// ============================================================================

export interface RequestOptions extends Omit<RequestInit, 'headers'> {
  headers?: HeadersInit
  timeout?: number
  retryAttempts?: number
  requireAuth?: boolean
  skipAuth?: boolean
}

export interface APIResponse<T = unknown> {
  data: T
  status: number
  success: boolean
}

// ============================================================================
// Base Client Class
// ============================================================================

export class BaseClient {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private requestCache = new Map<string, Promise<any>>()

  /**
   * Make HTTP request with retry logic
   */
  async request<T = unknown>(
    url: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      requireAuth = false,
      skipAuth = false,
      timeout = API_CONFIG.timeout,
      retryAttempts = API_CONFIG.retryAttempts,
      headers = {},
      ...requestOptions
    } = options

    // Check for cached request (GET requests only)
    const cacheKey = this.getCacheKey(url, requestOptions)
    if (requestOptions.method === 'GET' && this.requestCache.has(cacheKey)) {
      return this.requestCache.get(cacheKey)!
    }

    const requestPromise = this.executeRequest<T>(
      url,
      {
        ...requestOptions,
        headers: this.buildHeaders(headers, requireAuth, skipAuth),
      },
      timeout,
      retryAttempts
    )

    // Cache GET requests
    if (requestOptions.method === 'GET') {
      this.requestCache.set(cacheKey, requestPromise)
      requestPromise.finally(() => this.requestCache.delete(cacheKey))
    }

    return requestPromise
  }

  /**
   * Execute request with retry and timeout
   */
  private async executeRequest<T>(
    url: string,
    options: RequestInit,
    timeout: number,
    maxRetries: number,
    attempt: number = 1
  ): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(url, {
        ...getRequestConfig(),
        ...options,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      // Handle 401 with token refresh
      if (response.status === 401 && !url.includes('/refresh/')) {
        const refreshed = await this.attemptTokenRefresh()
        if (refreshed) {
          // Retry with new token
          const newHeaders = this.buildHeaders(options.headers as HeadersInit, true, false)
          return this.executeRequest<T>(
            url,
            { ...options, headers: newHeaders },
            timeout,
            maxRetries,
            attempt
          )
        }
      }

      const data = await ErrorHandler.handleResponse(response, url)
      return data as T
    } catch (error) {
      clearTimeout(timeoutId)

      let apiError: APIError
      if (error instanceof APIError) {
        apiError = error
      } else if (error instanceof Error) {
        apiError = ErrorHandler.handleNetworkError(error, url)
      } else {
        apiError = ErrorFactory.networkError(url)
      }

      // Retry logic
      if (ErrorHandler.shouldRetry(apiError, attempt, maxRetries)) {
        const delay = ErrorHandler.getRetryDelay(attempt, API_CONFIG.retryDelay)
        await new Promise(resolve => setTimeout(resolve, delay))
        return this.executeRequest<T>(url, options, timeout, maxRetries, attempt + 1)
      }

      throw apiError
    }
  }

  /**
   * Attempt token refresh
   */
  private async attemptTokenRefresh(): Promise<boolean> {
    try {
      const refreshUrl = `${API_CONFIG.baseURL}/api/auth/refresh/`
      const response = await fetch(refreshUrl, {
        method: 'POST',
        ...getRequestConfig(),
        headers: getBaseHeaders(),
      })

      if (response.ok) {
        const data = await response.json()
        if (data.access_token) {
          TokenManager.setToken(data.access_token, data.expires_in)
          return true
        }
      }
    } catch (error) {
      console.warn('Token refresh failed:', error)
    }

    return false
  }

  /**
   * Build request headers
   */
  private buildHeaders(
    customHeaders: HeadersInit = {},
    requireAuth: boolean,
    skipAuth: boolean
  ): HeadersInit {
    if (skipAuth) {
      return { ...getBaseHeaders(), ...customHeaders }
    }

    const token = requireAuth ? TokenManager.getToken() : null
    return { ...getAuthHeaders(token || undefined), ...customHeaders }
  }

  /**
   * Generate cache key for request
   */
  private getCacheKey(url: string, options: RequestInit): string {
    return `${url}:${JSON.stringify(options)}`
  }

  /**
   * Convenience methods
   */
  async get<T = unknown>(url: string, options: Omit<RequestOptions, 'method'> = {}): Promise<T> {
    return this.request<T>(url, { ...options, method: 'GET' })
  }

  async post<T = unknown>(url: string, data?: unknown, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T = unknown>(url: string, data?: unknown, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async patch<T = unknown>(url: string, data?: unknown, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<T> {
    return this.request<T>(url, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T = unknown>(url: string, options: Omit<RequestOptions, 'method'> = {}): Promise<T> {
    return this.request<T>(url, { ...options, method: 'DELETE' })
  }
}

export default BaseClient