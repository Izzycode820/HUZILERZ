/**
 * Email Service - Enterprise Email Verification
 * Aligned with backend email_views.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
  EmailVerificationRequest,
  EmailVerificationResponse,
  EmailVerificationConfirmRequest as EmailVerificationConfirm,
  PasswordResetRequest,
  PasswordResetConfirmRequest as PasswordResetConfirm,
  PasswordResetResponse,
  EmailChangeRequest,
  EmailChangeConfirmRequest as EmailChangeConfirm,
  EmailChangeResponse,
  EmailVerificationStatus
} from '../../types/authentication/email'

// ============================================================================
// Email Service (Matches Backend endpoints exactly)
// ============================================================================

export class EmailService extends BaseService {
  constructor() {
    super('auth')
  }

  /**
   * Request email verification code
   * Backend: POST /api/auth/email/verify-request/
   */
  async requestVerificationCode(data: EmailVerificationRequest): Promise<EmailVerificationResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['email', 'code_type'])

    return this.postPublic<EmailVerificationResponse>('/email/verify-request/', {
      email: data.email.toLowerCase().trim(),
      code_type: data.code_type
    })
  }

  /**
   * Verify email verification code
   * Backend: POST /api/auth/email/verify-confirm/
   */
  async verifyCode(data: EmailVerificationConfirm): Promise<EmailVerificationResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['email', 'code_type', 'code'])

    return this.postPublic<EmailVerificationResponse>('/email/verify-confirm/', {
      email: data.email.toLowerCase().trim(),
      code_type: data.code_type,
      code: data.code.replace(/\D/g, '') // Remove non-digits
    })
  }

  /**
   * Request password reset
   * Backend: POST /api/auth/password/reset-request/
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<PasswordResetResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['email'])

    return this.postPublic<PasswordResetResponse>('/password/reset-request/', {
      email: data.email.toLowerCase().trim()
    })
  }

  /**
   * Confirm password reset with token
   * Backend: POST /api/auth/password/reset-confirm/
   */
  async confirmPasswordReset(data: PasswordResetConfirm): Promise<PasswordResetResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['token', 'new_password', 'confirm_password'])

    // Validate passwords match
    if (data.new_password !== data.confirm_password) {
      throw new Error('Passwords do not match')
    }

    return this.postPublic<PasswordResetResponse>('/password/reset-confirm/', {
      token: data.token.trim(),
      new_password: data.new_password,
      confirm_password: data.confirm_password
    })
  }

  /**
   * Request email address change
   * Backend: POST /api/auth/email/change-request/
   */
  async requestEmailChange(data: EmailChangeRequest): Promise<EmailChangeResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['new_email'])

    return this.post<EmailChangeResponse>('/email/change-request/', {
      new_email: data.new_email.toLowerCase().trim()
    })
  }

  /**
   * Confirm email address change
   * Backend: POST /api/auth/email/change-confirm/
   */
  async confirmEmailChange(data: EmailChangeConfirm): Promise<EmailChangeResponse> {
    this.validateRequired(data as unknown as Record<string, unknown>, ['new_email', 'code'])

    return this.post<EmailChangeResponse>('/email/change-confirm/', {
      new_email: data.new_email.toLowerCase().trim(),
      code: data.code.replace(/\D/g, '') // Remove non-digits
    })
  }

  /**
   * Get email verification status
   * Backend: GET /api/auth/email/verification-status/
   */
  async getVerificationStatus(): Promise<EmailVerificationStatus> {
    return this.get<EmailVerificationStatus>('/email/verification-status/')
  }

  /**
   * Resend email verification for current user
   * Backend: POST /api/auth/email/resend-verification/
   */
  async resendVerification(): Promise<EmailVerificationResponse> {
    return this.post<EmailVerificationResponse>('/email/resend-verification/')
  }
}

// ============================================================================
// Email Validation Utilities
// ============================================================================

class EmailValidationUtils {
  /**
   * Validate email format
   */
  static isValidEmail(email: string): boolean {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    return emailRegex.test(email.trim())
  }

  /**
   * Normalize email address
   */
  static normalizeEmail(email: string): string {
    return email.toLowerCase().trim()
  }

  /**
   * Validate verification code format
   */
  static isValidVerificationCode(code: string): boolean {
    const cleanCode = code.replace(/\D/g, '')
    return cleanCode.length >= 4 && cleanCode.length <= 8
  }

  /**
   * Format verification code (remove non-digits)
   */
  static formatVerificationCode(code: string): string {
    return code.replace(/\D/g, '')
  }

  /**
   * Check if email domain is allowed
   */
  static isAllowedEmailDomain(email: string): boolean {
    const domain = email.split('@')[1]?.toLowerCase()

    // Block known temporary email domains
    const blockedDomains = [
      '10minutemail.com',
      'tempmail.org',
      'guerrillamail.com',
      'mailinator.com',
      'throwaway.email',
      'example.com',
      'test.com'
    ]

    return !blockedDomains.includes(domain)
  }

  /**
   * Get display name for code type
   */
  static getCodeTypeDisplayName(codeType: string): string {
    const displayNames: Record<string, string> = {
      account_verification: 'Account Verification',
      login_verification: 'Login Verification',
      email_change: 'Email Change',
      password_reset: 'Password Reset'
    }

    return displayNames[codeType] || codeType
  }

  /**
   * Estimate time remaining for code expiration
   */
  static getTimeUntilExpiration(expiresAt: string): {
    minutes: number
    isExpired: boolean
    isExpiringSoon: boolean
  } {
    const now = new Date()
    const expiration = new Date(expiresAt)
    const diffMs = expiration.getTime() - now.getTime()
    const minutes = Math.floor(diffMs / (1000 * 60))

    return {
      minutes: Math.max(0, minutes),
      isExpired: diffMs <= 0,
      isExpiringSoon: diffMs <= (5 * 60 * 1000) // 5 minutes
    }
  }
}

// ============================================================================
// Email Security Utilities
// ============================================================================

class EmailSecurityUtils {
  /**
   * Check for rate limiting indicators
   */
  static checkRateLimit(recentVerifications: any[]): {
    isRateLimited: boolean
    recentCount: number
    maxAllowed: number
    nextAllowedTime?: Date
  } {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000)
    const recentCount = recentVerifications.filter(
      v => new Date(v.created_at) > fiveMinutesAgo
    ).length

    const maxAllowed = 3 // Conservative rate limit
    const isRateLimited = recentCount >= maxAllowed

    return {
      isRateLimited,
      recentCount,
      maxAllowed,
      nextAllowedTime: isRateLimited
        ? new Date(Date.now() + 5 * 60 * 1000)
        : undefined
    }
  }

  /**
   * Sanitize email input for security
   */
  static sanitizeEmailInput(email: string): string {
    return email
      .trim()
      .toLowerCase()
      .replace(/[<>\"'/\\]/g, '') // Remove dangerous characters
      .substring(0, 254) // RFC limit
  }

  /**
   * Validate password strength for reset
   */
  static validatePasswordStrength(password: string): {
    isValid: boolean
    errors: string[]
    score: number
  } {
    const errors: string[] = []
    let score = 0

    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long')
    } else {
      score += 1
    }

    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter')
    } else {
      score += 1
    }

    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter')
    } else {
      score += 1
    }

    if (!/\d/.test(password)) {
      errors.push('Password must contain at least one number')
    } else {
      score += 1
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain at least one special character')
    } else {
      score += 1
    }

    return {
      isValid: errors.length === 0,
      errors,
      score
    }
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const emailService = new EmailService()
export { EmailValidationUtils, EmailSecurityUtils }
export default emailService