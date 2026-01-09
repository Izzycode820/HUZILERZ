/**
 * Sessions Service - Enterprise Session Management
 * Aligned with backend session_views.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
  UserSession,
  SessionsResponse,
  RevokeSessionResponse as SessionActionResponse
} from '../../types/authentication/user'

// ============================================================================
// Sessions Service (Matches Backend endpoints exactly)
// ============================================================================

export class SessionsService extends BaseService {
  constructor() {
    super('auth')
  }

  /**
   * Get active user sessions
   * Backend: GET /api/auth/sessions/
   */
  async getActiveSessions(): Promise<UserSession[]> {
    const response = await this.get<SessionsResponse>('/sessions/')
    return response.sessions || []
  }

  /**
   * Revoke a specific session
   * Backend: DELETE /api/auth/sessions/{session_id}/
   */
  async revokeSession(sessionId: string): Promise<SessionActionResponse> {
    this.validateRequired({ sessionId }, ['sessionId'])
    return this.delete<SessionActionResponse>(`/sessions/${sessionId}/`)
  }

  /**
   * Revoke all other sessions (keep current)
   * Backend: POST /api/auth/sessions/revoke-all/
   */
  async revokeAllOtherSessions(): Promise<SessionActionResponse> {
    return this.post<SessionActionResponse>('/sessions/revoke-all/')
  }
}

// ============================================================================
// Session Utilities
// ============================================================================

export class SessionUtils {
  /**
   * Format device information for display
   */
  static formatDeviceInfo(session: UserSession): string {
    const parts = []

    if (session.device_name) {
      parts.push(session.device_name)
    }

    if (session.ip_address) {
      parts.push(`IP: ${session.ip_address}`)
    }

    return parts.join(' • ') || 'Unknown Device'
  }

  /**
   * Format last activity time
   */
  static formatLastActivity(timestamp: string): string {
    const now = new Date()
    const activityTime = new Date(timestamp)
    const diffMs = now.getTime() - activityTime.getTime()

    const minutes = Math.floor(diffMs / (1000 * 60))
    const hours = Math.floor(diffMs / (1000 * 60 * 60))
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`
    if (days < 7) return `${days} day${days !== 1 ? 's' : ''} ago`

    return activityTime.toLocaleDateString()
  }

  /**
   * Check if session is recent (within last 24 hours)
   */
  static isRecentSession(session: UserSession): boolean {
    const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000)
    const sessionTime = new Date(session.last_used).getTime()
    return sessionTime > oneDayAgo
  }

  /**
   * Group sessions by activity (current, recent, older)
   */
  static groupSessionsByActivity(sessions: UserSession[]): {
    current: UserSession | null
    recent: UserSession[]
    older: UserSession[]
  } {
    const current = sessions.find(s => s.is_current) || null
    const others = sessions.filter(s => !s.is_current)

    const recent: UserSession[] = []
    const older: UserSession[] = []

    others.forEach(session => {
      if (SessionUtils.isRecentSession(session)) {
        recent.push(session)
      } else {
        older.push(session)
      }
    })

    return { current, recent, older }
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const sessionsService = new SessionsService()
export default sessionsService