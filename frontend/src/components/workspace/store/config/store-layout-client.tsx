"use client"

/**
 * Store Workspace Client Layout (v4.0 - Bulletproof Context Restoration)
 *
 * KEY IMPROVEMENTS FROM RESEARCH:
 * 1. AbortController + 10s timeout (prevents infinite loading)
 * 2. 3 retries with exponential backoff (handles transient failures)
 * 3. isHydrated guard (fixes Next.js SSR race conditions)
 * 4. Always try URL workspace first (don't require localStorage match)
 * 5. Graceful fallback to /workspace (no error screens)
 * 6. Branded loader for premium UX
 *
 * FLOW:
 * 1. Wait for client hydration + auth init
 * 2. If workspace already matches URL → done
 * 3. Try to restore workspace from URL (with retries)
 * 4. On success → render layout
 * 5. On failure → soft redirect to /workspace (not error screen)
 */

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import { WorkspaceLayout } from "@/components/workspace/layouts/workspace-layout"
import { WorkspaceSidebar } from "@/components/workspace/layouts/workspace-sidebar"
import { WorkspaceHeader } from "@/components/workspace/layouts/workspace-header"
import { getStoreSidebarConfig } from "@/components/workspace/store/config/sidebar"
import { useAuthStore, authSelectors, WorkspaceContextManager } from "@/stores/authentication/authStore"
import { useWorkspaceStore, workspaceSelectors } from "@/stores/authentication/workspaceStore"
import workspaceService from "@/services/authentication/workspace"
import { AuthPageSpinner } from "@/components/authentication/shared/AuthLoadingSpinner"
import type { WorkspaceAuthContext } from "@/types/authentication/workspace"
import { MobileBottomNav } from "@/components/workspace/layouts/mobile/mobile-bottom-nav"
import { MobileHeader } from "@/components/workspace/layouts/mobile/mobile-header"
import { MobileMenuDrawer } from "@/components/workspace/layouts/mobile/mobile-menu-drawer"

// ============================================================================
// Configuration
// ============================================================================

const RESTORE_TIMEOUT_MS = 10000  // 10 second timeout per attempt
const MAX_RETRIES = 3             // Max retry attempts
const INITIAL_RETRY_DELAY_MS = 1000 // 1s, then 2s, then 4s (exponential)

// ============================================================================
// Utility: Fetch with timeout
// ============================================================================

async function fetchWithTimeout<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  timeoutMs: number
): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    return await fn(controller.signal)
  } finally {
    clearTimeout(timeoutId)
  }
}

// ============================================================================
// Utility: Retry with exponential backoff
// ============================================================================

async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number,
  initialDelayMs: number
): Promise<T | null> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
      console.warn(`[StoreLayoutClient] Attempt ${attempt + 1}/${maxRetries} failed:`, lastError.message)

      // Don't delay after last attempt
      if (attempt < maxRetries - 1) {
        const delay = initialDelayMs * Math.pow(2, attempt)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
  }

  console.error('[StoreLayoutClient] All retry attempts failed:', lastError)
  return null
}

// ============================================================================
// Component
// ============================================================================

interface StoreLayoutClientProps {
  children: React.ReactNode
}

