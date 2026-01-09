/**
 * Core Authentication Types
 * Aligned with backend AuthenticationService and JWT patterns
 * Features: Discriminated unions, feature bitmaps, type safety
 */

// ============================================================================
// Login Types
// ============================================================================

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  success: boolean;
  user?: UserData;
  tokens?: {
    access_token: string;
    token_type: string;
    expires_in: number;
  };
  workspace?: WorkspaceAuthContext;
  message?: string;
  error?: string;
  mfa_required?: boolean;
  mfa_challenge_id?: string;
}

// ============================================================================
// Registration Types
// ============================================================================

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  username?: string;
}

export interface RegisterResponse {
  success: boolean;
  user?: UserData;
  tokens?: {
    access_token: string;
    token_type: string;
    expires_in: number;
  };
  message?: string;
  error?: string;
  email_verification_required?: boolean;
  verification_id?: string;
}

// ============================================================================
// Token Types
// ============================================================================

export interface TokenResponse {
  success: boolean;
  access_token: string;
  token_type: string;
  expires_in: number;
  message?: string;
  workspace?: WorkspaceAuthContext;
}

/**
 * Refresh Token Response (Industry Standard: OAuth2)
 *
 * v3.0 - Simple Session Extension:
 * - Refresh tokens extend sessions, they don't change authorization scope
 * - NO workspace context in response (workspace sent via X-Workspace-Id header)
 * - Frontend maintains workspace state in Zustand
 * - Eliminates complex refresh logic and race conditions
 */
export interface RefreshTokenResponse {
  success: boolean;
  tokens?: {
    access_token: string;
    token_type: string;
    expires_in: number;
  };
  user?: {
    id: number;
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    avatar?: string;
    email_verified: boolean;
  };
  message?: string;
  error?: string;
}

/**
 * JWT Payload Structure (Industry Standard: Shopify/Stripe/Linear)
 *
 * v3.0 - Header-Based Workspace Context:
 * - JWT contains ONLY user identity + subscription tier
 * - NO workspace fields (workspace sent via X-Workspace-Id header per-request)
 * - Eliminates context drift, race conditions, and stale workspace bugs
 *
 * Access Token = Identity + Global Roles + Subscription
 * Refresh Token = Identity only (extends session, doesn't change scope)
 */
export interface JWTPayload {
  // User identity claims
  user_id: number;
  email: string;
  username: string;

  // Global system roles (NOT workspace-specific)
  is_staff?: boolean;
  is_superuser?: boolean;
  is_active?: boolean;

  // Subscription data (tier, status, billing)
  subscription?: SubscriptionData;

  // Standard JWT claims
  iat: number;
  exp: number;
  type: 'access' | 'refresh';
  jti: string;
  iss?: string;
  aud?: string;
}

// ============================================================================
// User Data Types
// ============================================================================

export interface UserData {
  id: number; // Aligned with backend IntegerField
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar?: string;
  bio?: string;
  email_verified: boolean;
  phone_number?: string;
  phone_verified: boolean;
  two_factor_enabled: boolean;
  preferred_auth_method: string;
  security_notifications: boolean;
  created_at: string;
  last_login?: string;
  // Add subscription data from JWT
  subscription: SubscriptionData;
}

// ============================================================================
// Device Fingerprinting Types (from Backend)
// ============================================================================

// Aligned with backend _extract_device_info and _get_client_ip
export interface DeviceFingerprint {
  user_agent: string;
  device_name: string;
  browser: string;
  os: string;
  device_type: 'mobile' | 'tablet' | 'desktop';
}

export interface LocationInfo {
  ip_address: string;
  country?: string;
  city?: string;
  region?: string;
}

// ============================================================================
// Subscription Data Types (from JWT)
// ============================================================================

/**
 * Subscription Data (Minimal JWT Claims)
 * Industry Standard: Stripe/GitHub/Vercel approach
 *
 * JWT contains minimal data + version hash
 * Full capabilities fetched separately via API
 */
export interface SubscriptionData {
  // Core subscription info
  tier: 'free' | 'beginner' | 'pro' | 'enterprise';
  status: 'active' | 'inactive' | 'expired' | 'grace_period';
  expires_at: string | null;

  // Capabilities versioning (industry standard)
  capabilities_version: string; // Hash from plans.yaml (e.g., 'v2_abc123de')
  billing_cycle: 'monthly' | 'yearly';
  currency: string; // e.g., 'XAF'

  // Trial claims (from JWT)
  trial: {
    eligible: boolean;
    used_trial: boolean;
    current_tier: string | null;
    expires_at: string | null;
    can_upgrade: boolean;
    days_remaining: number | null;
    used_at: string | null;
    ineligible_reason?: 'paid_subscription_active' | 'trial_already_used' | null;
  };

