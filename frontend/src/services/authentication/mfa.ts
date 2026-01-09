/**
 * Multi-Factor Authentication Service - Enterprise MFA Management
 * Aligned with backend mfa_views.py endpoints
 */

import BaseService from '../base/BaseService'
import { apiClient } from '../api/client'
import type {
  MFAStatus,
  MFAStatusResponse,
  TOTPSetupResponse,
  TOTPConfirmResponse,
  MFAVerifyResponse,
  BackupCodesRegenerateResponse as BackupCodesResponse,
  MFAChallengeResponse
} from '../../types/authentication/mfa'

// ============================================================================
// MFA Service (Matches Backend endpoints exactly)
// ============================================================================

export class MFAService extends BaseService {
  constructor() {
    super('auth')
  }

  /**
   * Get current MFA status
   * Backend: GET /api/auth/mfa/status/
   */
  async getStatus(): Promise<MFAStatus> {
    const response = await this.get<MFAStatusResponse>('/mfa/status/')
    return response.data || {} as MFAStatus
  }

  /**
   * Setup TOTP authentication
   * Backend: POST /api/auth/mfa/totp/setup/
   */
  async setupTOTP(deviceName?: string): Promise<TOTPSetupResponse> {
    const data = this.cleanData({ device_name: deviceName })
    return this.post('/mfa/totp/setup/', data)
  }

  /**
   * Start TOTP setup (alias for setupTOTP)
   */
  async startTOTPSetup(deviceName?: string): Promise<TOTPSetupResponse> {
    return this.setupTOTP(deviceName)
  }

  /**
   * Confirm TOTP setup
   * Backend: POST /api/auth/mfa/totp/confirm/
   */
  async confirmTOTP(token: string): Promise<TOTPConfirmResponse> {
    this.validateRequired({ token }, ['token'])

    // Clean and validate token format
    const cleanToken = token.replace(/\D/g, '') // Remove non-digits
    if (cleanToken.length !== 6) {
      throw new Error('TOTP token must be exactly 6 digits')
    }

    return this.post('/mfa/totp/confirm/', { token: cleanToken })
  }

  /**
   * Confirm TOTP setup (alias for confirmTOTP)
   */
  async confirmTOTPSetup(token: string): Promise<TOTPConfirmResponse> {
    return this.confirmTOTP(token)
  }

  /**
   * Verify MFA token for authentication
   * Backend: POST /api/auth/mfa/verify/
   */
  async verifyToken(token: string): Promise<MFAVerifyResponse> {
    this.validateRequired({ token }, ['token'])

    // Clean token (works for both TOTP and backup codes)
    const cleanToken = token.replace(/\s|-/g, '').toUpperCase()

    return this.post('/mfa/verify/', { token: cleanToken })
  }

  /**
   * Generate new backup codes
   * Backend: POST /api/auth/mfa/backup-codes/regenerate/
   */
  async regenerateBackupCodes(currentMfaToken?: string): Promise<BackupCodesResponse> {
    const data = this.cleanData({
      current_mfa_token: currentMfaToken,
      count: 10
    })
    return this.post('/mfa/backup-codes/regenerate/', data)
  }

  /**
   * Disable MFA
   * Backend: POST /api/auth/mfa/disable/
   */
  async disableMFA(password: string): Promise<MFAVerifyResponse> {
    this.validateRequired({ password }, ['password'])
    return this.post('/mfa/disable/', { password })
  }

  /**
   * Verify challenge during login
   */
  async verifyChallenge(challengeToken: string, mfaToken: string): Promise<MFAChallengeResponse> {
    return mfaChallengeService.verifyChallenge({
      challenge_token: challengeToken,
      mfa_token: mfaToken
    })
  }

  /**
   * Test TOTP code for validation
   */
  async testTOTPCode(token: string): Promise<{ valid: boolean }> {
    try {
      await this.verifyToken(token)
      return { valid: true }
    } catch {
      return { valid: false }
    }
  }


}

// ============================================================================
// MFA Authentication Challenge Service
// ============================================================================

export class MFAChallengeService extends BaseService {
  constructor() {
    super('auth')
  }

