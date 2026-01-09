/**
 * Multi-Factor Authentication Types
 * Based on backend MFAService and TOTP/backup code patterns
 */

// ============================================================================
// TOTP Setup Types
// ============================================================================

export interface TOTPSetupRequest {
  device_name?: string;
  force_reset?: boolean;
}

export interface TOTPSetupResponse {
  success: boolean;
  message?: string;
  data?: {
    device_id: string;
    device_name: string;
    qr_code_base64: string;
    manual_entry_key: string;
    issuer: string;
    account_name: string;
    setup_instructions: {
      step1: string;
      step2: string;
      step3: string;
    };
  };
  device_status?: string;
  error?: string;
}

export interface TOTPConfirmRequest {
  token: string;
}

export interface TOTPConfirmResponse {
  success: boolean;
  message?: string;
  data?: {
    device_confirmed: boolean;
    backup_codes: string[];
    backup_codes_info: {
      count: number;
      expiration_days: number;
      single_use: boolean;
      storage_warning: string;
    };
  };
  error?: string;
}

// ============================================================================
// MFA Verification Types
// ============================================================================

export interface MFAVerifyRequest {
  token: string; // 6-digit TOTP or backup code
}

export interface MFAVerifyResponse {
  success: boolean;
  message?: string;
  method?: 'totp' | 'backup_code';
  remaining_backup_codes?: number;
  warning?: string;
  error?: string;
}

// ============================================================================
// TOTP Device Types
// ============================================================================

export interface TOTPDevice {
  id: string;
  name: string;
  is_active: boolean;
  is_confirmed: boolean;
  is_locked: boolean;
  created_at: string;
  activated_at?: string;
  last_used?: string;
  failure_count: number;
  total_verifications: number;
  lockout_until?: string;
}

// ============================================================================
// Backup Codes Types
// ============================================================================

export interface BackupCode {
  id: string;
  code_partial: string; // First few characters for display
  status: 'unused' | 'used' | 'expired' | 'revoked';
  created_at: string;
  used_at?: string;
  expires_at: string;
}

export interface BackupCodesStats {
  total: number;
  unused: number;
  used: number;
  expired: number;
  revoked?: number;
}

export interface BackupCodesRegenerateRequest {
  current_mfa_token?: string;
  count?: number;
}

export interface BackupCodesRegenerateResponse {
  success: boolean;
  message?: string;
  data?: {
    backup_codes: string[];
    codes_generated: number;
    expiration_days: number;
    warning: string;
  };
  error?: string;
}

export interface BackupCodesStatusResponse {
  success: boolean;
  data?: {
    status: BackupCodesStats;
    recent_usage: Array<{
      code_partial: string;
      used_at: string;
      used_ip: string;
    }>;
    recommendations: string[];
  };
  error?: string;
}

// ============================================================================
// MFA Status Types
// ============================================================================

export interface MFAEnforcementPolicy {
  required: boolean;
  reason: string;
  grace_period_days: number | null;
}

export interface MFAStatus {
  mfa_enabled: boolean;
  totp_device: TOTPDevice | null;
  backup_codes: BackupCodesStats;
  enforcement: MFAEnforcementPolicy;
  security_score: number; // 0-100
}

export interface MFAStatusResponse {
  success: boolean;
  data?: MFAStatus;
  error?: string;
}

// ============================================================================
// MFA Management Types
// ============================================================================

export interface MFADisableRequest {
  token: string; // Current MFA token for confirmation
}

export interface MFADisableResponse {
  success: boolean;
  message?: string;
  security_warning?: string;
  error?: string;
}

export interface UnlockTOTPDeviceResponse {
  success: boolean;
  message?: string;
  lockout_until?: string;
  error?: string;
}

// ============================================================================
// MFA Security Report Types
// ============================================================================

export interface SecurityEvent {
  event_type: string;
  description: string;
  risk_level: number; // 0-4 numeric levels matching backend
  created_at: string;
  ip_address?: string;
  metadata?: Record<string, unknown>;
}

export interface MFASecurityReport {
  user_id: number; // Aligned with backend User model
  mfa_status: MFAStatus;
  security_score: number;
  recent_security_events: SecurityEvent[];
  recommendations: Array<{
    priority: 'low' | 'medium' | 'high' | 'critical';
    type: string;
    message: string;
  }>;
}

export interface MFASecurityReportResponse {
  success: boolean;
  data?: MFASecurityReport;
  error?: string;
}

// ============================================================================
// MFA Challenge Types (for login flow)
// ============================================================================

export interface MFAChallenge {
  challenge_id: string;
  challenge_type: 'totp' | 'backup_code';
  expires_at: string;
  attempts_remaining: number;
}

export interface MFAChallengeRequest {
  challenge_id: string;
  token: string;
}

export interface MFAChallengeResponse {
  success: boolean;
  valid: boolean;
  message?: string;
  attempts_remaining?: number;
  error?: string;
}

