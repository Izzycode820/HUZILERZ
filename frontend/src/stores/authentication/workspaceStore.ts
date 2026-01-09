/**
 * Workspace Store - Zustand 2024 Best Practices
 * Manages workspace context, switching, and permissions
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  WorkspaceAuthContext,
  WorkspaceSwitchResponse,
  AvailableWorkspace
} from '../../types/authentication'

// ============================================================================
// Workspace Store State Interface
// ============================================================================

interface WorkspaceStoreState {
  // Current Workspace Context
  currentWorkspace: WorkspaceAuthContext | null
  availableWorkspaces: AvailableWorkspace[]

  // UI State
  isLoading: boolean
  isSwitching: boolean
  error: string | null

  // Workspace Switching Flow
  switchInProgress: boolean
  previousWorkspace: WorkspaceAuthContext | null

  // Actions
  setCurrentWorkspace: (workspace: WorkspaceAuthContext | null) => void
  setAvailableWorkspaces: (workspaces: AvailableWorkspace[]) => void
  setSwitchSuccess: (response: WorkspaceSwitchResponse) => void
  startWorkspaceSwitch: (workspaceId: string) => void
  completeSwitchSuccess: (newWorkspace: WorkspaceAuthContext) => void
  cancelWorkspaceSwitch: () => void
  setLoading: (loading: boolean) => void
  setSwitching: (switching: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void

  // Helper Methods
  hasPermission: (permission: string) => boolean
  isWorkspaceOwner: () => boolean
  isWorkspaceAdmin: () => boolean
  canSwitchTo: (workspaceId: string) => boolean
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
      currentWorkspace: null,
      availableWorkspaces: [],
      isLoading: false,
      isSwitching: false,
      error: null,
      switchInProgress: false,
      previousWorkspace: null,

      // ========================================================================
      // Workspace Management Actions
      // ========================================================================

      setCurrentWorkspace: (workspace) => {
        set((state) => {
          state.currentWorkspace = workspace
        })
      },

      setAvailableWorkspaces: (workspaces) => {
        set((state) => {
          state.availableWorkspaces = workspaces
        })
      },

      setSwitchSuccess: (response) => {
        set((state) => {
          if (response.workspace) {
            state.currentWorkspace = response.workspace
          }
          state.isSwitching = false
          state.switchInProgress = false
          state.previousWorkspace = null
          state.error = null
        })
      },

      // ========================================================================
      // Workspace Switching Flow
      // ========================================================================

      startWorkspaceSwitch: (workspaceId) => {
        set((state) => {
          state.switchInProgress = true
          state.isSwitching = true
          state.previousWorkspace = state.currentWorkspace
          state.error = null
        })
      },

      completeSwitchSuccess: (newWorkspace) => {
        set((state) => {
          state.currentWorkspace = newWorkspace
          state.switchInProgress = false
          state.isSwitching = false
          state.previousWorkspace = null
          state.error = null
        })
      },

      cancelWorkspaceSwitch: () => {
        set((state) => {
          state.switchInProgress = false
          state.isSwitching = false
          state.previousWorkspace = null
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

      setSwitching: (switching) => {
        set((state) => {
          state.isSwitching = switching
        })
      },

      setError: (error) => {
        set((state) => {
          state.error = error
          if (error) {
            state.isLoading = false
            state.isSwitching = false
            state.switchInProgress = false
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      hasPermission: (permission) => {
        const { currentWorkspace } = get()
        return currentWorkspace?.permissions?.includes(permission) ?? false
      },

      isWorkspaceOwner: () => {
        const { currentWorkspace } = get()
        return currentWorkspace?.role === 'owner'
      },

      isWorkspaceAdmin: () => {
        const { currentWorkspace } = get()
        return currentWorkspace?.role === 'admin' || currentWorkspace?.role === 'owner'
      },

      canSwitchTo: (workspaceId) => {
        const { availableWorkspaces } = get()
        return availableWorkspaces.some(ws => ws.id === workspaceId)
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

// Stable empty array to avoid infinite loops (RULES.md line 213-296)
const EMPTY_PERMISSIONS: string[] = []

export const workspaceSelectors = {
  // Core selectors
  currentWorkspace: (state: WorkspaceStoreState) => state.currentWorkspace,
  availableWorkspaces: (state: WorkspaceStoreState) => state.availableWorkspaces,
  isLoading: (state: WorkspaceStoreState) => state.isLoading,
  isSwitching: (state: WorkspaceStoreState) => state.isSwitching,
  error: (state: WorkspaceStoreState) => state.error,
  switchInProgress: (state: WorkspaceStoreState) => state.switchInProgress,

  // Computed selectors
  currentWorkspaceName: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.name || null,
  currentWorkspaceId: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.id || null,
  userRole: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.role || null,
  userPermissions: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.permissions || EMPTY_PERMISSIONS,  // ← Stable reference
  availableWorkspaceCount: (state: WorkspaceStoreState) =>
    state.availableWorkspaces.length,
  hasMultipleWorkspaces: (state: WorkspaceStoreState) =>
    state.availableWorkspaces.length > 1,
  isCurrentWorkspaceOwner: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.role === 'owner',
  isCurrentWorkspaceAdmin: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.role === 'admin' || state.currentWorkspace?.role === 'owner',

  // Staff-aware selectors
  isCurrentWorkspaceStaff: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.role !== 'owner',
  isCurrentWorkspaceRestricted: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.restricted_mode === true,
  currentWorkspaceStatus: (state: WorkspaceStoreState) =>
    state.currentWorkspace?.status || null,
}

// ============================================================================
// Default Export
// ============================================================================

export default useWorkspaceStore