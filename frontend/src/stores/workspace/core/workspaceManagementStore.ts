/**
 * Workspace Store - Core workspace management
 * Zustand 2024 Best Practices
 * Manages workspace CRUD operations and state
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  WorkspaceData,
  WorkspaceListItem,
  WorkspaceCreateRequest,
  WorkspaceUpdateRequest,
  WorkspaceCreateResponse,
  WorkspaceUpdateResponse,
  WorkspaceDeleteResponse,
  WorkspaceRestoreResponse
} from '../../../types/workspace/core'
import workspaceService from '../../../services/workspace/core/workspace'
import { useWorkspaceStore as useWorkspaceAuthStore } from '../../authentication/workspaceStore'
import type { AvailableWorkspace } from '../../../types/authentication/workspace'

// ============================================================================
// Helper Functions - Store Synchronization
// ============================================================================

/**
 * Map workspace list items to available workspaces for auth store
 * Keeps the two stores in sync
 * Filters out deleted workspaces
 */
function mapToAvailableWorkspaces(workspaces: WorkspaceListItem[]): AvailableWorkspace[] {
  return workspaces
    .filter(ws => ws.status !== 'deleted') // Only include active/suspended workspaces
    .map(ws => ({
      id: ws.id,
      name: ws.name,
      type: ws.type,
      is_default: false, // Backend should provide this
      user_role: ws.role,
      role: ws.role,
      status: ws.status as 'active' | 'suspended', // Safe cast after filtering
      permissions: ws.permissions,
      member_count: ws.member_count,
      createdAt: ws.createdAt,
      updatedAt: ws.updatedAt
    }))
}

/**
 * Sync workspaces to auth store
 * Ensures both stores have consistent data
 */
function syncToAuthStore(workspaces: WorkspaceListItem[]) {
  const availableWorkspaces = mapToAvailableWorkspaces(workspaces)
  useWorkspaceAuthStore.getState().setAvailableWorkspaces(availableWorkspaces)
}

// ============================================================================
// Workspace Store State Interface
// ============================================================================

interface WorkspaceStoreState {
  // Workspace Data
  workspaces: WorkspaceListItem[]
  currentWorkspace: WorkspaceData | null
  workspaceDetails: Record<string, WorkspaceData> // Cache for individual workspaces

  // UI State
  isLoading: boolean
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
  isRestoring: boolean
  error: string | null

  // Actions - Workspace Management
  listWorkspaces: (force?: boolean) => Promise<void>
  getWorkspace: (workspaceId: string) => Promise<void>
  createWorkspace: (request: WorkspaceCreateRequest) => Promise<WorkspaceCreateResponse>
  updateWorkspace: (workspaceId: string, request: WorkspaceUpdateRequest) => Promise<WorkspaceUpdateResponse>
  deleteWorkspace: (workspaceId: string) => Promise<WorkspaceDeleteResponse>
  restoreWorkspace: (workspaceId: string) => Promise<WorkspaceRestoreResponse>

  // UI Actions
  setCurrentWorkspace: (workspace: WorkspaceData | null) => void
  setLoading: (loading: boolean) => void
  setCreating: (creating: boolean) => void
  setUpdating: (updating: boolean) => void
  setDeleting: (deleting: boolean) => void
  setRestoring: (restoring: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearWorkspaces: () => void

  // Helper Methods
  hasWorkspaces: () => boolean
  getWorkspaceById: (workspaceId: string) => WorkspaceData | undefined
  isWorkspaceOwner: (workspaceId: string) => boolean
  canEditWorkspace: (workspaceId: string) => boolean
  canDeleteWorkspace: (workspaceId: string) => boolean
}

// ============================================================================
// Create Workspace Store
// ============================================================================

export const useWorkspaceStore = create<WorkspaceStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      workspaces: [],
      currentWorkspace: null,
      workspaceDetails: {},
      isLoading: false,
      isCreating: false,
      isUpdating: false,
      isDeleting: false,
      isRestoring: false,
      error: null,

      // ========================================================================
      // Workspace Actions
      // ========================================================================

