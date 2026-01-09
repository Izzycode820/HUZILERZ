/**
 * Authentication Types Index
 * Optimized exports to prevent circular dependencies and improve tree-shaking
 * For complex types, import directly from specific modules
 */

// ============================================================================
// CORE TYPES ONLY - Most commonly used
// ============================================================================

// Essential auth types (no re-export of everything)
export type {
  // Auth flow types
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  LogoutRequest,
  LogoutResponse,

  // Auth state (discriminated union only)
  AuthState,
  AuthContextValue,

  // JWT and tokens
  JWTPayload,
  TokenResponse,
  RefreshTokenResponse,

  // User essentials
  UserData,
  SubscriptionData,
  DeviceFingerprint,
  LocationInfo,
} from './auth';


export type {
  // Workspace context
  WorkspaceAuthContext,
  WorkspaceSwitchRequest,
  WorkspaceSwitchResponse,
  LeaveWorkspaceResponse,
  AvailableWorkspace,
  UseWorkspaceSwitchReturn,
} from './workspace';

// ============================================================================
// SPECIALIZED IMPORTS - Import directly from modules for these:
// ============================================================================
// import { MFAStatus, TOTPDevice } from './mfa'
// import { EmailVerificationRequest } from './email'
// import { PhoneVerificationRequest } from './phone'
// import { OAuth2Provider } from './oauth2'
// import { UserSecurityEvent } from './security'
// import { UserProfile, UserSession } from './user'

export type {
  // MFA essentials for auth flow
  MFAStatus,
  MFAChallenge,
  MFAChallengeRequest,
  MFAChallengeResponse,
  TOTPSetupRequest,
  TOTPConfirmRequest,
  MFAVerifyRequest,
  BackupCodesRegenerateRequest,
  MFADisableRequest,
  TOTPDevice,
  BackupCodesStats,
} from './mfa';

// Re-exports removed to prevent duplication

// ============================================================================
// Common Error Types (Aligned with Backend)
// ============================================================================
export interface AuthenticationError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
  statusCode?: number;
  retryAfter?: number;
}

export interface ValidationErrors {
  [field: string]: string[];
}

export interface APIErrorResponse {
  success: false;
  error: string;
  code?: string;
  errors?: ValidationErrors;
  details?: Record<string, unknown>;
  message?: string; // Backend includes message field
}

// ============================================================================
// Common Response Types
// ============================================================================
export interface BaseResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data?: T[];
  pagination?: {
    current_page: number;
    total_pages: number;
    total_count: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
  };
  error?: string;
}

