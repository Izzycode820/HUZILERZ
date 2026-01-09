/**
 * Token Management Component
 * Handles silent token refresh and session management
 * Uses existing auth store and service infrastructure
 *
 * v2.0 - Enhanced with soft navigation and intent preservation
 */

'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore, authSelectors } from '@/stores/authentication/authStore'
import { storeAuthIntent } from '@/utils/redirect-with-intent'

interface TokenManagerProps {
  children: React.ReactNode
  refreshBeforeExpiry?: number // Minutes before expiry to refresh
  checkInterval?: number // How often to check token status (milliseconds)
}

export function TokenManager({
  children,
  refreshBeforeExpiry = 5, // Refresh 5 minutes before expiry
  checkInterval = 60000 // Check every minute
}: TokenManagerProps) {
  const router = useRouter()
  const intervalRef = React.useRef<NodeJS.Timeout | null>(null)
  const refreshingRef = React.useRef(false)
  const [shouldRedirectToLogin, setShouldRedirectToLogin] = React.useState(false)

  // Auth store selectors
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const isTokenExpired = useAuthStore(state => state.isTokenExpired)
  const getTimeUntilExpiry = useAuthStore(state => state.getTimeUntilExpiry)
  const refreshTokenSafe = useAuthStore(state => state.refreshTokenSafe)
  const setLogoutSuccess = useAuthStore(state => state.setLogoutSuccess)

  // Soft navigation effect - triggers after logout state update
  React.useEffect(() => {
    if (shouldRedirectToLogin) {
      router.push('/auth/login?expired=true')
      setShouldRedirectToLogin(false)
    }
  }, [shouldRedirectToLogin, router])

  const checkAndRefreshToken = React.useCallback(async () => {
    if (refreshingRef.current || !isAuthenticated) return

    try {
      const timeUntilExpiry = getTimeUntilExpiry()

      if (timeUntilExpiry === null) return

      // Convert refreshBeforeExpiry from minutes to milliseconds
      const refreshThreshold = refreshBeforeExpiry * 60 * 1000

      // If token is expired or will expire soon, refresh it
      if (timeUntilExpiry <= refreshThreshold) {
        refreshingRef.current = true

        try {
          await refreshTokenSafe()
        } catch (error) {
          console.error('Token refresh failed:', error)

          // CRITICAL: Capture intent BEFORE logout (preserves workspace context)
          const currentPath = window.location.pathname + window.location.search
          const currentWorkspaceId = localStorage.getItem('current_workspace_id')
          storeAuthIntent(currentPath, currentWorkspaceId)

          // Now logout user (this clears workspace context in store)
          setLogoutSuccess()

          // Use soft navigation (preserves React state where possible)
          // router.push is called in useEffect below after state update
          setShouldRedirectToLogin(true)
        }
      }
    } catch (error) {
      console.error('Error checking token status:', error)
    } finally {
      refreshingRef.current = false
    }
  }, [isAuthenticated, getTimeUntilExpiry, refreshBeforeExpiry, refreshTokenSafe, setLogoutSuccess])

  // Set up token checking interval
  React.useEffect(() => {
    if (!isAuthenticated) {
      // Clear interval if not authenticated
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    // Initial check
    checkAndRefreshToken()

    // Set up periodic checks
    intervalRef.current = setInterval(checkAndRefreshToken, checkInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isAuthenticated, checkAndRefreshToken, checkInterval])

  // Handle page visibility changes - refresh when page becomes visible
  React.useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && isAuthenticated) {
        // Check token when page becomes visible
        checkAndRefreshToken()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [isAuthenticated, checkAndRefreshToken])

  // Handle user activity - refresh on activity if token is close to expiry
  React.useEffect(() => {
    const handleUserActivity = () => {
      if (isAuthenticated && !refreshingRef.current) {
        const timeUntilExpiry = getTimeUntilExpiry()
        const refreshThreshold = refreshBeforeExpiry * 60 * 1000

        if (timeUntilExpiry !== null && timeUntilExpiry <= refreshThreshold) {
          checkAndRefreshToken()
        }
      }
    }

    // Throttle activity checks to avoid excessive calls
    let activityTimeout: NodeJS.Timeout | null = null
    const throttledActivityHandler = () => {
      if (activityTimeout) return

      activityTimeout = setTimeout(() => {
        handleUserActivity()
        activityTimeout = null
      }, 30000) // Throttle to once per 30 seconds
    }

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart']

    events.forEach(event => {
      document.addEventListener(event, throttledActivityHandler, { passive: true })
    })

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, throttledActivityHandler)
      })
      if (activityTimeout) {
        clearTimeout(activityTimeout)
      }
    }
  }, [isAuthenticated, getTimeUntilExpiry, refreshBeforeExpiry, checkAndRefreshToken])

  return <>{children}</>
}

/**
 * Hook for manual token management operations
 */
export function useTokenManager() {
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const isTokenExpired = useAuthStore(state => state.isTokenExpired)
  const getTimeUntilExpiry = useAuthStore(state => state.getTimeUntilExpiry)
  const refreshTokenSafe = useAuthStore(state => state.refreshTokenSafe)

  const forceRefresh = React.useCallback(async () => {
    if (!isAuthenticated) {
      throw new Error('User not authenticated')
    }

    try {
      await refreshTokenSafe()
      return true
    } catch (error) {
      console.error('Force refresh failed:', error)
      throw error
    }
  }, [isAuthenticated, refreshTokenSafe])

  const checkTokenStatus = React.useCallback(() => {
    const timeUntilExpiry = getTimeUntilExpiry()
    const expired = isTokenExpired()

    return {
      isExpired: expired,
      timeUntilExpiry,
      shouldRefresh: timeUntilExpiry !== null && timeUntilExpiry <= 5 * 60 * 1000 // 5 minutes
    }
  }, [getTimeUntilExpiry, isTokenExpired])

  return {
    isAuthenticated,
    forceRefresh,
    checkTokenStatus,
    isTokenExpired: isTokenExpired()
  }
}