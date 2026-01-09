/**
 * Sessions Hook - 2024 Best Practices with Zustand
 * Custom hook layer for sessions store - handles session management and security
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { useSessionsStore, sessionsSelectors } from '../../stores/authentication/sessionsStore'
import sessionsService from '../../services/authentication/sessions'
import type { UserSession } from '../../types/authentication/user'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseSessionsReturn {
  // State selectors (performance optimized)
  activeSessions: UserSession[]
  currentSession: UserSession | null
  isLoading: boolean
  isTerminating: boolean
  error: string | null
  terminatingSessionId: string | null

  // Computed state
  activeSessionsCount: number
  hasMultipleSessions: boolean
  currentSessionId: string | null
  currentDevice: string | null
  uniqueLocations: (string | undefined)[]
  lastRefreshed: number | null

  // Actions (stable references)
  loadSessions: () => Promise<UserSession[]>
  terminateSession: (sessionId: string) => Promise<void>
  terminateAllOtherSessions: () => Promise<void>
  refreshSessions: () => Promise<void>
  clearError: () => void

  // Helper methods
  getSessionById: (sessionId: string) => UserSession | null
  isCurrentSession: (sessionId: string) => boolean
  getSessionsFromLocation: (location: string) => UserSession[]
}

// ============================================================================
// Main Sessions Hook
// ============================================================================

export function useSessions(): UseSessionsReturn {
  // Selective store subscriptions (performance optimized)
  const activeSessions = useSessionsStore(sessionsSelectors.activeSessions)
  const currentSession = useSessionsStore(sessionsSelectors.currentSession)
  const isLoading = useSessionsStore(sessionsSelectors.isLoading)
  const isTerminating = useSessionsStore(sessionsSelectors.isTerminating)
  const error = useSessionsStore(sessionsSelectors.error)
  const terminatingSessionId = useSessionsStore(sessionsSelectors.terminatingSessionId)
  const activeSessionsCount = useSessionsStore(sessionsSelectors.activeSessionsCount)
  const hasMultipleSessions = useSessionsStore(sessionsSelectors.hasMultipleSessions)
  const currentSessionId = useSessionsStore(sessionsSelectors.currentSessionId)
  const currentDevice = useSessionsStore(sessionsSelectors.currentDevice)
  const uniqueLocations = useSessionsStore(sessionsSelectors.uniqueLocations)
  const lastRefreshed = useSessionsStore(sessionsSelectors.lastRefreshed)

  // Store actions (direct references for performance)
  const setActiveSessions = useSessionsStore((state: any) => state.setActiveSessions)
  const setCurrentSession = useSessionsStore((state: any) => state.setCurrentSession)
  const removeSession = useSessionsStore((state: any) => state.removeSession)
  const setTerminatingSession = useSessionsStore((state: any) => state.setTerminatingSession)
  const setLoading = useSessionsStore((state: any) => state.setLoading)
  const setTerminating = useSessionsStore((state: any) => state.setTerminating)
  const setError = useSessionsStore((state: any) => state.setError)
  const clearError = useSessionsStore((state: any) => state.clearError)
  const markRefreshed = useSessionsStore((state: any) => state.markRefreshed)
  const getSessionById = useSessionsStore((state: any) => state.getSessionById)
  const isCurrentSession = useSessionsStore((state: any) => state.isCurrentSession)
  const getSessionsFromLocation = useSessionsStore((state: any) => state.getSessionsFromLocation)

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const loadSessions = useCallback(async (): Promise<UserSession[]> => {
    try {
      setLoading(true)
      setError(null)

      const sessions = await sessionsService.getActiveSessions()

      if (sessions) {
        setActiveSessions(sessions)

        // Set current session if available
        const currentSession = sessions.find(s => s.is_current) || null
        setCurrentSession(currentSession)

        return sessions
      }

      throw new Error('Failed to load sessions')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load sessions'
      setError(errorMessage)
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setError, setActiveSessions, setCurrentSession])

  const terminateSession = useCallback(async (sessionId: string): Promise<void> => {
    try {
      setTerminatingSession(sessionId)
      setError(null)

      const response = await sessionsService.revokeSession(sessionId)

      if (response.success) {
        removeSession(sessionId)
        return
      }

      throw new Error(response.error || 'Failed to terminate session')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to terminate session'
      setError(errorMessage)
      throw error
    } finally {
      setTerminatingSession(null)
    }
  }, [setTerminatingSession, setError, removeSession])

  const terminateAllOtherSessions = useCallback(async (): Promise<void> => {
    try {
      setTerminating(true)
      setError(null)

      const response = await sessionsService.revokeAllOtherSessions()

      if (response.success) {
        // Refresh sessions to get updated list
        await loadSessions()
        return
      }

      throw new Error(response.error || 'Failed to terminate other sessions')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to terminate other sessions'
      setError(errorMessage)
      throw error
    } finally {
      setTerminating(false)
    }
  }, [setTerminating, setError, loadSessions])

  const refreshSessions = useCallback(async (): Promise<void> => {
    try {
      setError(null)
      await loadSessions()
      markRefreshed()
    } catch (error) {
      // Error already handled by loadSessions
      throw error
    }
  }, [loadSessions, markRefreshed, setError])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    activeSessions,
    currentSession,
    isLoading,
    isTerminating,
    error,
    terminatingSessionId,

    // Computed state
    activeSessionsCount,
    hasMultipleSessions,
    currentSessionId,
    currentDevice,
    uniqueLocations,
    lastRefreshed,

    // Actions (stable)
    loadSessions,
    terminateSession,
    terminateAllOtherSessions,
    refreshSessions,
    clearError,

    // Helper methods
    getSessionById,
    isCurrentSession,
    getSessionsFromLocation
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for current session info only - minimal re-renders
 */
export function useCurrentSession() {
  return {
    currentSession: useSessionsStore(sessionsSelectors.currentSession),
    currentSessionId: useSessionsStore(sessionsSelectors.currentSessionId),
    currentDevice: useSessionsStore(sessionsSelectors.currentDevice)
  }
}

/**
 * Hook for session list management only - minimal re-renders
 */
export function useSessionsList() {
  return {
    activeSessions: useSessionsStore(sessionsSelectors.activeSessions),
    activeSessionsCount: useSessionsStore(sessionsSelectors.activeSessionsCount),
    hasMultipleSessions: useSessionsStore(sessionsSelectors.hasMultipleSessions),
    uniqueLocations: useSessionsStore(sessionsSelectors.uniqueLocations),
    lastRefreshed: useSessionsStore(sessionsSelectors.lastRefreshed)
  }
}

/**
 * Hook for session termination only - minimal re-renders
 */
export function useSessionTermination() {
  return {
    isTerminating: useSessionsStore(sessionsSelectors.isTerminating),
    terminatingSessionId: useSessionsStore(sessionsSelectors.terminatingSessionId)
  }
}

// ============================================================================
// Default Export
// ============================================================================

export default useSessions