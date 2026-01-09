/**
 * User Profile and Session Management Types
 * Based on backend User model and session tracking
 */

// Import security types to avoid duplication
import type { UserSecurityEvent } from './security';

// ============================================================================
// User Profile Types
// ============================================================================

export interface UserProfile {
  id: number; // Aligned with backend User model IntegerField
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar?: string;
  bio?: string;
  email_verified: boolean;
  phone_verified: boolean;
  two_factor_enabled: boolean;
  preferred_auth_method: string;
  security_notifications: boolean;
  created_at: string;
  last_login?: string;
}

export interface ProfileUpdateRequest {
  first_name?: string;
  last_name?: string;
  username?: string;
  bio?: string;
  avatar?: string;
  preferred_auth_method?: string;
  security_notifications?: boolean;
}

export interface ProfileUpdateResponse {
  success: boolean;
  message?: string;
  user?: UserProfile;
  error?: string;
}

export interface ProfileResponse {
  success: boolean;
  user?: UserProfile;
  error?: string;
}

// ============================================================================
// Session Management Types
// ============================================================================

export interface UserSession {
  id: string;
  device_name: string;
  ip_address: string;
  last_used: string;
  created_at: string;
  is_current: boolean;
  user_agent?: string;
  location?: string;
  platform?: string;
  browser?: string;
}

export interface SessionsResponse {
  success: boolean;
  sessions?: UserSession[];
  error?: string;
}

export interface RevokeSessionRequest {
  session_id: string;
}

export interface RevokeSessionResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface RevokeAllSessionsRequest {
  confirm: boolean;
}

export interface RevokeAllSessionsResponse {
  success: boolean;
  revoked_count?: number;
  message?: string;
  error?: string;
}

// ============================================================================
// User Preferences Types
// ============================================================================

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  email_notifications: {
    security_alerts: boolean;
    product_updates: boolean;
    marketing: boolean;
    weekly_digest: boolean;
  };
  privacy_settings: {
    profile_visibility: 'public' | 'private' | 'friends';
    activity_tracking: boolean;
    analytics_data: boolean;
  };
  workspace_defaults: {
    default_workspace_id?: string;
    auto_switch_workspace: boolean;
  };
}

export interface UpdatePreferencesRequest {
  theme?: 'light' | 'dark' | 'system';
  language?: string;
  timezone?: string;
  email_notifications?: Partial<UserPreferences['email_notifications']>;
  privacy_settings?: Partial<UserPreferences['privacy_settings']>;
  workspace_defaults?: Partial<UserPreferences['workspace_defaults']>;
}

export interface PreferencesResponse {
  success: boolean;
  preferences?: UserPreferences;
  message?: string;
  error?: string;
}

// ============================================================================
// Account Security Types
// ============================================================================

export interface AccountSecurityInfo {
  password_last_changed: string;
  login_attempts_count: number;
  last_failed_login?: string;
  security_score: number;
  active_sessions_count: number;
  mfa_enabled: boolean;
  backup_codes_remaining: number;
  recent_security_events: UserSecurityEvent[];
}

// SecurityEvent moved to security.ts to avoid duplication

export interface AccountSecurityResponse {
  success: boolean;
  security_info?: AccountSecurityInfo;
  error?: string;
}

// ============================================================================
// Password Management Types
// ============================================================================

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ChangePasswordResponse {
  success: boolean;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
}

export interface PasswordStrength {
  score: number; // 0-4
  feedback: string[];
  is_valid: boolean;
  requirements: {
    min_length: boolean;
    has_uppercase: boolean;
    has_lowercase: boolean;
    has_numbers: boolean;
    has_symbols: boolean;
    not_common: boolean;
  };
}

// ============================================================================
// Account Management Types
// ============================================================================

export interface DeactivateAccountRequest {
  password: string;
  reason?: string;
  feedback?: string;
}

export interface DeactivateAccountResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface DeleteAccountRequest {
  password: string;
  confirmation_text: string;
  reason?: string;
}

export interface DeleteAccountResponse {
  success: boolean;
  message?: string;
  scheduled_deletion_date?: string;
  error?: string;
}

// ============================================================================
// User Activity Types
// ============================================================================

export interface UserActivity {
  id: string;
  activity_type: string;
  description: string;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
  metadata?: Record<string, unknown>;
}

