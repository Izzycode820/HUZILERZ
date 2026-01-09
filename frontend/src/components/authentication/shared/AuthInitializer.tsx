'use client'

console.log('[LOAD] AuthInitializer module');

/**
 * Authentication Initializer Component
 * Handles session restoration from httpOnly refresh token cookie on app mount
 * Prevents hydration errors with Next.js App Router
 *
 * Flow:
 * 1. Wait for client-side hydration (avoid SSR mismatch)
 * 2. Check if session already initialized
 * 3. Call refresh token endpoint to restore session
 * 4. Hydrate Zustand store with user data
 * 5. Restore workspace context if exists (v3.0 - Header-Based Context)
 * 6. Mark initialization complete
 */


import React, { useEffect, useState } from 'react'
import { useAuthStore, authSelectors, WorkspaceContextManager } from '@/stores/authentication/authStore'
import { useWorkspaceStore } from '@/stores/authentication/workspaceStore'
import workspaceService from '@/services/authentication/workspace'
import type { WorkspaceAuthContext } from '@/types/authentication/workspace'
import { AuthPageSpinner } from './AuthLoadingSpinner'

interface AuthInitializerProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function AuthInitializer({
  children,
  fallback
}: AuthInitializerProps) {
  // Hydration protection: wait for client-side mount
  const [isHydrated, setIsHydrated] = useState(false)
  const [workspaceRestored, setWorkspaceRestored] = useState(false)

  // Auth store state
  const isInitialized = useAuthStore(authSelectors.isInitialized)
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const initializeSession = useAuthStore((state: any) => state.initializeSession)

  // Workspace store state
  const currentWorkspace = useWorkspaceStore((state: any) => state.currentWorkspace)
  const setCurrentWorkspace = useWorkspaceStore((state: any) => state.setCurrentWorkspace)
  const setAuthWorkspace = useAuthStore((state: any) => state.setWorkspace)

  // Step 1: Wait for hydration (prevents SSR mismatch)
  useEffect(() => {
    setIsHydrated(true)
  }, [])

  // Step 2: Initialize session after hydration
  useEffect(() => {
    if (!isHydrated) return
    if (isInitialized) return

    // Restore session from refresh token cookie
    initializeSession()
  }, [isHydrated, isInitialized, initializeSession])

  // Step 3: Restore workspace context globally (v3.0 - runs on ALL routes)
  useEffect(() => {
    // Wait for auth initialization
    if (!isInitialized || !isAuthenticated) return

    // Already restored or no workspace to restore
    if (workspaceRestored) return

    // Workspace already in Zustand (no need to restore)
    if (currentWorkspace) {
      setWorkspaceRestored(true)
      return
    }

    const restoreWorkspace = async () => {
      try {
        // Check if user was in a workspace (persisted in localStorage)
        const lastWorkspaceId = WorkspaceContextManager.getCurrentWorkspace()

        if (!lastWorkspaceId) {
          // No workspace to restore (user never switched to one)
          setWorkspaceRestored(true)
          return
        }

        console.log('[AuthInitializer] Restoring workspace from localStorage:', lastWorkspaceId)

        // Fetch fresh workspace details from backend (validates access + gets latest data)
        const response = await workspaceService.switchWorkspace(lastWorkspaceId)

        if (response.success && response.workspace && response.membership) {
          // Build WorkspaceAuthContext from response
          const workspaceContext: WorkspaceAuthContext = {
            id: response.workspace.id,
            name: response.workspace.name,
            type: response.workspace.type,
            status: response.workspace.status,
            role: response.membership.role,
            permissions: response.membership.permissions,
            is_default: false
          }

          // Update both stores (unified state management)
          setCurrentWorkspace(workspaceContext)
          setAuthWorkspace(workspaceContext)

          console.log('✅ Workspace restored globally:', workspaceContext.name)
        } else {
          // Workspace restoration failed (user lost access, workspace deleted, etc.)
          console.warn('[AuthInitializer] Workspace restoration failed - clearing localStorage')
          WorkspaceContextManager.clearWorkspace()
        }
      } catch (error) {
        // Non-blocking error (user can still use app without workspace context)
        console.error('[AuthInitializer] Workspace restoration error:', error)
        WorkspaceContextManager.clearWorkspace()
      } finally {
        // Mark as restored (success or failure) to prevent infinite loop
        setWorkspaceRestored(true)
      }
    }

    restoreWorkspace()
  }, [isInitialized, isAuthenticated, currentWorkspace, workspaceRestored, setCurrentWorkspace, setAuthWorkspace])

  // Show loading during hydration or initialization
  if (!isHydrated || !isInitialized) {
    return fallback || <AuthPageSpinner />
  }

  // Initialization complete - render app
  return <>{children}</>
}

/**
 * Hook for accessing initialization state
 */
export function useAuthInitialization() {
  const isInitialized = useAuthStore(authSelectors.isInitialized)
  const isHydrated = typeof window !== 'undefined'

  return {
    isInitialized,
    isHydrated,
    isReady: isHydrated && isInitialized
  }
}
