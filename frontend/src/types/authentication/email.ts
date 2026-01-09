/**
 * Email Authentication and Verification Types
 * Based on backend EmailService and email verification patterns
 */

// ============================================================================
// Email Verification Types
// ============================================================================

export interface EmailVerificationRequest {
  email: string;
  code_type: 'account_verification' | 'login_verification' | 'email_change' | 'password_reset';
}

export interface EmailVerificationResponse {
  success: boolean;
  message?: string;
  data?: {
    verification_id: string;
    expires_in_minutes: number;
    code_type: string;
  };
  cooldown_until?: string;
  error?: string;
}

export interface EmailVerificationConfirmRequest {
  email: string;
  code_type: string;
  code: string;
}

export interface EmailVerificationConfirmResponse {
  success: boolean;
  message?: string;
  data?: {
    verification_id: string;
    user_id?: string;
    email_verified: boolean;
  };
  error?: string;
}

// ============================================================================
// Password Reset Types
// ============================================================================

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetResponse {
  success: boolean;
  message: string;
  error?: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetConfirmResponse {
  success: boolean;
  message?: string;
  data?: {
    password_reset: boolean;
    user_id?: string;
  };
  error?: string;
  errors?: Record<string, string[]>;
}

// ============================================================================
// Email Change Types
// ============================================================================

export interface EmailChangeRequest {
  new_email: string;
}

export interface EmailChangeResponse {
  success: boolean;
  message?: string;
  data?: {
    verification_id: string;
    new_email: string;
    expires_in_minutes: number;
  };
  error?: string;
}

export interface EmailChangeConfirmRequest {
  new_email: string;
  code: string;
}

export interface EmailChangeConfirmResponse {
  success: boolean;
  message?: string;
  data?: {
    new_email: string;
    old_email: string;
  };
  error?: string;
}

// ============================================================================
// Email Verification Status Types
// ============================================================================

export interface EmailVerificationCode {
  id: string;
  code_type: string;
  code_type_display: string;
  status: 'pending' | 'verified' | 'expired' | 'failed';
  created_at: string;
  expires_at: string;
  verified_at?: string;
}

export interface EmailVerificationStatus {
  user_email: string;
  is_email_verified: boolean;
  recent_verifications: EmailVerificationCode[];
}

export interface EmailVerificationStatusResponse {
  success: boolean;
  data?: EmailVerificationStatus;
  error?: string;
}

// ============================================================================
// Email Resend Types
// ============================================================================

export interface ResendVerificationRequest {
  email: string;
  code_type: string;
}

export interface ResendVerificationResponse {
  success: boolean;
  message?: string;
  data?: {
    verification_id: string;
    expires_in_minutes: number;
  };
  error?: string;
}

// ============================================================================
// Rate Limiting Types
// ============================================================================

export interface EmailRateLimitInfo {
  is_rate_limited: boolean;
  recent_codes: number;
  max_codes: number;
  time_window_minutes: number;
  cooldown_until?: string;
}

export interface EmailRateLimitResponse {
  success: boolean;
  rate_limit_info?: EmailRateLimitInfo;
  error?: string;
}

// ============================================================================
// Email Security Stats Types
// ============================================================================

export interface EmailSecurityStats {
  total_codes_sent: number;
  successful_verifications: number;
  failed_attempts: number;
  expired_codes: number;
  rate_limited_requests: number;
}

export interface EmailSecurityStatsResponse {
  success: boolean;
  stats?: EmailSecurityStats;
  error?: string;
}

// ============================================================================
// Email Template Types
// ============================================================================

export interface EmailTemplate {
  template_type: 'verification' | 'password_reset' | 'email_change' | 'security_alert';
  subject: string;
  body_text: string;
  body_html: string;
  variables: Record<string, string>;
}

export interface EmailPreviewRequest {
  template_type: string;
  variables?: Record<string, string>;
}

export interface EmailPreviewResponse {
  success: boolean;
  preview?: {
    subject: string;
    body_html: string;
    body_text: string;
  };
  error?: string;
}

// ============================================================================
// Email Validation Types
// ============================================================================

export interface EmailValidationResult {
  is_valid: boolean;
  is_disposable: boolean;
  is_business: boolean;
  domain_info: {
    domain: string;
    mx_records: boolean;
    smtp_valid: boolean;
  };
  suggestions?: string[];
  error?: string;
}

export interface EmailValidationResponse {
  success: boolean;
  validation?: EmailValidationResult;
  error?: string;
}

// ============================================================================
// Email Delivery Types
// ============================================================================

export interface EmailDeliveryStatus {
  message_id: string;
  status: 'queued' | 'sent' | 'delivered' | 'failed' | 'bounced';
  sent_at?: string;
  delivered_at?: string;
  failed_reason?: string;
  bounce_type?: 'hard' | 'soft';
}

export interface EmailDeliveryResponse {
  success: boolean;
  delivery_status?: EmailDeliveryStatus;
  error?: string;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseEmailVerificationReturn {
  isLoading: boolean;
  error: string | null;
  cooldownUntil: string | null;
  requestVerification: (request: EmailVerificationRequest) => Promise<EmailVerificationResponse>;
  confirmVerification: (request: EmailVerificationConfirmRequest) => Promise<EmailVerificationConfirmResponse>;
  resendCode: (request: ResendVerificationRequest) => Promise<ResendVerificationResponse>;
  getStatus: () => Promise<EmailVerificationStatusResponse>;
  clearError: () => void;
}

export interface UsePasswordResetReturn {
  isLoading: boolean;
  error: string | null;
  resetRequested: boolean;
  requestReset: (email: string) => Promise<PasswordResetResponse>;
  confirmReset: (request: PasswordResetConfirmRequest) => Promise<PasswordResetConfirmResponse>;
  clearError: () => void;
  clearState: () => void;
}

export interface UseEmailChangeReturn {
  isLoading: boolean;
  error: string | null;
  changeRequested: boolean;
  pendingEmail: string | null;
  requestChange: (newEmail: string) => Promise<EmailChangeResponse>;
  confirmChange: (request: EmailChangeConfirmRequest) => Promise<EmailChangeConfirmResponse>;
  clearError: () => void;
  clearState: () => void;
}

export interface UseEmailValidationReturn {
  isLoading: boolean;
  error: string | null;
  validationResult: EmailValidationResult | null;
  validateEmail: (email: string) => Promise<EmailValidationResponse>;
  clearValidation: () => void;
  clearError: () => void;
}

// ============================================================================
// Email UI State Types
// ============================================================================

export interface EmailVerificationFlow {
  currentStep: 'request' | 'verify' | 'success' | 'error';
  email: string | null;
  codeType: string | null;
  verificationId: string | null;
  expiresAt: string | null;
  attemptsRemaining: number;
  isLoading: boolean;
  error: string | null;
}

export interface PasswordResetFlow {
  currentStep: 'request' | 'confirm' | 'success' | 'error';
  email: string | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface EmailChangeFlow {
  currentStep: 'request' | 'verify' | 'success' | 'error';
  oldEmail: string | null;
  newEmail: string | null;
  verificationId: string | null;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Constants
// ============================================================================

export const EMAIL_CODE_TYPES = {
  ACCOUNT_VERIFICATION: 'account_verification',
  LOGIN_VERIFICATION: 'login_verification',
  EMAIL_CHANGE: 'email_change',
  PASSWORD_RESET: 'password_reset',
} as const;

export const EMAIL_VERIFICATION_STATUS = {
  PENDING: 'pending',
  VERIFIED: 'verified',
  EXPIRED: 'expired',
  FAILED: 'failed',
} as const;

export const EMAIL_DELIVERY_STATUS = {
  QUEUED: 'queued',
  SENT: 'sent',
  DELIVERED: 'delivered',
  FAILED: 'failed',
  BOUNCED: 'bounced',
} as const;

export const EMAIL_TEMPLATE_TYPES = {
  VERIFICATION: 'verification',
  PASSWORD_RESET: 'password_reset',
  EMAIL_CHANGE: 'email_change',
  SECURITY_ALERT: 'security_alert',
} as const;

export const EMAIL_CONSTANTS = {
  CODE_LENGTH: 6,
  CODE_EXPIRY_MINUTES: 15,
  MAX_CODES_PER_HOUR: 5,
  RESEND_COOLDOWN_MINUTES: 1,
  MAX_VERIFICATION_ATTEMPTS: 3,
} as const;

export const EMAIL_VALIDATION_PATTERNS = {
  EMAIL_REGEX: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  DISPOSABLE_DOMAINS: [
    '10minutemail.com',
    'tempmail.org',
    'guerrillamail.com',
    'mailinator.com',
    'throwaway.email',
  ],
} as const;

export const EMAIL_ERRORS = {
  INVALID_EMAIL: 'INVALID_EMAIL',
  EMAIL_ALREADY_EXISTS: 'EMAIL_ALREADY_EXISTS',
  EMAIL_NOT_FOUND: 'EMAIL_NOT_FOUND',
  CODE_EXPIRED: 'CODE_EXPIRED',
  CODE_INVALID: 'CODE_INVALID',
  CODE_ALREADY_USED: 'CODE_ALREADY_USED',
  RATE_LIMITED: 'RATE_LIMITED',
  DISPOSABLE_EMAIL: 'DISPOSABLE_EMAIL',
  DELIVERY_FAILED: 'DELIVERY_FAILED',
} as const;

export type EmailCodeType = typeof EMAIL_CODE_TYPES[keyof typeof EMAIL_CODE_TYPES];
export type EmailVerificationStatusType = typeof EMAIL_VERIFICATION_STATUS[keyof typeof EMAIL_VERIFICATION_STATUS];
export type EmailDeliveryStatusType = typeof EMAIL_DELIVERY_STATUS[keyof typeof EMAIL_DELIVERY_STATUS];
export type EmailTemplateType = typeof EMAIL_TEMPLATE_TYPES[keyof typeof EMAIL_TEMPLATE_TYPES];
export type EmailErrorCode = typeof EMAIL_ERRORS[keyof typeof EMAIL_ERRORS];