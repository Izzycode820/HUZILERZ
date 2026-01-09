/**
 * Combined Auth + Redirect Hook
 * Provides authentication state AND redirect helpers in one place
 *
 * Use this in components that need to gate actions behind auth
 */

'use client'

import { useRouter } from 'next/navigation'
import { useCallback } from 'react'
import { useAuth } from './useAuth'
import {
  redirectToLogin,
  redirectToRegister,
  redirectToCheckout,
  smartRedirect,
  buildPathWithParams
} from '../../utils/redirect-with-intent'

export interface UseAuthWithRedirectReturn extends ReturnType<typeof useAuth> {
  // Redirect helpers (bound to router)
  redirectToLogin: (next: string) => void
  redirectToRegister: (next: string) => void
  redirectToCheckout: (returnTo: string, params?: Record<string, string>) => void
  requireAuth: (intendedDestination: string, onAuthenticated?: () => void) => void
  buildPathWithParams: (basePath: string, params?: Record<string, string>) => string
}

/**
 * Combined hook for auth state + redirect helpers
 *
 * @example
 * // In a component
 * const { isAuthenticated, requireAuth } = useAuthWithRedirect()
 *
 * <button onClick={() =>
 *   requireAuth('/pricing?plan=pro', () => {
 *     // User is authenticated, proceed with action
 *     startCheckout()
 *   })
 * }>
 */
export function useAuthWithRedirect(): UseAuthWithRedirectReturn {
  const router = useRouter()
  const auth = useAuth()

  // Bind redirect helpers to router
  const boundRedirectToLogin = useCallback(
    (next: string) => redirectToLogin(router, next),
    [router]
  )

  const boundRedirectToRegister = useCallback(
    (next: string) => redirectToRegister(router, next),
    [router]
  )

  const boundRedirectToCheckout = useCallback(
    (returnTo: string, params?: Record<string, string>) =>
      redirectToCheckout(router, returnTo, params),
    [router]
  )

  /**
   * Require authentication before proceeding
   * If not authenticated, redirects to login with intent
   * If authenticated, executes callback
   */
  const requireAuth = useCallback(
    (intendedDestination: string, onAuthenticated?: () => void) => {
      smartRedirect(router, auth.isAuthenticated, intendedDestination, onAuthenticated)
    },
    [router, auth.isAuthenticated]
  )

  return {
    ...auth,
    redirectToLogin: boundRedirectToLogin,
    redirectToRegister: boundRedirectToRegister,
    redirectToCheckout: boundRedirectToCheckout,
    requireAuth,
    buildPathWithParams
  }
}

export default useAuthWithRedirect
