"use client"

/**
 * Management (Workspace Home) Client Layout (v2.0 - Robust Auth Handling)
 * Uses Zustand stores + Config files (Industry Standard Pattern)
 *
 * KEY IMPROVEMENTS (Aligned with StoreLayoutClient):
 * 1. isHydrated guard (fixes Next.js SSR race conditions)
 * 2. isInitialized check (waits for auth to complete)
 * 3. isAuthenticated check (verifies auth status)
 * 4. Login redirect with return URL (proper UX)
 * 5. Branded loader (consistent UX)
 *
 * DATA FLOW:
 * 1. Wait for client hydration + auth initialization
 * 2. If not authenticated → redirect to login with return URL
 * 3. If authenticated → render layout with user data
 * 4. Zustand stores provide runtime data (user)
 * 5. Config files provide static structure (navigation blueprint)
 */

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { WorkspaceLayout } from "@/components/workspace/layouts/workspace-layout"
import { WorkspaceSidebar } from "@/components/workspace/layouts/workspace-sidebar"
import { WorkspaceHeader } from "@/components/workspace/layouts/workspace-header"
import { getManagementSidebarConfig } from "@/components/workspace/management/config/sidebar"
import { useAuthStore, authSelectors } from "@/stores/authentication/authStore"
import { AuthPageSpinner } from "@/components/authentication/shared/AuthLoadingSpinner"

interface ManagementLayoutClientProps {
  children: React.ReactNode
}

export function ManagementLayoutClient({ children }: ManagementLayoutClientProps) {
  const router = useRouter()

  // Hydration guard - prevents SSR/client mismatch
  const [isHydrated, setIsHydrated] = useState(false)

  // Auth state from Zustand
  const user = useAuthStore(authSelectors.user)
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const isInitialized = useAuthStore(authSelectors.isInitialized)

  // Mark as hydrated on client mount
  useEffect(() => {
    setIsHydrated(true)
  }, [])

  // Auth check effect - runs after hydration + auth init
  useEffect(() => {
    // Wait for hydration + auth initialization
    if (!isHydrated || !isInitialized) {
      return
    }

    // Not authenticated → redirect to login with return URL
    if (!isAuthenticated) {
      console.log('[ManagementLayoutClient] Not authenticated, redirecting to login')
      router.replace(`/auth/login?next=${encodeURIComponent(window.location.pathname)}`)
      return
    }
  }, [isHydrated, isInitialized, isAuthenticated, router])

  // Show branded loader while waiting for hydration or auth init
  if (!isHydrated || !isInitialized) {
    return <AuthPageSpinner />
  }

  // Show loader while redirecting (user not authenticated)
  if (!isAuthenticated || !user) {
    return <AuthPageSpinner />
  }

  // Get STATIC STRUCTURE from config (Management-specific navigation blueprint)
  const sidebarConfig = getManagementSidebarConfig({
    name: user.username,
    email: user.email,
    avatar: user.avatar || "/avatars/default.jpg"
  })

  return (
    <WorkspaceLayout
      sidebar={<WorkspaceSidebar config={sidebarConfig} />}
      header={<WorkspaceHeader title="Workspace Management" />}
    >
      {children}
    </WorkspaceLayout>
  )
}