export interface DataResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// ============================================================================
// Hook Common Types
// ============================================================================
export interface BaseHookReturn {
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export interface AsyncHookReturn<T> extends BaseHookReturn {
  data: T | null;
  refresh: () => Promise<void>;
}

export interface MutationHookReturn<TRequest, TResponse> extends BaseHookReturn {
  mutate: (request: TRequest) => Promise<TResponse>;
  data: TResponse | null;
  reset: () => void;
}

// ============================================================================
// Storage Types
// ============================================================================
export interface StorageAdapter {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
  removeItem: (key: string) => void;
  clear: () => void;
}

export interface AuthStorageKeys {
  ACCESS_TOKEN: string;
  REFRESH_TOKEN: string;
  USER_DATA: string;
  WORKSPACE_DATA: string;
  AUTH_STATE: string;
  PREFERENCES: string;
}

// ============================================================================
// Event Types
// ============================================================================
export interface AuthEvent {
  type: 'login' | 'logout' | 'token_refresh' | 'workspace_switch' | 'mfa_required';
  payload?: unknown;
  timestamp: number;
}

export interface AuthEventHandler {
  (event: AuthEvent): void;
}

// ============================================================================
// Configuration Types
// ============================================================================
export interface AuthConfig {
  apiBaseUrl: string;
  tokenRefreshInterval: number;
  sessionTimeoutMinutes: number;
  enableMFA: boolean;
  enableOAuth2: boolean;
  enableWorkspaces: boolean;
  enableSecurityMonitoring: boolean;
  storageAdapter: StorageAdapter;
  onAuthEvent?: AuthEventHandler;
}

// ============================================================================
// Utility Types
// ============================================================================
export type AuthStatus = 'authenticated' | 'unauthenticated' | 'loading' | 'error';

export type PermissionLevel = 'none' | 'read' | 'write' | 'admin' | 'owner';

export type AuthMethod = 'email' | 'oauth2' | 'sso' | 'mfa';

export type TokenType = 'access' | 'refresh' | 'reset' | 'verification';

// ============================================================================
// Type Guards
// ============================================================================
// ============================================================================
// Enhanced Type Guards
// ============================================================================
export const isAuthError = (error: unknown): error is AuthenticationError => {
  return typeof error === 'object' && error !== null && 'code' in error && 'message' in error && typeof error.code === 'string' && typeof error.message === 'string';
};

export const isAPIError = (response: unknown): response is APIErrorResponse => {
  return typeof response === 'object' && response !== null && 'success' in response && 'error' in response && response.success === false && typeof response.error === 'string';
};

import type { JWTPayload, AuthState } from './auth';
import type { WorkspaceAuthContext } from './workspace';

export const hasValidToken = (payload: unknown): payload is JWTPayload => {
  return typeof payload === 'object' && payload !== null && 'user_id' in payload && 'exp' in payload && 'type' in payload &&
    typeof payload.user_id === 'number' && // Aligned with backend
    typeof payload.exp === 'number' &&
    payload.exp > Date.now() / 1000 &&
    (payload.type === 'access' || payload.type === 'refresh');
};

export const isWorkspaceAuthContext = (context: unknown): context is WorkspaceAuthContext => {
  return typeof context === 'object' && context !== null && 'id' in context && 'name' in context && 'role' in context && 'permissions' in context &&
    typeof context.id === 'string' &&
    typeof context.name === 'string' &&
    typeof context.role === 'string' &&
    Array.isArray(context.permissions);
};

// Auth state type guards for discriminated union
export const isAuthenticatedState = (state: unknown): state is Extract<AuthState, { status: 'authenticated' }> => {
  return typeof state === 'object' && state !== null && 'status' in state && state.status === 'authenticated' && 'user' in state && typeof state.user === 'object' && state.user !== null && 'id' in state.user && typeof state.user.id === 'number';
};

export const isLoadingState = (state: unknown): state is Extract<AuthState, { status: 'loading' }> => {
  return typeof state === 'object' && state !== null && 'status' in state && state.status === 'loading';
};

export const isErrorState = (state: unknown): state is Extract<AuthState, { status: 'error' }> => {
  return typeof state === 'object' && state !== null && 'status' in state && state.status === 'error' && 'error' in state && state.error !== null;
};

export const isIdleState = (state: unknown): state is Extract<AuthState, { status: 'idle' }> => {
  return typeof state === 'object' && state !== null && 'status' in state && state.status === 'idle';
};

// ============================================================================
// Constants
// ============================================================================
// Performance optimized with const assertions
export const AUTH_CONSTANTS = {
  TOKEN_REFRESH_THRESHOLD: 5 * 60 * 1000, // 5 minutes in milliseconds
  SESSION_TIMEOUT_WARNING: 2 * 60 * 1000, // 2 minutes in milliseconds
  MAX_LOGIN_ATTEMPTS: 5,
  PASSWORD_RESET_TOKEN_EXPIRY: 60 * 60 * 1000, // 1 hour
  EMAIL_VERIFICATION_CODE_EXPIRY: 15 * 60 * 1000, // 15 minutes
  MFA_CODE_EXPIRY: 30 * 1000, // 30 seconds
  WORKSPACE_SWITCH_TIMEOUT: 10 * 1000, // 10 seconds
} as const;

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
} as const;

// Aligned with backend and legacy constants
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'huzilerz_token',
  REFRESH_TOKEN: 'huzilerz_refresh_token',
  USER_DATA: 'huzilerz_user',
  WORKSPACE_DATA: 'huzilerz_workspace_data',
  PREFERENCES: 'huzilerz_preferences',
  LAST_ACTIVITY: 'huzilerz_last_activity',
} as const;