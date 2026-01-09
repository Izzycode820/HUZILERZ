/**
 * Base Service Class - Foundation for all service implementations
 */

import { apiClient } from '../api/client'
import { API_BASE } from '../api/config'

// ============================================================================
// Base Service Class
// ============================================================================

export abstract class BaseService {
  protected readonly baseKey: keyof typeof API_BASE

  constructor(baseKey: keyof typeof API_BASE) {
    this.baseKey = baseKey
  }

  /**
   * Make GET request to service endpoint
   */
  protected async get<T>(path: string = '', options: Record<string, unknown> = {}): Promise<T> {
    return apiClient.getEndpoint<T>(this.baseKey, path, {
      requireAuth: true,
      ...options,
    })
  }

  /**
   * Make POST request to service endpoint
   */
  protected async post<T>(path: string = '', data?: unknown, options: Record<string, unknown> = {}): Promise<T> {
    return apiClient.postEndpoint<T>(this.baseKey, path, data, {
      requireAuth: true,
      ...options,
    })
  }

  /**
   * Make PUT request to service endpoint
   */
  protected async put<T>(path: string = '', data?: unknown, options: Record<string, unknown> = {}): Promise<T> {
    return apiClient.putEndpoint<T>(this.baseKey, path, data, {
      requireAuth: true,
      ...options,
    })
  }

  /**
   * Make PATCH request to service endpoint
   */
  protected async patch<T>(path: string = '', data?: unknown, options: Record<string, unknown> = {}): Promise<T> {
    return apiClient.patchEndpoint<T>(this.baseKey, path, data, {
      requireAuth: true,
      ...options,
    })
  }

  /**
   * Make DELETE request to service endpoint
   */
  protected async delete<T>(path: string = '', options: Record<string, unknown> = {}): Promise<T> {
    return apiClient.deleteEndpoint<T>(this.baseKey, path, {
      requireAuth: true,
      ...options,
    })
  }

  /**
   * Make public request (no auth required)
   */
  protected async getPublic<T>(path: string = '', options: Record<string, unknown> = {}): Promise<T> {
    return apiClient.getEndpoint<T>(this.baseKey, path, {
      skipAuth: true,
      ...options,
    })
  }

  /**
   * Make public POST request (no auth required)
   */
  protected async postPublic<T>(path: string = '', data?: unknown, options: Record<string, unknown> = {}): Promise<T> {
    return apiClient.postEndpoint<T>(this.baseKey, path, data, {
      skipAuth: true,
      ...options,
    })
  }

  /**
   * Build query string from parameters
   */
  protected buildQuery(params: Record<string, unknown>): string {
    const searchParams = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.set(key, String(value))
      }
    })

    const query = searchParams.toString()
    return query ? `?${query}` : ''
  }

  /**
   * Handle paginated responses
   */
  protected async getPaginated<T>(
    path: string,
    params: {
      limit?: number
      offset?: number
      [key: string]: unknown
    } = {}
  ): Promise<{
    results: T[]
    count: number
    next: string | null
    previous: string | null
  }> {
    const query = this.buildQuery(params)
    return this.get<{
      results: T[]
      count: number
      next: string | null
      previous: string | null
    }>(`${path}${query}`)
  }

  /**
   * Validate required fields
   */
  protected validateRequired(data: Record<string, unknown>, fields: string[]): void {
    const missing = fields.filter(field => !data[field])
    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`)
    }
  }

  /**
   * Clean undefined values from object
   */
  protected cleanData(data: Record<string, unknown>): Record<string, unknown> {
    return Object.fromEntries(
      Object.entries(data).filter(([_, value]) => value !== undefined)
    )
  }
}

export default BaseService