  // Template claims (from JWT)
  templates: {
    owned_count: number;
    owned_templates: string[];
  };
}

/**
 * Full Capabilities Response (from API)
 * Fetched separately from GET /api/subscriptions/me/capabilities/
 */
export interface CapabilitiesResponse {
  tier: 'free' | 'beginner' | 'pro' | 'enterprise';
  status: 'active' | 'inactive' | 'expired' | 'grace_period';
  capabilities: Record<string, any>; // Full capabilities from YAML
  version: string; // Same as capabilities_version in JWT
  expires_at: string | null;
}

// ============================================================================
// Import Workspace Types
// ============================================================================

// Import from workspace.ts to avoid duplication
import type { WorkspaceAuthContext, WorkspaceSwitchResponse } from './workspace';

// ============================================================================
// Authentication State Types
// ============================================================================

// Discriminated union for type-safe auth states - ONLY this pattern allowed
export type AuthState =
  | {
    status: 'idle';
    user: null;
    error: null;
    isAuthenticated: false;
    isLoading: false;
    tokens: null;
    workspace: null;
  }
  | {
    status: 'loading';
    user: null;
    error: null;
    isAuthenticated: false;
    isLoading: true;
    tokens: null;
    workspace: null;
  }
  | {
    status: 'authenticated';
    user: UserData;
    error: null;
    isAuthenticated: true;
    isLoading: false;
    tokens: {
      access_token: string;
      token_type: string;
      expires_in: number;
    };
    workspace: WorkspaceAuthContext | null;
    lastActivity: number;
  }
  | {
    status: 'error';
    user: null;
    error: AuthError;
    isAuthenticated: false;
    isLoading: false;
    tokens: null;
    workspace: null;
  };

// REMOVED: AuthStatus - replaced with AuthState discriminated union

// ============================================================================
// Logout Types
// ============================================================================

export interface LogoutRequest {
  revoke_all_sessions?: boolean;
}

export interface LogoutResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// ============================================================================
// Error Types
// ============================================================================

export interface AuthError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  field?: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export interface AuthErrorResponse {
  success: false;
  error: string;
  code?: string;
  errors?: ValidationError[];
  details?: Record<string, unknown>;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface BaseAuthResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export type AuthResponse<T = unknown> = BaseAuthResponse & {
  data?: T;
};

// ============================================================================
// Authentication Context Types
// ============================================================================

export interface AuthContextValue {
  // State (discriminated union only)
  state: AuthState;

  // Actions
  login: (credentials: LoginRequest) => Promise<LoginResponse>;
  register: (data: RegisterRequest) => Promise<RegisterResponse>;
  logout: (options?: LogoutRequest) => Promise<void>;
  refreshToken: () => Promise<RefreshTokenResponse>;
  switchWorkspace: (workspaceId: string) => Promise<WorkspaceSwitchResponse>;
  clearError: () => void;

  // Utilities
  isTokenExpired: () => boolean;
  hasPermission: (permission: string) => boolean;
  hasFeature: (featureName: string) => boolean; // Uses feature bitmap system
  getFeatureBitmap: () => number | null;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseLoginReturn {
  login: (credentials: LoginRequest) => Promise<LoginResponse>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export interface UseRegisterReturn {
  register: (data: RegisterRequest) => Promise<RegisterResponse>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export interface UseLogoutReturn {
  logout: (options?: LogoutRequest) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export interface UseTokenRefreshReturn {
  refresh: () => Promise<RefreshTokenResponse>;
  isRefreshing: boolean;
  error: string | null;
  lastRefresh: number | null;
}

export interface UseAuthStateReturn {
  auth: AuthState;
  isAuthenticated: boolean;
  user: UserData | null;
  workspace: WorkspaceAuthContext | null;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Storage Types
// ============================================================================

export interface AuthStorage {
  getToken: () => string | null;
  setToken: (token: string) => void;
  removeToken: () => void;
  getRefreshToken: () => string | null;
  setRefreshToken: (token: string) => void;
  removeRefreshToken: () => void;
  clear: () => void;
}

// ============================================================================
// Constants
// ============================================================================

export const AUTH_STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  WORKSPACE_DATA: 'workspace_data',
  AUTH_STATE: 'auth_state',
} as const;

export const AUTH_ERRORS = {
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  TOKEN_INVALID: 'TOKEN_INVALID',
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  ACCOUNT_DISABLED: 'ACCOUNT_DISABLED',
  MFA_REQUIRED: 'MFA_REQUIRED',
  RATE_LIMITED: 'RATE_LIMITED',
  NETWORK_ERROR: 'NETWORK_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
} as const;

export type AuthErrorCode = typeof AUTH_ERRORS[keyof typeof AUTH_ERRORS];