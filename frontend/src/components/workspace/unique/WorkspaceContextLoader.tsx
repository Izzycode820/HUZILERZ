"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { useAuthStore, authSelectors, WorkspaceContextManager } from "@/stores/authentication/authStore"
import { useWorkspaceStore, workspaceSelectors } from "@/stores/authentication/workspaceStore"
import workspaceService from "@/services/authentication/workspace"
import type { WorkspaceAuthContext } from "@/types/authentication/workspace"

interface WorkspaceContextLoaderProps {
    children: React.ReactNode
}

export function WorkspaceContextLoader({ children }: WorkspaceContextLoaderProps) {
    const params = useParams()
    const workspaceId = params?.workspace_id as string

    // Auth state
    const user = useAuthStore(authSelectors.user)
    const isInitialized = useAuthStore(authSelectors.isInitialized)

    // Workspace state
    const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace)
    const setCurrentWorkspace = useWorkspaceStore((state: any) => state.setCurrentWorkspace)
    const setAuthWorkspace = useAuthStore((state: any) => state.setWorkspace)

    // Local loading state
    const [isRestoring, setIsRestoring] = useState(true)
    const [restorationError, setRestorationError] = useState<string | null>(null)

    useEffect(() => {
        if (!isInitialized) {
            return
        }

        if (currentWorkspace?.id === workspaceId) {
            setIsRestoring(false)
            return
        }

        const restoreWorkspace = async () => {
            try {
                const persistedWorkspaceId = WorkspaceContextManager.getCurrentWorkspace()

                // Just blindly try to load the workspace from ID in URL if persisted logic fails or mismatches
                // This is "force load" behavior appropriate for direct link access
                const targetWorkspaceId = workspaceId || persistedWorkspaceId

                if (targetWorkspaceId) {
                    console.log('[WorkspaceContextLoader] Restoring workspace:', targetWorkspaceId)

                    const response = await workspaceService.switchWorkspace(targetWorkspaceId)

                    if (response.success && response.workspace && response.membership) {
                        const workspaceContext: WorkspaceAuthContext = {
                            id: response.workspace.id,
                            name: response.workspace.name,
                            type: response.workspace.type,
                            status: response.workspace.status,
                            role: response.membership.role,
                            permissions: response.membership.permissions,
                            is_default: false
                        }

                        setCurrentWorkspace(workspaceContext)
                        setAuthWorkspace(workspaceContext)

                        console.log('✅ Workspace restored:', workspaceContext.name)
                        setIsRestoring(false)
                        return
                    } else {
                        throw new Error(response.error || 'Failed to restore workspace')
                    }
                }

                console.warn('[WorkspaceContextLoader] No workspace ID found')
                setRestorationError('Workspace ID missing')
                setIsRestoring(false)
            } catch (error) {
                console.error('[WorkspaceContextLoader] Workspace restoration failed:', error)
                setRestorationError(error instanceof Error ? error.message : 'Failed to restore workspace')
                setIsRestoring(false)
            }
        }

        restoreWorkspace()
    }, [isInitialized, currentWorkspace, workspaceId, setCurrentWorkspace, setAuthWorkspace])

    if (!isInitialized || isRestoring) {
        return (
            <div className="flex h-screen items-center justify-center bg-white">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-500">Loading workspace context...</p>
                </div>
            </div>
        )
    }

    if (restorationError || !currentWorkspace || !user) {
        return (
            <div className="flex h-screen items-center justify-center flex-col gap-4 bg-white">
                <p className="text-red-500">
                    {restorationError || 'Workspace context missing'}
                </p>
                <a href="/workspaces" className="text-sm text-blue-600 hover:underline">
                    ← Return to Dashboard
                </a>
            </div>
        )
    }

    return <>{children}</>
}
