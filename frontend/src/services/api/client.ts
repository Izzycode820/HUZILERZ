/**
 * Main API Client - Enterprise-grade client with base inheritance
 */

import BaseClient from './base/BaseClient'
import TokenManager from './base/TokenManager'
import { APIError } from './base/ErrorHandler'
import { getEndpointURL, API_BASE } from './config'

// ============================================================================
// Request Options (simplified)
// ============================================================================

export interface RequestOptions {
  method?: string
  body?: string
  requireAuth?: boolean
  skipAuth?: boolean
  timeout?: number
  retryAttempts?: number
}

// ============================================================================
// Main API Client Class
// ============================================================================

export class APIClient extends BaseClient {
  private static instance: APIClient

  static getInstance(): APIClient {
    if (!APIClient.instance) {
      APIClient.instance = new APIClient()
    }
    return APIClient.instance
  }

  /**
   * Set authentication token
   */
  setAuthToken(token: string, expiresIn?: number): void {
    TokenManager.setToken(token, expiresIn)
  }

  /**
   * Clear authentication token
   */
  clearAuthToken(): void {
    TokenManager.clearToken()
  }

  /**
   * Get current auth token
   */
  getAuthToken(): string | null {
    return TokenManager.getToken()
  }

  /**
   * Make request to specific endpoint
   * @template T - The expected response type (defaults to unknown for type safety)
   */
  async requestEndpoint<T = unknown>(
    baseKey: keyof typeof API_BASE,
    path: string = '',
    options: RequestOptions = {}
  ): Promise<T> {
    const url = getEndpointURL(baseKey, path)
    return this.request<T>(url, options)
  }

  /**
   * Endpoint-specific convenience methods
   */
  async getEndpoint<T = unknown>(
    baseKey: keyof typeof API_BASE,
    path: string = '',
    options: RequestOptions = {}
  ): Promise<T> {
    return this.requestEndpoint<T>(baseKey, path, { ...options, method: 'GET' })
  }

  async postEndpoint<T = unknown>(
    baseKey: keyof typeof API_BASE,
    path: string = '',
    data?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.requestEndpoint<T>(baseKey, path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async putEndpoint<T = unknown>(
    baseKey: keyof typeof API_BASE,
    path: string = '',
    data?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.requestEndpoint<T>(baseKey, path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async patchEndpoint<T = unknown>(
    baseKey: keyof typeof API_BASE,
    path: string = '',
    data?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {
    return this.requestEndpoint<T>(baseKey, path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async deleteEndpoint<T = unknown>(
    baseKey: keyof typeof API_BASE,
    path: string = '',
    options: RequestOptions = {}
  ): Promise<T> {
    return this.requestEndpoint<T>(baseKey, path, { ...options, method: 'DELETE' })
  }
}

// ============================================================================
// Export Singleton Instance
// ============================================================================

export const apiClient = APIClient.getInstance()
export { APIError, TokenManager }
export default apiClient