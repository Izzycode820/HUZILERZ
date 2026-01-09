"use client"

/**
 * Management (Workspace Home) Client Layout
 * Uses Zustand stores + Config files (Industry Standard Pattern)
 *
 * DATA FLOW:
 * 1. Zustand stores provide runtime data (user)
 * 2. Config files provide static structure (navigation blueprint for Management/Home)
 * 3. This component combines both → renders universal layout
 */

import { WorkspaceLayout } from "@/components/workspace/layouts/workspace-layout"
import { WorkspaceSidebar } from "@/components/workspace/layouts/workspace-sidebar"
import { WorkspaceHeader } from "@/components/workspace/layouts/workspace-header"
import { getManagementSidebarConfig } from "@/components/workspace/management/config/sidebar"
import { useAuthStore } from "@/stores/authentication/authStore"

interface ManagementLayoutClientProps {
  children: React.ReactNode
}

export function ManagementLayoutClient({ children }: ManagementLayoutClientProps) {
  // Get RUNTIME DATA from Zustand (changes per user)
  const user = useAuthStore((state: any) => state.user)

  // Fallback if no user loaded yet
  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
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
