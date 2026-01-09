/**
 * Phone Authentication and Verification Types
 * Based on backend SMSService and phone verification patterns
 * Follows email.ts pattern for consistency
 */

// ============================================================================
// Phone Verification Types
// ============================================================================

export interface PhoneVerificationRequest {
    phone_number: string;
    code_type: 'phone_verification' | 'login_verification' | 'password_reset' | 'phone_change';
}

export interface PhoneVerificationResponse {
    success: boolean;
    message?: string;
    verification_id?: string;
    expires_in_minutes?: number;
    code_type?: string;
    rate_limited?: boolean;
    cooldown_until?: string;
    error_code?: string;
}

export interface PhoneVerificationConfirmRequest {
    phone_number: string;
    code_type: string;
    code: string;
}

export interface PhoneVerificationConfirmResponse {
    success: boolean;
    message?: string;
    verification_id?: string;
    user_id?: string;
    errors?: Record<string, string[]>;
}

// ============================================================================
// Phone Change Types
// ============================================================================

export interface PhoneChangeRequest {
    new_phone_number: string;
}

export interface PhoneChangeResponse {
    success: boolean;
    message?: string;
    verification_id?: string;
    expires_in_minutes?: number;
    rate_limited?: boolean;
    cooldown_until?: string;
}

export interface PhoneChangeConfirmRequest {
    new_phone_number: string;
    code: string;
}

export interface PhoneChangeConfirmResponse {
    success: boolean;
    message?: string;
    phone_number?: string;
    errors?: Record<string, string[]>;
}

// ============================================================================
// Phone Verification Status Types
// ============================================================================

export interface PhoneVerificationStatus {
    phone_verified: boolean;
    phone_number: string | null;
    has_pending_verification: boolean;
    pending_expires_at?: string;
    rate_limit?: PhoneRateLimitInfo;
}

export interface PhoneVerificationStatusResponse {
    success: boolean;
    message?: string;
    phone_verified?: boolean;
    phone_number?: string | null;
    has_pending_verification?: boolean;
    pending_expires_at?: string;
    rate_limit?: PhoneRateLimitInfo;
    error?: string;
}

// ============================================================================
// Rate Limiting Types
// ============================================================================

export interface PhoneRateLimitInfo {
    is_limited: boolean;
    remaining_attempts: number;
    cooldown_until: string | null;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UsePhoneVerificationReturn {
    isLoading: boolean;
    error: string | null;
    cooldownUntil: string | null;
    requestVerification: (request: PhoneVerificationRequest) => Promise<PhoneVerificationResponse>;
    confirmVerification: (request: PhoneVerificationConfirmRequest) => Promise<PhoneVerificationConfirmResponse>;
    getStatus: () => Promise<PhoneVerificationStatusResponse>;
    clearError: () => void;
}

export interface UsePhoneChangeReturn {
    isLoading: boolean;
    error: string | null;
    changeRequested: boolean;
    pendingPhone: string | null;
    requestChange: (newPhone: string) => Promise<PhoneChangeResponse>;
    confirmChange: (request: PhoneChangeConfirmRequest) => Promise<PhoneChangeConfirmResponse>;
    clearError: () => void;
    clearState: () => void;
}

// ============================================================================
// Phone UI State Types
// ============================================================================

export interface PhoneVerificationFlow {
    currentStep: 'request' | 'verify' | 'success' | 'error';
    phoneNumber: string | null;
    codeType: string | null;
    verificationId: string | null;
    expiresAt: string | null;
    attemptsRemaining: number;
    isLoading: boolean;
    error: string | null;
}

export interface PhoneChangeFlow {
    currentStep: 'request' | 'verify' | 'success' | 'error';
    oldPhone: string | null;
    newPhone: string | null;
    verificationId: string | null;
    isLoading: boolean;
    error: string | null;
}

// ============================================================================
// Constants
// ============================================================================

export const PHONE_CODE_TYPES = {
    PHONE_VERIFICATION: 'phone_verification',
    LOGIN_VERIFICATION: 'login_verification',
    PASSWORD_RESET: 'password_reset',
    PHONE_CHANGE: 'phone_change',
} as const;

export const PHONE_VERIFICATION_STATUS = {
    PENDING: 'pending',
    VERIFIED: 'verified',
    EXPIRED: 'expired',
    REVOKED: 'revoked',
} as const;

export const PHONE_CONSTANTS = {
    CODE_LENGTH: 6,
    CODE_EXPIRY_MINUTES: 10,
    MAX_CODES_PER_HOUR: 3,
    RESEND_COOLDOWN_MINUTES: 1,
    MAX_VERIFICATION_ATTEMPTS: 3,
} as const;

export const PHONE_VALIDATION_PATTERNS = {
    // E.164 format: +[country code][number]
    E164_REGEX: /^\+[1-9]\d{6,14}$/,
    // Basic phone format (digits, spaces, dashes, parens)
    BASIC_REGEX: /^[\d\s\-\(\)\+]+$/,
    // Cameroon specific
    CAMEROON_REGEX: /^(\+237|237)?[6-9]\d{8}$/,
} as const;

export const PHONE_ERRORS = {
    INVALID_PHONE: 'INVALID_PHONE',
    PHONE_ALREADY_EXISTS: 'PHONE_ALREADY_EXISTS',
    PHONE_NOT_FOUND: 'PHONE_NOT_FOUND',
    CODE_EXPIRED: 'CODE_EXPIRED',
    CODE_INVALID: 'CODE_INVALID',
    CODE_REVOKED: 'CODE_REVOKED',
    RATE_LIMITED: 'RATE_LIMITED',
    SMS_DELIVERY_FAILED: 'SMS_DELIVERY_FAILED',
    SERVICE_NOT_CONFIGURED: 'SERVICE_NOT_CONFIGURED',
} as const;

export type PhoneCodeType = typeof PHONE_CODE_TYPES[keyof typeof PHONE_CODE_TYPES];
export type PhoneVerificationStatusType = typeof PHONE_VERIFICATION_STATUS[keyof typeof PHONE_VERIFICATION_STATUS];
export type PhoneErrorCode = typeof PHONE_ERRORS[keyof typeof PHONE_ERRORS];
