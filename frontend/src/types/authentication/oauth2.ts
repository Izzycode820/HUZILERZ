/**
 * OAuth2 Social Authentication Types
 * Based on backend OAuth2Service and social provider patterns
 */

// ============================================================================
// OAuth2 Provider Types
// ============================================================================

export interface OAuth2Provider {
  id: string;
  name: string;
  display_name: string;
  icon?: string;
  color?: string;
  description?: string;
  scopes: readonly string[]; // Immutable for security
  configured: boolean;
  // REMOVED: Sensitive endpoints not exposed to frontend
}

export interface OAuth2ProvidersResponse {
  success: boolean;
  providers?: OAuth2Provider[];
  error?: string;
}

// ============================================================================
// OAuth2 Flow Initiation Types
// ============================================================================

export interface OAuth2InitiateRequest {
  provider: string;
  redirect_uri?: string;
  state?: string;
  scopes?: string[];
}

export interface OAuth2InitiateResponse {
  success: boolean;
  data?: {
    authorization_url: string;
    state: string;
    provider: string;
    expires_in: number;
  };
  error?: string;
}

// ============================================================================
// OAuth2 Callback Types
// ============================================================================

export interface OAuth2CallbackRequest {
  provider: string;
  code: string;
  state: string;
  error?: string;
  error_description?: string;
}

export interface OAuth2CallbackResponse {
  success: boolean;
  user?: {
    id: number; // Aligned with backend User model
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    avatar?: string;
    email_verified: boolean;
  };
  access_token?: string;
  token_type?: string;
  expires_in?: number;
  workspace?: {
    id: string;
    name: string;
    type: string;
    role: string;
  };
  is_new_user?: boolean;
  linked_account?: boolean;
  message?: string;
  error?: string;
}

// ============================================================================
// OAuth2 Token Management Types
// ============================================================================

export interface OAuth2TokenRefreshRequest {
  provider: string;
  refresh_token: string;
}

export interface OAuth2TokenRefreshResponse {
  success: boolean;
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
  token_type?: string;
  error?: string;
}

export interface OAuth2TokenRevokeRequest {
  provider: string;
  token: string;
  token_type_hint?: 'access_token' | 'refresh_token';
}

export interface OAuth2TokenRevokeResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// ============================================================================
// OAuth2 Account Connection Types
// ============================================================================

export interface OAuth2ConnectionStatus {
  provider: string;
  is_connected: boolean;
  connected_at?: string;
  account_info?: {
    provider_user_id: string;
    email: string;
    display_name: string;
    avatar?: string;
  };
  permissions: string[];
  last_used?: string;
  expires_at?: string;
}

export interface OAuth2ConnectionsResponse {
  success: boolean;
  connections?: OAuth2ConnectionStatus[];
  error?: string;
}

export interface OAuth2DisconnectRequest {
  provider: string;
  revoke_tokens?: boolean;
}

export interface OAuth2DisconnectResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// ============================================================================
// OAuth2 User Information Types
// ============================================================================

export interface OAuth2UserInfo {
  provider_user_id: string;
  email: string;
  email_verified: boolean;
  name: string;
  given_name?: string;
  family_name?: string;
  picture?: string;
  locale?: string;
  timezone?: string;
  profile_url?: string;
  raw_data: Record<string, unknown>;
}

export interface OAuth2UserInfoResponse {
  success: boolean;
  user_info?: OAuth2UserInfo;
  error?: string;
}

// ============================================================================
// OAuth2 Configuration Types
// ============================================================================

// REMOVED: OAuth2Configuration - Contains sensitive data not for frontend

export interface OAuth2TestResponse {
  success: boolean;
  test_results?: {
    authorization_endpoint: boolean;
    token_endpoint: boolean;
    user_info_endpoint: boolean;
    scopes_valid: boolean;
  };
  error?: string;
}

// ============================================================================
// OAuth2 Security Types
// ============================================================================

export interface OAuth2SecurityEvent {
  id: string;
  provider: string;
  event_type: 'login' | 'token_refresh' | 'connection' | 'disconnection' | 'security_alert';
  description: string;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
  risk_level: 'low' | 'medium' | 'high';
  metadata: Record<string, unknown>;
}