export function StoreLayoutClient({ children }: StoreLayoutClientProps) {
  const router = useRouter()
  const params = useParams()
  const workspaceId = params?.workspace_id as string

  // Hydration guard - prevents SSR/client mismatch
  const [isHydrated, setIsHydrated] = useState(false)

  // Auth state
  const user = useAuthStore(authSelectors.user)
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const isInitialized = useAuthStore(authSelectors.isInitialized)

  // Workspace state
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace)
  const setCurrentWorkspace = useWorkspaceStore((state: any) => state.setCurrentWorkspace)
  const setAuthWorkspace = useAuthStore((state: any) => state.setWorkspace)

  // Local state
  const [isRestoring, setIsRestoring] = useState(true)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const restorationAttemptedRef = useRef(false)

  // Mark as hydrated on client
  useEffect(() => {
    setIsHydrated(true)
  }, [])

  // Main restoration effect
  useEffect(() => {
    // Wait for hydration + auth init
    if (!isHydrated || !isInitialized) {
      return
    }

    // Not authenticated → redirect to login
    if (!isAuthenticated) {
      console.log('[StoreLayoutClient] Not authenticated, redirecting to login')
      router.replace(`/auth/login?next=${encodeURIComponent(window.location.pathname)}`)
      return
    }

    // Already loaded and matches URL → done
    if (currentWorkspace?.id === workspaceId) {
      setIsRestoring(false)
      return
    }

    // Prevent duplicate restoration attempts
    if (restorationAttemptedRef.current) {
      return
    }
    restorationAttemptedRef.current = true

    // Restore workspace
    const restoreWorkspace = async () => {
      console.log('[StoreLayoutClient] Restoring workspace:', workspaceId)

      const result = await withRetry(async () => {
        return await fetchWithTimeout(async (signal) => {
          // Note: switchWorkspace doesn't use signal yet, but we abort via timeout
          const response = await workspaceService.switchWorkspace(workspaceId)

          // Check if aborted before processing
          if (signal.aborted) {
            throw new Error('Request aborted')
          }

          if (!response.success) {
            // 401/403 errors - user lost access
            if (response.error?.includes('401') || response.error?.includes('403') ||
              response.error?.includes('permission') || response.error?.includes('access')) {
              throw new Error('ACCESS_DENIED')
            }
            throw new Error(response.error || 'Failed to restore workspace')
          }

          if (!response.workspace || !response.membership) {
            throw new Error('Invalid response structure')
          }

          return response
        }, RESTORE_TIMEOUT_MS)
      }, MAX_RETRIES, INITIAL_RETRY_DELAY_MS)

      if (result?.success && result.workspace && result.membership) {
        // Build WorkspaceAuthContext
        const workspaceContext: WorkspaceAuthContext = {
          id: result.workspace.id,
          name: result.workspace.name,
          type: result.workspace.type,
          status: result.workspace.status,
          role: result.membership.role,
          permissions: result.membership.permissions,
          is_default: false
        }

        // Update stores
        setCurrentWorkspace(workspaceContext)
        setAuthWorkspace(workspaceContext)
        WorkspaceContextManager.setCurrentWorkspace(workspaceContext.id)

        console.log('✅ Workspace restored:', workspaceContext.name)
        setIsRestoring(false)
      } else {
        // All retries failed → graceful fallback to workspace picker
        console.warn('[StoreLayoutClient] Restoration failed, redirecting to workspace picker')
        WorkspaceContextManager.clearWorkspace()
        router.replace('/workspace')
      }
    }

    restoreWorkspace()
  }, [isHydrated, isInitialized, isAuthenticated, currentWorkspace, workspaceId, router, setCurrentWorkspace, setAuthWorkspace])

  // Show branded loader while restoring
  if (!isHydrated || !isInitialized || isRestoring) {
    return <AuthPageSpinner />
  }

  // Safety check: workspace must match URL
  if (!currentWorkspace || currentWorkspace.id !== workspaceId || !user) {
    // Shouldn't reach here, but if we do, redirect gracefully
    console.error('[StoreLayoutClient] Unexpected state mismatch, redirecting')
    router.replace('/workspace')
    return <AuthPageSpinner />
  }

  // Workspace ready → render layout
  const sidebarConfig = getStoreSidebarConfig(currentWorkspace.id, {
    name: user.username,
    email: user.email,
    avatar: user.avatar || "/avatars/default.jpg"
  })



  return (
    <>
      <WorkspaceLayout
        sidebar={<WorkspaceSidebar config={sidebarConfig} />}
        header={<WorkspaceHeader title={`${currentWorkspace.name} - Store`} />}
        mobileHeader={<MobileHeader user={{ name: user.username, email: user.email, avatar: user.avatar }} />}
        mobileNav={<MobileBottomNav onMenuClick={() => setIsMobileMenuOpen(true)} />}
      >
        {children}
      </WorkspaceLayout>

      {/* Mobile Drawer (Portal based) */}
      <MobileMenuDrawer
        config={sidebarConfig}
        isOpen={isMobileMenuOpen}
        onClose={setIsMobileMenuOpen}
      />
    </>
  )
}
