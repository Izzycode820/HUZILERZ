/**
 * User Security Store - Personal Account Security
 * Manages user's personal security events, sessions, and security settings
 * (NOT system-wide admin security)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  UserSession,
  AccountSecurityInfo,
  UserActivity,
} from '../../types/authentication/user'
import type {
  UserSecurityEvent,
} from '../../types/authentication/security'

// ============================================================================
// Store State Interface
// ============================================================================

interface UserSecurityStoreState {
  // Personal Security Info
  securityInfo: AccountSecurityInfo | null

  // Active Sessions
  activeSessions: UserSession[]

  // Recent Security Events (for this user only)
  recentSecurityEvents: UserSecurityEvent[]

  // Activity Log (for this user only)
  recentActivity: UserActivity[]

  // Security Alerts (personal)
  personalAlerts: Array<{
    id: string
    type: 'suspicious_login' | 'new_device' | 'password_weak' | 'mfa_disabled' | 'security_recommendation'
    title: string
    message: string
    severity: 'low' | 'medium' | 'high'
    created_at: string
    is_read: boolean
    action_required: boolean
    action_url?: string
  }>

  // Security Settings
  securitySettings: {
    email_notifications: boolean
    sms_notifications: boolean
    push_notifications: boolean
    security_alerts: boolean
    login_notifications: boolean
    device_notifications: boolean
  }

  // Loading States
  isLoading: boolean
  isLoadingSessions: boolean
  isLoadingActivity: boolean
  error: string | null

  // Last Update
  lastUpdate: number
}

interface UserSecurityStoreActions {
  // Security Info Management
  setSecurityInfo: (info: AccountSecurityInfo) => void
  refreshSecurityInfo: () => Promise<void>

  // Sessions Management
  setSessions: (sessions: UserSession[]) => void
  removeSession: (sessionId: string) => void
  refreshSessions: () => Promise<void>

  // Security Events Management
  setSecurityEvents: (events: UserSecurityEvent[]) => void
  addSecurityEvent: (event: UserSecurityEvent) => void
  markSecurityEventRead: (eventId: string) => void

  // Activity Management
  setActivity: (activities: UserActivity[]) => void
  addActivity: (activity: UserActivity) => void

  // Personal Alerts Management
  setPersonalAlerts: (alerts: UserSecurityStoreState['personalAlerts']) => void
  addPersonalAlert: (alert: Omit<UserSecurityStoreState['personalAlerts'][0], 'id' | 'created_at' | 'is_read'>) => void
  markAlertRead: (alertId: string) => void
  dismissAlert: (alertId: string) => void

  // Security Settings
  setSecuritySettings: (settings: Partial<UserSecurityStoreState['securitySettings']>) => void
  updateSecuritySetting: (key: keyof UserSecurityStoreState['securitySettings'], value: boolean) => void

  // Loading and Error States
  setLoading: (loading: boolean) => void
  setLoadingSessions: (loading: boolean) => void
  setLoadingActivity: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void

  // Utilities
  getUnreadAlertsCount: () => number
  getHighPriorityAlertsCount: () => number
  hasRecentSuspiciousActivity: () => boolean
  getSecurityRecommendations: () => Array<{
    type: string
    message: string
    priority: 'low' | 'medium' | 'high'
    action: string
  }>

  // Reset
  reset: () => void
}

export type UserSecurityStore = UserSecurityStoreState & UserSecurityStoreActions

// ============================================================================
// Initial State
// ============================================================================

const initialSecuritySettings = {
  email_notifications: true,
  sms_notifications: false,
  push_notifications: true,
  security_alerts: true,
  login_notifications: true,
  device_notifications: true,
}

const initialState: UserSecurityStoreState = {
  securityInfo: null,
  activeSessions: [],
  recentSecurityEvents: [],
  recentActivity: [],
  personalAlerts: [],
  securitySettings: initialSecuritySettings,
  isLoading: false,
  isLoadingSessions: false,
  isLoadingActivity: false,
  error: null,
  lastUpdate: Date.now(),
}

// ============================================================================
// Zustand Store
// ============================================================================

export const useUserSecurityStore = create<UserSecurityStore>()(
  persist(
    (set, get) => ({
      // Initial State
      ...initialState,

      // ========================================================================
      // Security Info Management
      // ========================================================================

      setSecurityInfo: (info) => {
        set({
          securityInfo: info,
          lastUpdate: Date.now(),
        })
      },

      refreshSecurityInfo: async () => {
        // This will be implemented by services layer
        set({ isLoading: true })
        // The actual API call will be in the service layer
      },

      // ========================================================================
      // Sessions Management
      // ========================================================================

      setSessions: (sessions) => {
        set({
          activeSessions: sessions,
          isLoadingSessions: false,
          lastUpdate: Date.now(),
        })
      },

      removeSession: (sessionId) => {
        const current = get().activeSessions
        set({
          activeSessions: current.filter(session => session.id !== sessionId),
          lastUpdate: Date.now(),
        })
      },

      refreshSessions: async () => {
        set({ isLoadingSessions: true })
        // The actual API call will be in the service layer
      },

      // ========================================================================
      // Security Events Management
      // ========================================================================

      setSecurityEvents: (events) => {
        set({
          recentSecurityEvents: events,
          lastUpdate: Date.now(),
        })
      },

      addSecurityEvent: (event) => {
        const current = get().recentSecurityEvents
        set({
          recentSecurityEvents: [event, ...current].slice(0, 50), // Keep last 50 events
          lastUpdate: Date.now(),
        })

        // Auto-create alerts for high-risk events
        if (event.risk_level >= 3) { // HIGH or CRITICAL (3-4)
          get().addPersonalAlert({
            type: 'suspicious_login',
            title: 'Security Alert',
            message: event.description,
            severity: event.risk_level === 4 ? 'high' : 'medium',
            action_required: true,
          })
        }
      },

      markSecurityEventRead: (eventId) => {
        const current = get().recentSecurityEvents
        set({
          recentSecurityEvents: current.map(event =>
            event.id === eventId ? { ...event, is_processed: true } : event
          ),
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Activity Management
      // ========================================================================

      setActivity: (activities) => {
        set({
          recentActivity: activities,
          isLoadingActivity: false,
          lastUpdate: Date.now(),
        })
      },

      addActivity: (activity) => {
        const current = get().recentActivity
        set({
          recentActivity: [activity, ...current].slice(0, 100), // Keep last 100 activities
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Personal Alerts Management
      // ========================================================================

      setPersonalAlerts: (alerts) => {
        set({
          personalAlerts: alerts,
          lastUpdate: Date.now(),
        })
      },

      addPersonalAlert: (alertData) => {
        const alert = {
          id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          created_at: new Date().toISOString(),
          is_read: false,
          ...alertData,
        }

        const current = get().personalAlerts
        set({
          personalAlerts: [alert, ...current],
          lastUpdate: Date.now(),
        })
      },

      markAlertRead: (alertId) => {
        const current = get().personalAlerts
        set({
          personalAlerts: current.map(alert =>
            alert.id === alertId ? { ...alert, is_read: true } : alert
          ),
          lastUpdate: Date.now(),
        })
      },

      dismissAlert: (alertId) => {
        const current = get().personalAlerts
        set({
          personalAlerts: current.filter(alert => alert.id !== alertId),
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Security Settings
      // ========================================================================

      setSecuritySettings: (settings) => {
        const current = get().securitySettings
        set({
          securitySettings: { ...current, ...settings },
          lastUpdate: Date.now(),
        })
      },

      updateSecuritySetting: (key, value) => {
        const current = get().securitySettings
        set({
          securitySettings: { ...current, [key]: value },
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Loading and Error States
      // ========================================================================

      setLoading: (loading) => {
        set({
          isLoading: loading,
          lastUpdate: Date.now(),
        })
      },

      setLoadingSessions: (loading) => {
        set({
          isLoadingSessions: loading,
          lastUpdate: Date.now(),
        })
      },

      setLoadingActivity: (loading) => {
        set({
          isLoadingActivity: loading,
          lastUpdate: Date.now(),
        })
      },

      setError: (error) => {
        set({
          error,
          isLoading: false,
          isLoadingSessions: false,
          isLoadingActivity: false,
          lastUpdate: Date.now(),
        })
      },

      clearError: () => {
        set({
          error: null,
          lastUpdate: Date.now(),
        })
      },

      // ========================================================================
      // Utilities
      // ========================================================================

      getUnreadAlertsCount: () => {
        return get().personalAlerts.filter(alert => !alert.is_read).length
      },

      getHighPriorityAlertsCount: () => {
        return get().personalAlerts.filter(
          alert => !alert.is_read && (alert.severity === 'high' || alert.action_required)
        ).length
      },

      hasRecentSuspiciousActivity: () => {
        const recentEvents = get().recentSecurityEvents
        const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000)

        return recentEvents.some(event => {
          const eventTime = new Date(event.timestamp).getTime()
          return eventTime > oneDayAgo && event.risk_level >= 3 // HIGH or CRITICAL
        })
      },

      getSecurityRecommendations: () => {
        const { securityInfo, personalAlerts } = get()
        const recommendations = []

        if (securityInfo) {
          // Password recommendations
          if (securityInfo.security_score < 70) {
            recommendations.push({
              type: 'password_strength',
              message: 'Consider using a stronger password',
              priority: 'medium' as const,
              action: 'Change Password',
            })
          }

          // MFA recommendations
          if (!securityInfo.mfa_enabled) {
            recommendations.push({
              type: 'enable_mfa',
              message: 'Enable two-factor authentication for better security',
              priority: 'high' as const,
              action: 'Enable MFA',
            })
          }

          // Backup codes recommendations
          if (securityInfo.mfa_enabled && securityInfo.backup_codes_remaining < 3) {
            recommendations.push({
              type: 'backup_codes',
              message: 'You have few backup codes remaining',
              priority: 'medium' as const,
              action: 'Generate New Codes',
            })
          }

          // Password age recommendation
          const passwordAge = Date.now() - new Date(securityInfo.password_last_changed).getTime()
          const sixMonthsInMs = 6 * 30 * 24 * 60 * 60 * 1000
          if (passwordAge > sixMonthsInMs) {
            recommendations.push({
              type: 'password_age',
              message: 'Your password is over 6 months old',
              priority: 'low' as const,
              action: 'Change Password',
            })
          }
        }

        return recommendations
      },

      // ========================================================================
      // Reset
      // ========================================================================

      reset: () => {
        set({
          ...initialState,
          lastUpdate: Date.now(),
        })
      },
    }),
    {
      name: 'huzilerz-user-security-store',
      partialize: (state) => ({
        // Persist user preferences and non-sensitive data
        securitySettings: state.securitySettings,
        personalAlerts: state.personalAlerts.filter(alert => !alert.is_read), // Only persist unread alerts
        // Don't persist sensitive security info or sessions
      }),
    }
  )
)

// ============================================================================
// Selectors (for performance optimization)
// ============================================================================

export const userSecuritySelectors = {
  securityInfo: (state: UserSecurityStore) => state.securityInfo,
  activeSessions: (state: UserSecurityStore) => state.activeSessions,
  recentSecurityEvents: (state: UserSecurityStore) => state.recentSecurityEvents,
  personalAlerts: (state: UserSecurityStore) => state.personalAlerts,
  unreadAlertsCount: (state: UserSecurityStore) => state.getUnreadAlertsCount(),
  highPriorityAlertsCount: (state: UserSecurityStore) => state.getHighPriorityAlertsCount(),
  hasRecentSuspiciousActivity: (state: UserSecurityStore) => state.hasRecentSuspiciousActivity(),
  securityRecommendations: (state: UserSecurityStore) => state.getSecurityRecommendations(),
  securitySettings: (state: UserSecurityStore) => state.securitySettings,
  isLoading: (state: UserSecurityStore) => state.isLoading,
  error: (state: UserSecurityStore) => state.error,
}

// ============================================================================
// Store Instance Export
// ============================================================================

export default useUserSecurityStore