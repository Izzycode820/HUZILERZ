/**
 * Sessions Store - Zustand 2024 Best Practices
 * Manages user sessions, active devices, and session security
 * Works directly with SessionsService and comprehensive types
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  UserSession
} from '../../types/authentication/user'
import type {
  DeviceFingerprint,
  LocationInfo
} from '../../types/authentication/auth'

// ============================================================================
// Sessions Store State Interface
// ============================================================================

interface SessionsStoreState {
  // Sessions Data
  activeSessions: UserSession[]
  currentSession: UserSession | null

  // UI State
  isLoading: boolean
  isTerminating: boolean
  error: string | null

  // Session Management
  terminatingSessionId: string | null
  lastRefreshed: number | null

  // Actions
  setActiveSessions: (sessions: UserSession[]) => void
  setCurrentSession: (session: UserSession | null) => void
  addSession: (session: UserSession) => void
  removeSession: (sessionId: string) => void
  updateSession: (sessionId: string, updates: Partial<UserSession>) => void
  setTerminatingSession: (sessionId: string | null) => void
  setLoading: (loading: boolean) => void
  setTerminating: (terminating: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  markRefreshed: () => void

  // Helper Methods
  getSessionById: (sessionId: string) => UserSession | null
  isCurrentSession: (sessionId: string) => boolean
  getActiveSessionsCount: () => number
  hasMultipleSessions: () => boolean
  getCurrentDevice: () => string | null
  getSessionsFromLocation: (location: string) => UserSession[]
}

// ============================================================================
// Create Sessions Store
// ============================================================================

export const useSessionsStore = create<SessionsStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      activeSessions: [],
      currentSession: null,
      securityInfo: null,
      isLoading: false,
      isTerminating: false,
      error: null,
      terminatingSessionId: null,
      lastRefreshed: null,

      // ========================================================================
      // Sessions Data Actions
      // ========================================================================

      setActiveSessions: (sessions) => {
        set((state) => {
          state.activeSessions = sessions
          state.lastRefreshed = Date.now()

          // Update current session if it exists in the list
          if (state.currentSession) {
            const updatedCurrent = sessions.find(s => s.id === state.currentSession?.id)
            if (updatedCurrent) {
              state.currentSession = updatedCurrent
            }
          }
        })
      },

      setCurrentSession: (session) => {
        set((state) => {
          state.currentSession = session
        })
      },


      addSession: (session) => {
        set((state) => {
          // Avoid duplicates
          const existingIndex = state.activeSessions.findIndex((s: UserSession) => s.id === session.id)
          if (existingIndex >= 0) {
            state.activeSessions[existingIndex] = session
          } else {
            state.activeSessions.push(session)
          }
        })
      },

      removeSession: (sessionId) => {
        set((state) => {
          state.activeSessions = state.activeSessions.filter((s: UserSession) => s.id !== sessionId)

          // Clear current session if it was removed
          if (state.currentSession?.id === sessionId) {
            state.currentSession = null
          }

          // Clear terminating session if it matches
          if (state.terminatingSessionId === sessionId) {
            state.terminatingSessionId = null
            state.isTerminating = false
          }
        })
      },

      updateSession: (sessionId, updates) => {
        set((state) => {
          const sessionIndex = state.activeSessions.findIndex((s: UserSession) => s.id === sessionId)
          if (sessionIndex >= 0) {
            Object.assign(state.activeSessions[sessionIndex], updates)
          }

          // Update current session if it matches
          if (state.currentSession?.id === sessionId) {
            Object.assign(state.currentSession, updates)
          }
        })
      },

      setTerminatingSession: (sessionId) => {
        set((state) => {
          state.terminatingSessionId = sessionId
          state.isTerminating = !!sessionId
        })
      },

      // ========================================================================
      // UI State Actions
      // ========================================================================

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading
        })
      },

      setTerminating: (terminating) => {
        set((state) => {
          state.isTerminating = terminating
          if (!terminating) {
            state.terminatingSessionId = null
          }
        })
      },

      setError: (error) => {
        set((state) => {
          state.error = error
          if (error) {
            state.isLoading = false
            state.isTerminating = false
            state.terminatingSessionId = null
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      markRefreshed: () => {
        set((state) => {
          state.lastRefreshed = Date.now()
        })
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      getSessionById: (sessionId) => {
        const { activeSessions } = get()
        return activeSessions.find(s => s.id === sessionId) || null
      },

      isCurrentSession: (sessionId) => {
        const { currentSession } = get()
        return currentSession?.id === sessionId
      },

      getActiveSessionsCount: () => {
        const { activeSessions } = get()
        return activeSessions.length
      },

      hasMultipleSessions: () => {
        const { activeSessions } = get()
        return activeSessions.length > 1
      },

      getCurrentDevice: () => {
        const { currentSession } = get()
        return currentSession?.device_name || null
      },

      getSessionsFromLocation: (location) => {
        const { activeSessions } = get()
        return activeSessions.filter(s =>
          s.location?.toLowerCase().includes(location.toLowerCase())
        )
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const sessionsSelectors = {
  // Core selectors
  activeSessions: (state: SessionsStoreState) => state.activeSessions,
  currentSession: (state: SessionsStoreState) => state.currentSession,
  isLoading: (state: SessionsStoreState) => state.isLoading,
  isTerminating: (state: SessionsStoreState) => state.isTerminating,
  error: (state: SessionsStoreState) => state.error,
  terminatingSessionId: (state: SessionsStoreState) => state.terminatingSessionId,

  // Computed selectors
  activeSessionsCount: (state: SessionsStoreState) => state.activeSessions.length,
  hasMultipleSessions: (state: SessionsStoreState) => state.activeSessions.length > 1,
  currentSessionId: (state: SessionsStoreState) => state.currentSession?.id || null,
  currentDevice: (state: SessionsStoreState) => state.currentSession?.device_name || null,
  lastRefreshed: (state: SessionsStoreState) => state.lastRefreshed,

  // Platform-focused selectors
  uniqueLocations: (state: SessionsStoreState) => {
    const locations = state.activeSessions
      .map(s => s.location)
      .filter(Boolean)
    return [...new Set(locations)]
  }
}

// ============================================================================
// Default Export
// ============================================================================

export default useSessionsStore