/**
 * Centralized API Configuration
 * Single source of truth for all API settings, base URLs, headers, and timeouts
 */

// ============================================================================
// Environment Configuration
// ============================================================================

export interface APIConfig {
  baseURL: string
  timeout: number
  retryAttempts: number
  retryDelay: number
  enableLogging: boolean
}

export interface APIBase {
  auth: string
  workspaces: string
  security: string
  subscriptions: string  // For subscription management and pricing (plural)
  payments: string  // For payment operations (retry, refund, etc.)
  users: string
  store: string  // For store management endpoints
  themes: string  // For theme management endpoints
}

// ============================================================================
// Environment-based Configuration
// ============================================================================

const getEnvironmentConfig = (): APIConfig => {
  const env = process.env.NODE_ENV
  const isDevelopment = env === 'development'
  const isProduction = env === 'production'

  // Development configuration
  if (isDevelopment) {
    return {
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 15000, // 15 seconds for development (slower with debugging)
      retryAttempts: 2,
      retryDelay: 1000,
      enableLogging: true,
    }
  }

  // Production configuration
  if (isProduction) {
    return {
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://api.huzilerz.com',
      timeout: 10000, // 10 seconds for production
      retryAttempts: 3,
      retryDelay: 2000,
      enableLogging: false,
    }
  }

  // Staging/Test configuration
  return {
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://staging-api.huzilerz.com',
    timeout: 12000,
    retryAttempts: 2,
    retryDelay: 1500,
    enableLogging: true,
  }
}

// ============================================================================
// API Base Paths Configuration
// ============================================================================

export const API_BASE: APIBase = {
  auth: '/api/auth',
  workspaces: '/api/workspaces',
  security: '/api/security',
  subscriptions: '/api/subscriptions',
  payments: '/api/payments',
  users: '/api/users',
  store: '/api/workspaces/{workspace_id}/store/admin',
  themes: '/api/themes',
}

// ============================================================================
// Request Headers Configuration
// ============================================================================

export const getBaseHeaders = (): HeadersInit => ({
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-Client-Version': process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  'X-Client-Platform': 'web',
})

export const getAuthHeaders = (token?: string): HeadersInit => ({
  ...getBaseHeaders(),
  ...(token && { Authorization: `Bearer ${token}` }),
})

// ============================================================================
// Request Configuration
// ============================================================================

export const getRequestConfig = (includeCredentials: boolean = true): RequestInit => ({
  credentials: includeCredentials ? 'include' : 'omit', // Include httpOnly cookies
  mode: 'cors',
  cache: 'no-cache',
})

// ============================================================================
// Error Messages Configuration
// ============================================================================

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',
  UNAUTHORIZED: 'Your session has expired. Please login again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  VALIDATION_ERROR: 'Invalid data provided. Please check your input.',
  RATE_LIMITED: 'Too many requests. Please wait before trying again.',
  MAINTENANCE: 'Service is temporarily unavailable for maintenance.',
} as const

// ============================================================================
// Status Code Mapping
// ============================================================================

export const STATUS_CODE_MESSAGES: Record<number, string> = {
  400: ERROR_MESSAGES.VALIDATION_ERROR,
  401: ERROR_MESSAGES.UNAUTHORIZED,
  403: ERROR_MESSAGES.FORBIDDEN,
  404: ERROR_MESSAGES.NOT_FOUND,
  408: ERROR_MESSAGES.TIMEOUT_ERROR,
  429: ERROR_MESSAGES.RATE_LIMITED,
  500: ERROR_MESSAGES.SERVER_ERROR,
  502: ERROR_MESSAGES.SERVER_ERROR,
  503: ERROR_MESSAGES.MAINTENANCE,
  504: ERROR_MESSAGES.TIMEOUT_ERROR,
}

// ============================================================================
// Feature Flags for API Behavior
// ============================================================================

export const API_FEATURES = {
  ENABLE_REQUEST_LOGGING: process.env.NODE_ENV === 'development',
  ENABLE_RESPONSE_CACHING: true,
  ENABLE_RETRY_LOGIC: true,
  ENABLE_REQUEST_DEDUPLICATION: true,
  ENABLE_OFFLINE_QUEUE: false, // Future feature
} as const

// ============================================================================
// Export Main Configuration
// ============================================================================

export const API_CONFIG = getEnvironmentConfig()

// ============================================================================
// Configuration Validation
// ============================================================================

export const validateAPIConfig = (): boolean => {
  if (!API_CONFIG.baseURL) {
    console.error('API_CONFIG: baseURL is required')
    return false
  }

  try {
    new URL(API_CONFIG.baseURL)
  } catch {
    console.error('API_CONFIG: baseURL must be a valid URL')
    return false
  }

  if (API_CONFIG.timeout < 1000) {
    console.warn('API_CONFIG: timeout is very low, this may cause issues')
  }

  return true
}

// ============================================================================
// Utility Functions
// ============================================================================

export const buildURL = (endpoint: string, path: string = ''): string => {
  const base = API_CONFIG.baseURL
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${base}${cleanEndpoint}${path ? cleanPath : ''}`
}

export const getEndpointURL = (
  baseKey: keyof APIBase,
  path: string = ''
): string => {
  return buildURL(API_BASE[baseKey], path)
}

// ============================================================================
// Development Helpers
// ============================================================================

if (process.env.NODE_ENV === 'development') {
  // Validate configuration on startup
  if (!validateAPIConfig()) {
    console.error('Invalid API configuration detected!')
  }

  // Log configuration for debugging
  console.log('API Configuration:', {
    baseURL: API_CONFIG.baseURL,
    timeout: API_CONFIG.timeout,
    environment: process.env.NODE_ENV,
  })
}

// ============================================================================
// Export Types
// ============================================================================

export type APIConfigType = typeof API_CONFIG
export type APIBaseType = typeof API_BASE
export type APIFeaturesType = typeof API_FEATURES
export type ErrorMessagesType = typeof ERROR_MESSAGES