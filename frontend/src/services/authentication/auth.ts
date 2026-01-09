/**
 * Core Authentication Service - Enterprise Authentication Management
 * Aligned with backend auth_views.py endpoints
 */

import BaseService from '../base/BaseService'
import { apiClient } from '../api/client'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  LogoutRequest,
  LogoutResponse,
  RefreshTokenResponse,
  UserData,
  BaseAuthResponse
} from '../../types/authentication/auth'
import type {
  WorkspaceSwitchRequest,
  WorkspaceSwitchResponse
} from '../../types/authentication/workspace'

// ============================================================================
// Authentication Service 
// ============================================================================

export class AuthService extends BaseService {
  constructor() {
    super('auth')
  }

  /**
   * Login with email and password
   * Backend: POST /api/auth/login/
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    this.validateRequired(credentials as unknown as Record<string, unknown>, ['email', 'password'])

    const response = await this.postPublic<LoginResponse>('/login/', credentials)

    // Store token after successful login
    if (response.tokens?.access_token) {
      apiClient.setAuthToken(response.tokens.access_token, response.tokens.expires_in)
    }

    return response
  }

  /**
   * Register new user account
   * Backend: POST /api/auth/register/
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    this.validateRequired(userData as unknown as Record<string, unknown>, ['email', 'password', 'first_name', 'last_name'])

    const response = await this.postPublic<RegisterResponse>('/register/', userData)

    // Store token after successful registration
    if (response.tokens?.access_token) {
      apiClient.setAuthToken(response.tokens.access_token, response.tokens.expires_in)
    }

    return response
  }

  /**
   * Logout and invalidate session
   * Backend: POST /api/auth/logout/
   */
  async logout(request?: LogoutRequest): Promise<LogoutResponse> {
    const response = await this.post<LogoutResponse>('/logout/', request)

    // Clear token after logout
    apiClient.clearAuthToken()

    return response
  }

  /**
   * Refresh access token using httpOnly refresh token
   * Backend: POST /api/auth/refresh/
   *
   * Security: Workspace context is automatically preserved via refresh token
   * - Backend extracts workspace_id from refresh token (primary method)
   * - Frontend sends workspace_id for explicit override (optional safety)
   * - This ensures refreshed tokens maintain workspace claims for RBAC
   */
  async refreshToken(): Promise<RefreshTokenResponse> {
    // Get current workspace context from localStorage (if user is in workspace)
    // NOTE: This is optional - backend will use workspace_id from refresh token
    // This provides an explicit override mechanism if needed
    const currentWorkspaceId = typeof window !== 'undefined'
      ? localStorage.getItem('current_workspace_id')
      : null

    // Send workspace_id for explicit override (backend defaults to refresh token context)
    const body = currentWorkspaceId ? { workspace_id: currentWorkspaceId } : undefined

    const response = await this.postPublic<RefreshTokenResponse>('/refresh/', body)

    // Update token after refresh
    if (response.tokens?.access_token) {
      apiClient.setAuthToken(response.tokens.access_token, response.tokens.expires_in)
    }

    return response
  }

  /**
   * Get current user profile
   * Backend: GET /api/auth/profile/
   */
  async getCurrentUser(): Promise<{ success: boolean; user: UserData }> {
    return this.get<{ success: boolean; user: UserData }>('/profile/')
  }

  /**
   * Update user profile
   * Backend: PUT /api/auth/profile/
   */
  async updateProfile(updates: {
    first_name?: string
    last_name?: string
    username?: string
    bio?: string
    avatar?: string
    preferred_auth_method?: string
    security_notifications?: boolean
  }): Promise<{
    success: boolean
    message: string
    user: unknown
  }> {
    const cleanedUpdates = this.cleanData(updates)
    return this.put('/profile/', cleanedUpdates)
  }

  /**
   * Switch to different workspace
   * Backend: POST /api/auth/workspace-switch/
   *
   * Security: Tracks workspace context for token refresh flow
   * This ensures future token refreshes maintain workspace claims
   */
  async switchWorkspace(workspaceId: string): Promise<WorkspaceSwitchResponse> {
    this.validateRequired({ workspace_id: workspaceId } as unknown as Record<string, unknown>, ['workspace_id'])

    const request: WorkspaceSwitchRequest = { workspace_id: workspaceId }
    const response = await this.post<WorkspaceSwitchResponse>('/workspace-switch/', request)

    // v3.0 - NO token regeneration on workspace switch
    // Backend validates access and returns workspace details
    // Frontend updates Zustand state (handled in useWorkspace hook)

    // Track workspace context in localStorage (for persistence across page reload)
    if (typeof window !== 'undefined' && response.success) {
      localStorage.setItem('current_workspace_id', workspaceId)
    }

    return response
  }


  /**
   * Verify current session
   * Backend: GET /api/auth/verify/
   */
  async verifySession(): Promise<{ success: boolean; user: UserData }> {
    return this.get<{ success: boolean; user: UserData }>('/verify/')
  }
}

// ============================================================================
// Token Management Utilities
// ============================================================================

class TokenManager {
  /**
   * Set access token
   */
  static setAccessToken(token: string, expiresIn?: number): void {
    apiClient.setAuthToken(token, expiresIn)
  }

  /**
   * Get current access token
   */
  static getAccessToken(): string | null {
    return apiClient.getAuthToken()
  }

  /**
   * Clear access token
   */
  static clearAccessToken(): void {
    apiClient.clearAuthToken()
  }

  /**
   * Check if current token exists
   */
  static hasToken(): boolean {
    return !!apiClient.getAuthToken()
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const authService = new AuthService()
export { TokenManager }
export default authService