// ============================================================================
// MFA Recovery Types
// ============================================================================

export interface MFARecoveryRequest {
  email: string;
  recovery_reason: string;
}

export interface MFARecoveryResponse {
  success: boolean;
  message?: string;
  recovery_id?: string;
  estimated_response_time?: string;
  error?: string;
}

export interface MFARecoveryStatus {
  id: string;
  status: 'pending' | 'under_review' | 'approved' | 'denied';
  created_at: string;
  updated_at: string;
  admin_notes?: string;
}

export interface MFARecoveryStatusResponse {
  success: boolean;
  recovery_status?: MFARecoveryStatus;
  error?: string;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseMFASetupReturn {
  setupData: TOTPSetupResponse['data'] | null;
  isLoading: boolean;
  error: string | null;
  setupTOTP: (request?: TOTPSetupRequest) => Promise<TOTPSetupResponse>;
  confirmTOTP: (token: string) => Promise<TOTPConfirmResponse>;
  clearSetupData: () => void;
  clearError: () => void;
}

export interface UseMFAVerifyReturn {
  isLoading: boolean;
  error: string | null;
  verifyMFA: (token: string) => Promise<MFAVerifyResponse>;
  clearError: () => void;
}

export interface UseMFAStatusReturn {
  mfaStatus: MFAStatus | null;
  isLoading: boolean;
  error: string | null;
  refreshStatus: () => Promise<void>;
  disableMFA: (token: string) => Promise<MFADisableResponse>;
  clearError: () => void;
}

export interface UseBackupCodesReturn {
  backupCodes: string[] | null;
  codesStatus: BackupCodesStats | null;
  recentUsage: Array<{
    code_partial: string;
    used_at: string;
    used_ip: string;
  }> | null;
  recommendations: string[];
  isLoading: boolean;
  error: string | null;
  regenerateCodes: (request?: BackupCodesRegenerateRequest) => Promise<BackupCodesRegenerateResponse>;
  getStatus: () => Promise<void>;
  clearCodes: () => void;
  clearError: () => void;
}

export interface UseTOTPDeviceReturn {
  device: TOTPDevice | null;
  isLoading: boolean;
  error: string | null;
  unlockDevice: () => Promise<UnlockTOTPDeviceResponse>;
  refreshDevice: () => Promise<void>;
  clearError: () => void;
}

export interface UseMFASecurityReturn {
  securityReport: MFASecurityReport | null;
  isLoading: boolean;
  error: string | null;
  refreshReport: () => Promise<void>;
  clearError: () => void;
}

// ============================================================================
// MFA UI State Types
// ============================================================================

export interface MFASetupFlow {
  currentStep: 'setup' | 'scan' | 'verify' | 'backup-codes' | 'complete';
  setupData: TOTPSetupResponse['data'] | null;
  backupCodes: string[] | null;
  isLoading: boolean;
  error: string | null;
}

export interface MFAVerificationFlow {
  isRequired: boolean;
  challengeId?: string;
  challengeType?: 'totp' | 'backup_code';
  attemptsRemaining: number;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Constants
// ============================================================================

export const MFA_SETUP_STEPS = {
  SETUP: 'setup',
  SCAN: 'scan',
  VERIFY: 'verify',
  BACKUP_CODES: 'backup-codes',
  COMPLETE: 'complete',
} as const;

export const MFA_DEVICE_STATUS = {
  PENDING: 'pending',
  ACTIVE: 'active',
  LOCKED: 'locked',
  DISABLED: 'disabled',
} as const;

export const BACKUP_CODE_STATUS = {
  UNUSED: 'unused',
  USED: 'used',
  EXPIRED: 'expired',
  REVOKED: 'revoked',
} as const;

export const MFA_VERIFICATION_METHODS = {
  TOTP: 'totp',
  BACKUP_CODE: 'backup_code',
} as const;

export const MFA_SECURITY_LEVELS = {
  NONE: 0,
  BASIC: 25,
  GOOD: 50,
  STRONG: 75,
  EXCELLENT: 100,
} as const;

export const MFA_CONSTANTS = {
  TOTP_CODE_LENGTH: 6,
  BACKUP_CODE_MIN_LENGTH: 8,
  BACKUP_CODE_MAX_LENGTH: 16,
  DEFAULT_BACKUP_CODES_COUNT: 10,
  LOCKOUT_ATTEMPTS_THRESHOLD: 5,
  GRACE_PERIOD_DAYS: 7,
} as const;

export type MFASetupStep = typeof MFA_SETUP_STEPS[keyof typeof MFA_SETUP_STEPS];
export type MFADeviceStatus = typeof MFA_DEVICE_STATUS[keyof typeof MFA_DEVICE_STATUS];
export type BackupCodeStatus = typeof BACKUP_CODE_STATUS[keyof typeof BACKUP_CODE_STATUS];
export type MFAVerificationMethod = typeof MFA_VERIFICATION_METHODS[keyof typeof MFA_VERIFICATION_METHODS];