export interface ActivityLogResponse {
  success: boolean;
  activities?: UserActivity[];
  pagination?: {
    current_page: number;
    total_pages: number;
    total_count: number;
    has_next: boolean;
    has_previous: boolean;
  };
  error?: string;
}

export interface ActivityLogRequest {
  page?: number;
  limit?: number;
  activity_type?: string;
  date_from?: string;
  date_to?: string;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseProfileReturn {
  profile: UserProfile | null;
  isLoading: boolean;
  error: string | null;
  updateProfile: (data: ProfileUpdateRequest) => Promise<ProfileUpdateResponse>;
  refreshProfile: () => Promise<void>;
  clearError: () => void;
}

export interface UseSessionsReturn {
  sessions: UserSession[];
  isLoading: boolean;
  error: string | null;
  refreshSessions: () => Promise<void>;
  revokeSession: (sessionId: string) => Promise<RevokeSessionResponse>;
  revokeAllSessions: () => Promise<RevokeAllSessionsResponse>;
  clearError: () => void;
}

export interface UsePreferencesReturn {
  preferences: UserPreferences | null;
  isLoading: boolean;
  error: string | null;
  updatePreferences: (data: UpdatePreferencesRequest) => Promise<PreferencesResponse>;
  refreshPreferences: () => Promise<void>;
  clearError: () => void;
}

export interface UseAccountSecurityReturn {
  securityInfo: AccountSecurityInfo | null;
  isLoading: boolean;
  error: string | null;
  refreshSecurityInfo: () => Promise<void>;
  changePassword: (data: ChangePasswordRequest) => Promise<ChangePasswordResponse>;
  checkPasswordStrength: (password: string) => PasswordStrength;
  clearError: () => void;
}

export interface UseActivityLogReturn {
  activities: UserActivity[];
  pagination: ActivityLogResponse['pagination'] | null;
  isLoading: boolean;
  error: string | null;
  loadActivities: (request?: ActivityLogRequest) => Promise<void>;
  loadMore: () => Promise<void>;
  clearError: () => void;
}

// ============================================================================
// Avatar Management Types
// ============================================================================

export interface AvatarUploadRequest {
  file: File;
}

export interface AvatarUploadResponse {
  success: boolean;
  avatar_url?: string;
  message?: string;
  error?: string;
}

export interface AvatarDeleteResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// ============================================================================
// Data Export Types
// ============================================================================

export interface DataExportRequest {
  format: 'json' | 'csv';
  include_activity_log: boolean;
  include_security_events: boolean;
  date_from?: string;
  date_to?: string;
}

export interface DataExportResponse {
  success: boolean;
  export_id?: string;
  message?: string;
  estimated_completion?: string;
  error?: string;
}

export interface ExportStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  created_at: string;
  completed_at?: string;
  download_url?: string;
  error_message?: string;
}

export interface ExportStatusResponse {
  success: boolean;
  export_status?: ExportStatus;
  error?: string;
}

// ============================================================================
// Constants
// ============================================================================

export const USER_ACTIVITY_TYPES = {
  LOGIN: 'login',
  LOGOUT: 'logout',
  PROFILE_UPDATE: 'profile_update',
  PASSWORD_CHANGE: 'password_change',
  MFA_SETUP: 'mfa_setup',
  SESSION_REVOKE: 'session_revoke',
  EMAIL_CHANGE: 'email_change',
  PREFERENCES_UPDATE: 'preferences_update',
} as const;

export const SECURITY_EVENT_TYPES = {
  LOGIN_SUCCESS: 'login_success',
  LOGIN_FAILED: 'login_failed',
  MFA_VERIFICATION: 'mfa_verification',
  PASSWORD_RESET: 'password_reset',
  SUSPICIOUS_ACTIVITY: 'suspicious_activity',
  ACCOUNT_LOCKED: 'account_locked',
} as const;

export const PROFILE_VALIDATION = {
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 30,
  BIO_MAX_LENGTH: 500,
  FIRST_NAME_MAX_LENGTH: 30,
  LAST_NAME_MAX_LENGTH: 30,
} as const;

export type UserActivityType = typeof USER_ACTIVITY_TYPES[keyof typeof USER_ACTIVITY_TYPES];
export type SecurityEventType = typeof SECURITY_EVENT_TYPES[keyof typeof SECURITY_EVENT_TYPES];