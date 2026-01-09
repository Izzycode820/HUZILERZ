/**
 * Workspace Management Hook - 2024 Best Practices with Zustand
 * Custom hook layer for workspace store - provides clean interface and performance
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { useWorkspaceStore, workspaceSelectors } from '../../../stores/workspace/core/workspaceManagementStore'
import type {
  WorkspaceCreateRequest,
  WorkspaceUpdateRequest,
  WorkspaceCreateResponse,
  WorkspaceUpdateResponse,
  WorkspaceDeleteResponse,
  WorkspaceRestoreResponse
} from '../../../types/workspace/core'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseWorkspaceManagementReturn {
  // State selectors (performance optimized)
  workspaces: ReturnType<typeof workspaceSelectors.workspaces>
  isLoading: boolean
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
  isRestoring: boolean
  error: string | null

  // Computed state
  hasWorkspaces: boolean
  workspaceCount: number

  // Actions (stable references)
  listWorkspaces: (force?: boolean) => Promise<void>
  getWorkspace: (workspaceId: string) => Promise<void>
  createWorkspace: (request: WorkspaceCreateRequest) => Promise<WorkspaceCreateResponse>
  updateWorkspace: (workspaceId: string, request: WorkspaceUpdateRequest) => Promise<WorkspaceUpdateResponse>
  deleteWorkspace: (workspaceId: string) => Promise<WorkspaceDeleteResponse>
  restoreWorkspace: (workspaceId: string) => Promise<WorkspaceRestoreResponse>
  clearError: () => void
  clearWorkspaces: () => void

  // Helper methods
  getWorkspaceById: ReturnType<typeof workspaceSelectors.getWorkspaceById>
  isWorkspaceOwner: (workspaceId: string) => boolean
  canEditWorkspace: (workspaceId: string) => boolean
  canDeleteWorkspace: (workspaceId: string) => boolean
}

// ============================================================================
// Main Workspace Hook
// ============================================================================

export function useWorkspaceManagement(): UseWorkspaceManagementReturn {
  // Selective store subscriptions (performance optimized)
  const workspaces = useWorkspaceStore(workspaceSelectors.workspaces)
  const isLoading = useWorkspaceStore(workspaceSelectors.isLoading)
  const isCreating = useWorkspaceStore(workspaceSelectors.isCreating)
  const isUpdating = useWorkspaceStore(workspaceSelectors.isUpdating)
  const isDeleting = useWorkspaceStore(workspaceSelectors.isDeleting)
  const isRestoring = useWorkspaceStore(workspaceSelectors.isRestoring)
  const error = useWorkspaceStore(workspaceSelectors.error)
  const hasWorkspaces = useWorkspaceStore(workspaceSelectors.hasWorkspaces)
  const workspaceCount = useWorkspaceStore(workspaceSelectors.workspaceCount)

  // Store actions (use stable selectors for performance - prevent infinite loops)
  const listWorkspacesAction = useWorkspaceStore(workspaceSelectors.listWorkspaces)
  const getWorkspaceAction = useWorkspaceStore(workspaceSelectors.getWorkspace)
  const createWorkspaceAction = useWorkspaceStore(workspaceSelectors.createWorkspace)
  const updateWorkspaceAction = useWorkspaceStore(workspaceSelectors.updateWorkspace)
  const deleteWorkspaceAction = useWorkspaceStore(workspaceSelectors.deleteWorkspace)
  const restoreWorkspaceAction = useWorkspaceStore(workspaceSelectors.restoreWorkspace)
  const clearError = useWorkspaceStore(workspaceSelectors.clearError)
  const clearWorkspaces = useWorkspaceStore(workspaceSelectors.clearWorkspaces)
  const getWorkspaceById = useWorkspaceStore(workspaceSelectors.getWorkspaceById)
  const isWorkspaceOwner = useWorkspaceStore(workspaceSelectors.isWorkspaceOwner)
  const canEditWorkspace = useWorkspaceStore(workspaceSelectors.canEditWorkspace)
  const canDeleteWorkspace = useWorkspaceStore(workspaceSelectors.canDeleteWorkspace)

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const listWorkspaces = useCallback(async (force?: boolean): Promise<void> => {
    return listWorkspacesAction(force)
  }, [listWorkspacesAction])

  const getWorkspace = useCallback(async (workspaceId: string): Promise<void> => {
    return getWorkspaceAction(workspaceId)
  }, [getWorkspaceAction])

  const createWorkspace = useCallback(async (request: WorkspaceCreateRequest): Promise<WorkspaceCreateResponse> => {
    return createWorkspaceAction(request)
  }, [createWorkspaceAction])

  const updateWorkspace = useCallback(async (workspaceId: string, request: WorkspaceUpdateRequest): Promise<WorkspaceUpdateResponse> => {
    return updateWorkspaceAction(workspaceId, request)
  }, [updateWorkspaceAction])

  const deleteWorkspace = useCallback(async (workspaceId: string): Promise<WorkspaceDeleteResponse> => {
    return deleteWorkspaceAction(workspaceId)
  }, [deleteWorkspaceAction])

  const restoreWorkspace = useCallback(async (workspaceId: string): Promise<WorkspaceRestoreResponse> => {
    return restoreWorkspaceAction(workspaceId)
  }, [restoreWorkspaceAction])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    workspaces,
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    isRestoring,
    error,

    // Computed state
    hasWorkspaces,
    workspaceCount,

    // Actions (stable)
    listWorkspaces,
    getWorkspace,
    createWorkspace,
    updateWorkspace,
    deleteWorkspace,
    restoreWorkspace,
    clearError,
    clearWorkspaces,

    // Helper methods
    getWorkspaceById,
    isWorkspaceOwner,
    canEditWorkspace,
    canDeleteWorkspace,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for workspace status only - minimal re-renders
 */
export function useWorkspaceStatus() {
  return {
    hasWorkspaces: useWorkspaceStore(workspaceSelectors.hasWorkspaces),
    isLoading: useWorkspaceStore(workspaceSelectors.isLoading),
    isCreating: useWorkspaceStore(workspaceSelectors.isCreating),
    isUpdating: useWorkspaceStore(workspaceSelectors.isUpdating),
    isDeleting: useWorkspaceStore(workspaceSelectors.isDeleting),
    isRestoring: useWorkspaceStore(workspaceSelectors.isRestoring),
    error: useWorkspaceStore(workspaceSelectors.error)
  }
}

/**
 * Hook for workspace data only - minimal re-renders
 */
export function useWorkspaceData() {
  return {
    workspaces: useWorkspaceStore(workspaceSelectors.workspaces),
    workspaceCount: useWorkspaceStore(workspaceSelectors.workspaceCount)
  }
}

/**
 * Hook for workspace actions only - no reactive state
 */
export function useWorkspaceActions() {
  const clearError = useWorkspaceStore(workspaceSelectors.clearError)
  const clearWorkspaces = useWorkspaceStore(workspaceSelectors.clearWorkspaces)

  return { clearError, clearWorkspaces }
}

// ============================================================================
// Default Export
// ============================================================================

export default useWorkspaceManagement