  /**
   * Verify MFA challenge during login
   * Backend: POST /api/auth/mfa/challenge/verify/
   */
  async verifyChallenge({
    challenge_token,
    mfa_token
  }: {
    challenge_token: string
    mfa_token: string
  }): Promise<MFAChallengeResponse> {
    this.validateRequired({ challenge_token, mfa_token }, ['challenge_token', 'mfa_token'])

    // Clean MFA token (works for both TOTP and backup codes)
    const cleanMfaToken = mfa_token.replace(/\s|-/g, '').toUpperCase()

    const data = {
      challenge_token,
      mfa_token: cleanMfaToken
    }

    const response = await this.postPublic<MFAChallengeResponse>('/mfa/challenge/verify/', data)

    // Store token after successful MFA verification (if available)
    // Note: MFAChallengeResponse may not always contain token data
    if (response.success && 'access_token' in response) {
      const tokenResponse = response as any
      apiClient.setAuthToken(tokenResponse.access_token, tokenResponse.expires_in)
    }

    return response
  }
}



// ============================================================================
// MFA Utilities
// ============================================================================

export class MFAUtils {
  /**
   * Validate TOTP token format
   */
  static isValidTOTPToken(token: string): boolean {
    const cleaned = token.replace(/\D/g, '')
    return cleaned.length === 6
  }

  /**
   * Validate TOTP code format (alias)
   */
  static isValidTOTPCode(token: string): boolean {
    return this.isValidTOTPToken(token)
  }

  /**
   * Validate backup code format
   */
  static isValidBackupCode(code: string): boolean {
    const cleaned = code.replace(/\s|-/g, '').toUpperCase()
    return cleaned.length >= 8 && cleaned.length <= 16
  }

  /**
   * Format TOTP token for display (XXX XXX)
   */
  static formatTOTPToken(token: string): string {
    const cleaned = token.replace(/\D/g, '')
    if (cleaned.length === 6) {
      return `${cleaned.slice(0, 3)} ${cleaned.slice(3)}`
    }
    return cleaned
  }

  /**
   * Format backup code for display (XXXX-XXXX-XXXX)
   */
  static formatBackupCode(code: string): string {
    const cleaned = code.replace(/\s|-/g, '').toUpperCase()
    if (cleaned.length >= 8) {
      const groups = cleaned.match(/.{1,4}/g) || []
      return groups.join('-')
    }
    return cleaned
  }

  /**
   * Determine if token is TOTP or backup code
   */
  static getTokenType(token: string): 'totp' | 'backup' | 'unknown' {
    const cleaned = token.replace(/\s|-/g, '')

    if (/^\d{6}$/.test(cleaned)) {
      return 'totp'
    }

    if (/^[A-Z0-9]{8,16}$/i.test(cleaned)) {
      return 'backup'
    }

    return 'unknown'
  }

  /**
   * Get QR code data URI for TOTP setup
   */
  static generateQRCodeURL(qrCodeData: string): string {
    // This would typically be handled by the backend
    return qrCodeData
  }

  /**
   * Generate QR code (alias)
   */
  static generateQRCode(secret: string, email: string, issuer: string = 'Huzilerz'): string {
    return `otpauth://totp/${issuer}:${email}?secret=${secret}&issuer=${issuer}`
  }

  /**
   * Check if device is locked (placeholder)
   */
  static isDeviceLocked(): boolean {
    return false
  }

  /**
   * Get time until unlock (placeholder)
   */
  static getTimeUntilUnlock(): number {
    return 0
  }

  /**
   * Calculate MFA security score
   */
  static calculateMFASecurityScore(status: MFAStatus): {
    score: number
    level: 'none' | 'basic' | 'good' | 'excellent'
    recommendations: string[]
  } {
    let score = 0
    const recommendations: string[] = []

    if (!status.mfa_enabled) {
      recommendations.push('Enable MFA for better security')
      return { score: 0, level: 'none', recommendations }
    }

    if (status.totp_device?.is_active) {
      score += 70
    } else {
      recommendations.push('Set up authenticator app')
    }

    if (status.backup_codes.unused > 0) {
      score += 20
    } else {
      recommendations.push('Generate backup codes')
    }

    if (status.backup_codes.unused >= 5) {
      score += 10
    } else if (status.backup_codes.unused > 0) {
      recommendations.push('Consider generating more backup codes')
    }

    let level: 'none' | 'basic' | 'good' | 'excellent'
    if (score >= 90) level = 'excellent'
    else if (score >= 70) level = 'good'
    else if (score >= 40) level = 'basic'
    else level = 'none'

    return { score, level, recommendations }
  }
}

// ============================================================================
// Export Service Instances
// ============================================================================

const mfaService = new MFAService()
const mfaChallengeService = new MFAChallengeService()

export { mfaChallengeService }
export default mfaService