export interface OAuth2SecurityEventsResponse {
  success: boolean;
  events?: OAuth2SecurityEvent[];
  pagination?: {
    current_page: number;
    total_pages: number;
    total_count: number;
  };
  error?: string;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseOAuth2ProvidersReturn {
  providers: OAuth2Provider[];
  isLoading: boolean;
  error: string | null;
  refreshProviders: () => Promise<void>;
  clearError: () => void;
}

export interface UseOAuth2LoginReturn {
  isLoading: boolean;
  error: string | null;
  initiateLogin: (provider: string, options?: { scopes?: string[] }) => Promise<OAuth2InitiateResponse>;
  handleCallback: (request: OAuth2CallbackRequest) => Promise<OAuth2CallbackResponse>;
  clearError: () => void;
}

export interface UseOAuth2ConnectionsReturn {
  connections: OAuth2ConnectionStatus[];
  isLoading: boolean;
  error: string | null;
  refreshConnections: () => Promise<void>;
  connectProvider: (provider: string) => Promise<OAuth2InitiateResponse>;
  disconnectProvider: (provider: string, revokeTokens?: boolean) => Promise<OAuth2DisconnectResponse>;
  refreshToken: (provider: string) => Promise<OAuth2TokenRefreshResponse>;
  clearError: () => void;
}

export interface UseOAuth2SecurityReturn {
  events: OAuth2SecurityEvent[];
  isLoading: boolean;
  error: string | null;
  loadEvents: (page?: number) => Promise<void>;
  clearError: () => void;
}

// ============================================================================
// OAuth2 Flow State Types
// ============================================================================

export interface OAuth2FlowState {
  provider: string | null;
  state: string | null;
  isInitiating: boolean;
  isProcessingCallback: boolean;
  authorizationUrl: string | null;
  error: string | null;
  redirectUri: string | null;
}

export interface OAuth2CallbackState {
  provider: string | null;
  code: string | null;
  state: string | null;
  error: string | null;
  isProcessing: boolean;
  result: OAuth2CallbackResponse | null;
}

// ============================================================================
// OAuth2 Error Types
// ============================================================================

export interface OAuth2Error {
  error: string;
  error_description?: string;
  error_uri?: string;
  state?: string;
}

export interface OAuth2ErrorResponse {
  success: false;
  error: string;
  error_code?: string;
  error_details?: OAuth2Error;
}

// ============================================================================
// Constants
// ============================================================================

export const OAUTH2_PROVIDERS = {
  GOOGLE: 'google',
  GITHUB: 'github',
  FACEBOOK: 'facebook',
  TWITTER: 'twitter',
  LINKEDIN: 'linkedin',
  MICROSOFT: 'microsoft',
  APPLE: 'apple',
} as const;

export const OAUTH2_SCOPES = {
  GOOGLE: {
    EMAIL: 'email',
    PROFILE: 'profile',
    OPENID: 'openid',
  },
  GITHUB: {
    USER: 'user:email',
    READ_USER: 'read:user',
  },
  FACEBOOK: {
    EMAIL: 'email',
    PUBLIC_PROFILE: 'public_profile',
  },
  MICROSOFT: {
    USER_READ: 'User.Read',
    EMAIL: 'email',
    PROFILE: 'profile',
  },
} as const;

export const OAUTH2_ERRORS = {
  ACCESS_DENIED: 'access_denied',
  INVALID_REQUEST: 'invalid_request',
  INVALID_CLIENT: 'invalid_client',
  INVALID_GRANT: 'invalid_grant',
  INVALID_SCOPE: 'invalid_scope',
  UNAUTHORIZED_CLIENT: 'unauthorized_client',
  UNSUPPORTED_GRANT_TYPE: 'unsupported_grant_type',
  UNSUPPORTED_RESPONSE_TYPE: 'unsupported_response_type',
  SERVER_ERROR: 'server_error',
  TEMPORARILY_UNAVAILABLE: 'temporarily_unavailable',
} as const;

export const OAUTH2_EVENT_TYPES = {
  LOGIN: 'login',
  TOKEN_REFRESH: 'token_refresh',
  CONNECTION: 'connection',
  DISCONNECTION: 'disconnection',
  SECURITY_ALERT: 'security_alert',
} as const;

export const OAUTH2_TOKEN_TYPES = {
  BEARER: 'Bearer',
  MAC: 'mac',
} as const;

export const OAUTH2_RESPONSE_TYPES = {
  CODE: 'code',
  TOKEN: 'token',
  ID_TOKEN: 'id_token',
} as const;

export const OAUTH2_GRANT_TYPES = {
  AUTHORIZATION_CODE: 'authorization_code',
  REFRESH_TOKEN: 'refresh_token',
  CLIENT_CREDENTIALS: 'client_credentials',
} as const;

export const OAUTH2_CONSTANTS = {
  STATE_LENGTH: 32,
  CODE_VERIFIER_LENGTH: 128,
  DEFAULT_TOKEN_EXPIRY: 3600, // 1 hour
  MAX_REDIRECT_URI_LENGTH: 2048,
  CALLBACK_TIMEOUT_SECONDS: 300, // 5 minutes
} as const;

export type OAuth2ProviderType = typeof OAUTH2_PROVIDERS[keyof typeof OAUTH2_PROVIDERS];
export type OAuth2ErrorType = typeof OAUTH2_ERRORS[keyof typeof OAUTH2_ERRORS];
export type OAuth2EventType = typeof OAUTH2_EVENT_TYPES[keyof typeof OAUTH2_EVENT_TYPES];
export type OAuth2TokenType = typeof OAUTH2_TOKEN_TYPES[keyof typeof OAUTH2_TOKEN_TYPES];
export type OAuth2ResponseType = typeof OAUTH2_RESPONSE_TYPES[keyof typeof OAUTH2_RESPONSE_TYPES];
export type OAuth2GrantType = typeof OAUTH2_GRANT_TYPES[keyof typeof OAUTH2_GRANT_TYPES];