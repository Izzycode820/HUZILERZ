/**
 * Phone Service - Enterprise Phone Verification
 * Aligned with backend phone_views.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
    PhoneVerificationRequest,
    PhoneVerificationResponse,
    PhoneVerificationConfirmRequest,
    PhoneVerificationConfirmResponse,
    PhoneChangeRequest,
    PhoneChangeResponse,
    PhoneChangeConfirmRequest,
    PhoneChangeConfirmResponse,
    PhoneVerificationStatusResponse
} from '../../types/authentication/phone'

// ============================================================================
// Phone Service (Matches Backend endpoints exactly)
// ============================================================================

export class PhoneService extends BaseService {
    constructor() {
        super('auth')
    }

    /**
     * Request phone verification code
     * Backend: POST /api/auth/phone/verify-request/
     */
    async requestVerificationCode(data: PhoneVerificationRequest): Promise<PhoneVerificationResponse> {
        this.validateRequired(data as unknown as Record<string, unknown>, ['phone_number'])

        return this.postPublic<PhoneVerificationResponse>('/phone/verify-request/', {
            phone_number: PhoneValidationUtils.normalizePhone(data.phone_number),
            code_type: data.code_type || 'phone_verification'
        })
    }

    /**
     * Verify phone verification code
     * Backend: POST /api/auth/phone/verify-confirm/
     */
    async verifyCode(data: PhoneVerificationConfirmRequest): Promise<PhoneVerificationConfirmResponse> {
        this.validateRequired(data as unknown as Record<string, unknown>, ['phone_number', 'code'])

        return this.postPublic<PhoneVerificationConfirmResponse>('/phone/verify-confirm/', {
            phone_number: PhoneValidationUtils.normalizePhone(data.phone_number),
            code_type: data.code_type || 'phone_verification',
            code: data.code.replace(/\D/g, '') // Remove non-digits
        })
    }

    /**
     * Get phone verification status
     * Backend: GET /api/auth/phone/status/
     */
    async getVerificationStatus(): Promise<PhoneVerificationStatusResponse> {
        return this.get<PhoneVerificationStatusResponse>('/phone/status/')
    }

    /**
     * Request phone number change
     * Backend: POST /api/auth/phone/change-request/
     */
    async requestPhoneChange(data: PhoneChangeRequest): Promise<PhoneChangeResponse> {
        this.validateRequired(data as unknown as Record<string, unknown>, ['new_phone_number'])

        return this.post<PhoneChangeResponse>('/phone/change-request/', {
            new_phone_number: PhoneValidationUtils.normalizePhone(data.new_phone_number)
        })
    }

    /**
     * Confirm phone number change
     * Backend: POST /api/auth/phone/change-confirm/
     */
    async confirmPhoneChange(data: PhoneChangeConfirmRequest): Promise<PhoneChangeConfirmResponse> {
        this.validateRequired(data as unknown as Record<string, unknown>, ['new_phone_number', 'code'])

        return this.post<PhoneChangeConfirmResponse>('/phone/change-confirm/', {
            new_phone_number: PhoneValidationUtils.normalizePhone(data.new_phone_number),
            code: data.code.replace(/\D/g, '') // Remove non-digits
        })
    }
}

// ============================================================================
// Phone Validation Utilities
// ============================================================================

class PhoneValidationUtils {
    /**
     * Validate phone number format (E.164 or basic)
     */
    static isValidPhone(phone: string): boolean {
        const cleaned = phone.replace(/[\s\-\(\)\.]/g, '')
        // E.164 format or basic digits with optional +
        return /^\+?[0-9]{8,15}$/.test(cleaned)
    }

    /**
     * Normalize phone number (remove formatting)
     */
    static normalizePhone(phone: string): string {
        // Remove formatting characters but keep + and digits
        return phone.replace(/[\s\-\(\)\.]/g, '').trim()
    }

    /**
     * Format phone for display (mask middle digits)
     */
    static maskPhone(phone: string): string {
        const cleaned = this.normalizePhone(phone)
        if (cleaned.length < 8) return cleaned

        const start = cleaned.slice(0, 4)
        const end = cleaned.slice(-4)
        return `${start}****${end}`
    }

    /**
     * Validate verification code format (6 digits)
     */
    static isValidVerificationCode(code: string): boolean {
        const cleanCode = code.replace(/\D/g, '')
        return cleanCode.length === 6
    }

    /**
     * Format verification code (remove non-digits)
     */
    static formatVerificationCode(code: string): string {
        return code.replace(/\D/g, '')
    }

    /**
     * Get display name for code type
     */
    static getCodeTypeDisplayName(codeType: string): string {
        const displayNames: Record<string, string> = {
            phone_verification: 'Phone Verification',
            login_verification: 'Login Verification',
            phone_change: 'Phone Change',
            password_reset: 'Password Reset'
        }

        return displayNames[codeType] || codeType
    }

    /**
     * Check if phone looks like Cameroon number
     */
    static isCameroonPhone(phone: string): boolean {
        const cleaned = this.normalizePhone(phone)
        return /^(\+237|237)?[6-9]\d{8}$/.test(cleaned)
    }

    /**
     * Add default country code if missing
     */
    static addDefaultCountryCode(phone: string, countryCode: string = '+237'): string {
        const cleaned = this.normalizePhone(phone)

        if (cleaned.startsWith('+')) {
            return cleaned
        }

        // Remove leading 0 if present
        const withoutLeadingZero = cleaned.startsWith('0') ? cleaned.slice(1) : cleaned

        return `${countryCode}${withoutLeadingZero}`
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
            isExpiringSoon: diffMs <= (2 * 60 * 1000) // 2 minutes for SMS (shorter than email)
        }
    }
}

// ============================================================================
// Phone Security Utilities
// ============================================================================

class PhoneSecurityUtils {
    /**
     * Check for rate limiting indicators
     */
    static checkRateLimit(recentVerifications: { created_at: string }[]): {
        isRateLimited: boolean
        recentCount: number
        maxAllowed: number
        nextAllowedTime?: Date
    } {
        const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
        const recentCount = recentVerifications.filter(
            v => new Date(v.created_at) > oneHourAgo
        ).length

        const maxAllowed = 3 // SMS rate limit (stricter than email)
        const isRateLimited = recentCount >= maxAllowed

        return {
            isRateLimited,
            recentCount,
            maxAllowed,
            nextAllowedTime: isRateLimited
                ? new Date(Date.now() + 60 * 60 * 1000)
                : undefined
        }
    }

    /**
     * Sanitize phone input for security
     */
    static sanitizePhoneInput(phone: string): string {
        return phone
            .trim()
            .replace(/[<>"'\\]/g, '') // Remove dangerous characters
            .replace(/[^\d\+\-\(\)\s\.]/g, '') // Keep only phone chars
            .substring(0, 20) // Reasonable limit
    }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const phoneService = new PhoneService()
export { PhoneValidationUtils, PhoneSecurityUtils }
export default phoneService