      listWorkspaces: async (force = false) => {
        // Skip if already loading or data exists (prevents infinite loops)
        // Use force=true to bypass cache (e.g., retry button)
        const { isLoading, workspaces } = get()
        if (isLoading) return
        if (!force && workspaces.length > 0) return

        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await workspaceService.listWorkspaces()

          set((state) => {
            state.workspaces = response.workspaces
            state.isLoading = false
          })

          // Sync workspaces to auth store for workspace switching
          syncToAuthStore(response.workspaces)
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to fetch workspaces'
            state.isLoading = false
          })
          throw error
        }
      },

      getWorkspace: async (workspaceId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await workspaceService.getWorkspace(workspaceId)

          set((state) => {
            state.workspaceDetails[workspaceId] = response.workspace
            state.isLoading = false
          })
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to fetch workspace'
            state.isLoading = false
          })
          throw error
        }
      },

      createWorkspace: async (request) => {
        set((state) => {
          state.isCreating = true
          state.error = null
        })

        try {
          const response = await workspaceService.createWorkspace(request)

          set((state) => {
            // Add new workspace to the list (Creator is always owner)
            state.workspaces.push({ ...response.workspace, role: 'owner' })
            // Cache the workspace details
            state.workspaceDetails[response.workspace.id] = response.workspace
            state.isCreating = false
          })

          // Sync updated workspace list to auth store
          const { workspaces } = get()
          syncToAuthStore(workspaces)

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to create workspace'
            state.isCreating = false
          })
          throw error
        }
      },

      updateWorkspace: async (workspaceId, request) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isUpdating = true
          state.error = null
        })

        try {
          const response = await workspaceService.updateWorkspace(workspaceId, request)

          set((state) => {
            // Update workspace in list
            const workspaceIndex = state.workspaces.findIndex(ws => ws.id === workspaceId)
            if (workspaceIndex !== -1) {
              // Preserve existing role and other list-specific props
              state.workspaces[workspaceIndex] = {
                ...state.workspaces[workspaceIndex],
                ...response.workspace
              }
            }

            // Update workspace in details cache
            if (state.workspaceDetails[workspaceId]) {
              state.workspaceDetails[workspaceId] = { ...state.workspaceDetails[workspaceId], ...response.workspace }
            }

            // Update current workspace if it's the one being updated
            if (state.currentWorkspace?.id === workspaceId) {
              state.currentWorkspace = { ...state.currentWorkspace, ...response.workspace }
            }

            state.isUpdating = false
          })

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to update workspace'
            state.isUpdating = false
          })
          throw error
        }
      },

      deleteWorkspace: async (workspaceId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isDeleting = true
          state.error = null
        })

        try {
          const response = await workspaceService.deleteWorkspace(workspaceId)

          set((state) => {
            // Update workspace in list to suspended status with deletion info
            const workspaceIndex = state.workspaces.findIndex(ws => ws.id === workspaceId)
            if (workspaceIndex !== -1) {
              // Preserve role when updating from data
              state.workspaces[workspaceIndex] = {
                ...state.workspaces[workspaceIndex],
                ...response.workspace
              }
            }

            // Update workspace in details cache
            if (state.workspaceDetails[workspaceId]) {
              state.workspaceDetails[workspaceId] = response.workspace
            }

            // Clear current workspace if it's the one being deleted
            if (state.currentWorkspace?.id === workspaceId) {
              state.currentWorkspace = null
            }

            state.isDeleting = false
          })

          // Sync updated workspace list to auth store
          const { workspaces } = get()
          syncToAuthStore(workspaces)

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to delete workspace'
            state.isDeleting = false
          })
          throw error
        }
      },

      restoreWorkspace: async (workspaceId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isRestoring = true
          state.error = null
        })

        try {
          const response = await workspaceService.restoreWorkspace(workspaceId)

          set((state) => {
            // Update workspace in list to active status
            const workspaceIndex = state.workspaces.findIndex(ws => ws.id === workspaceId)
            if (workspaceIndex !== -1) {
              // Preserve role when updating
              state.workspaces[workspaceIndex] = {
                ...state.workspaces[workspaceIndex],
                ...response.workspace
              }
            }

            // Update workspace in details cache
            if (state.workspaceDetails[workspaceId]) {
              state.workspaceDetails[workspaceId] = response.workspace
            }

            state.isRestoring = false
          })

          // Sync updated workspace list to auth store
          const { workspaces } = get()
          syncToAuthStore(workspaces)

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to restore workspace'
            state.isRestoring = false
          })
          throw error
        }
      },

      // ========================================================================
      // UI State Actions
      // ========================================================================

      setCurrentWorkspace: (workspace) => {
        set((state) => {
          state.currentWorkspace = workspace
        })
      },

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading
        })
      },

      setCreating: (creating) => {
        set((state) => {
          state.isCreating = creating
        })
      },

      setUpdating: (updating) => {
        set((state) => {
          state.isUpdating = updating
        })
      },

      setDeleting: (deleting) => {
        set((state) => {
          state.isDeleting = deleting
        })
      },

      setRestoring: (restoring) => {
        set((state) => {
          state.isRestoring = restoring
        })
      },

      setError: (error) => {
        set((state) => {
          state.error = error
          if (error) {
            state.isLoading = false
            state.isCreating = false
            state.isUpdating = false
            state.isDeleting = false
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      clearWorkspaces: () => {
        set((state) => {
          state.workspaces = []
          state.currentWorkspace = null
          state.workspaceDetails = {}
          state.error = null
        })
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      hasWorkspaces: () => {
        const { workspaces } = get()
        return workspaces.length > 0
      },

      getWorkspaceById: (workspaceId) => {
        const { workspaceDetails, workspaces } = get()

        // Check cache first
        if (workspaceDetails[workspaceId]) {
          return workspaceDetails[workspaceId]
        }

        // Fallback to list
        const workspace = workspaces.find(ws => ws.id === workspaceId)
        if (workspace) {
          // Convert list item to full workspace data
          return {
            id: workspace.id,
            name: workspace.name,
            slug: workspace.name.toLowerCase().replace(/\s+/g, '-'),
            description: '',
            type: workspace.type,
            status: workspace.status,
            permissions: workspace.permissions,
            member_count: workspace.member_count,
            createdAt: workspace.createdAt,
            updatedAt: workspace.updatedAt
          }
        }

        return undefined
      },

      isWorkspaceOwner: (workspaceId) => {
        const workspace = get().getWorkspaceById(workspaceId)
        // This would need to be implemented based on actual user permissions
        // For now, assume user is owner if they can access the workspace
        return workspace !== undefined
      },

      canEditWorkspace: (workspaceId) => {
        // This would check user permissions
        // For now, allow editing if user is workspace owner
        return get().isWorkspaceOwner(workspaceId)
      },

      canDeleteWorkspace: (workspaceId) => {
        // This would check user permissions
        // For now, allow deletion if user is workspace owner
        return get().isWorkspaceOwner(workspaceId)
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const workspaceSelectors = {
  // Core selectors
  workspaces: (state: WorkspaceStoreState) => state.workspaces,
  currentWorkspace: (state: WorkspaceStoreState) => state.currentWorkspace,
  isLoading: (state: WorkspaceStoreState) => state.isLoading,
  isCreating: (state: WorkspaceStoreState) => state.isCreating,
  isUpdating: (state: WorkspaceStoreState) => state.isUpdating,
  isDeleting: (state: WorkspaceStoreState) => state.isDeleting,
  isRestoring: (state: WorkspaceStoreState) => state.isRestoring,
  error: (state: WorkspaceStoreState) => state.error,

  // Computed selectors
  hasWorkspaces: (state: WorkspaceStoreState) => state.workspaces.length > 0,
  workspaceCount: (state: WorkspaceStoreState) => state.workspaces.length,
  storeWorkspaces: (state: WorkspaceStoreState) =>
    state.workspaces.filter(ws => ws.type === 'store'),
  blogWorkspaces: (state: WorkspaceStoreState) =>
    state.workspaces.filter(ws => ws.type === 'blog'),
  servicesWorkspaces: (state: WorkspaceStoreState) =>
    state.workspaces.filter(ws => ws.type === 'services'),
  portfolioWorkspaces: (state: WorkspaceStoreState) =>
    state.workspaces.filter(ws => ws.type === 'portfolio'),
  hasCurrentWorkspace: (state: WorkspaceStoreState) => state.currentWorkspace !== null,
  currentWorkspaceName: (state: WorkspaceStoreState) => state.currentWorkspace?.name || null,

  // Action selectors (stable references)
  listWorkspaces: (state: WorkspaceStoreState) => state.listWorkspaces,
  getWorkspace: (state: WorkspaceStoreState) => state.getWorkspace,
  createWorkspace: (state: WorkspaceStoreState) => state.createWorkspace,
  updateWorkspace: (state: WorkspaceStoreState) => state.updateWorkspace,
  deleteWorkspace: (state: WorkspaceStoreState) => state.deleteWorkspace,
  restoreWorkspace: (state: WorkspaceStoreState) => state.restoreWorkspace,
  setCurrentWorkspace: (state: WorkspaceStoreState) => state.setCurrentWorkspace,
  clearError: (state: WorkspaceStoreState) => state.clearError,
  clearWorkspaces: (state: WorkspaceStoreState) => state.clearWorkspaces,

  // Helper method selectors
  getWorkspaceById: (state: WorkspaceStoreState) => state.getWorkspaceById,
  isWorkspaceOwner: (state: WorkspaceStoreState) => state.isWorkspaceOwner,
  canEditWorkspace: (state: WorkspaceStoreState) => state.canEditWorkspace,
  canDeleteWorkspace: (state: WorkspaceStoreState) => state.canDeleteWorkspace,
}

// ============================================================================
// Default Export
// ============================================================================

export default useWorkspaceStore