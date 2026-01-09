/**
 * Workspace Members Hook - 2024 Best Practices with Zustand
 * Custom hook layer for members store - provides clean interface and performance
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { useWorkspaceMembersStore, workspaceMembersSelectors } from '../../../stores/workspace/core/membersStore'
import type {
  MemberInviteRequest,
  MemberRoleChangeRequest,
  MemberInviteResponse,
  MemberRemoveResponse,
  MemberRoleChangeResponse
} from '../../../types/workspace/core'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseMembersReturn {
  // State selectors (performance optimized)
  members: ReturnType<typeof workspaceMembersSelectors.members>
  pendingInvites: ReturnType<typeof workspaceMembersSelectors.pendingInvites>
  isLoading: boolean
  isInviting: boolean
  isRemoving: boolean
  isChangingRole: boolean
  error: string | null

  // Computed state
  hasMembers: (workspaceId: string) => boolean
  hasPendingInvites: (workspaceId: string) => boolean
  memberCount: (workspaceId: string) => number
  pendingInviteCount: (workspaceId: string) => number

  // Actions (stable references)
  listMembers: (workspaceId: string) => Promise<void>
  inviteMember: (workspaceId: string, request: MemberInviteRequest) => Promise<MemberInviteResponse>
  removeMember: (workspaceId: string, userId: number) => Promise<MemberRemoveResponse>
  changeMemberRole: (workspaceId: string, userId: number, request: MemberRoleChangeRequest) => Promise<MemberRoleChangeResponse>
  clearError: () => void
  clearMembers: (workspaceId?: string) => void

  // Helper methods
  getMembersByWorkspace: ReturnType<typeof workspaceMembersSelectors.getMembersByWorkspace>
  getPendingInvitesByWorkspace: ReturnType<typeof workspaceMembersSelectors.getPendingInvitesByWorkspace>
  isMember: ReturnType<typeof workspaceMembersSelectors.isMember>
  canManageMembers: ReturnType<typeof workspaceMembersSelectors.canManageMembers>
  canChangeMemberRole: ReturnType<typeof workspaceMembersSelectors.canChangeMemberRole>
}

// ============================================================================
// Main Members Hook
// ============================================================================

export function useMembers(): UseMembersReturn {
  // Selective store subscriptions (performance optimized)
  const members = useWorkspaceMembersStore(workspaceMembersSelectors.members)
  const pendingInvites = useWorkspaceMembersStore(workspaceMembersSelectors.pendingInvites)
  const isLoading = useWorkspaceMembersStore(workspaceMembersSelectors.isLoading)
  const isInviting = useWorkspaceMembersStore(workspaceMembersSelectors.isInviting)
  const isRemoving = useWorkspaceMembersStore(workspaceMembersSelectors.isRemoving)
  const isChangingRole = useWorkspaceMembersStore(workspaceMembersSelectors.isChangingRole)
  const error = useWorkspaceMembersStore(workspaceMembersSelectors.error)

  // Store actions (use stable selectors for performance)
  const listMembersAction = useWorkspaceMembersStore(workspaceMembersSelectors.listMembers)
  const inviteMemberAction = useWorkspaceMembersStore(workspaceMembersSelectors.inviteMember)
  const removeMemberAction = useWorkspaceMembersStore(workspaceMembersSelectors.removeMember)
  const changeMemberRoleAction = useWorkspaceMembersStore(workspaceMembersSelectors.changeMemberRole)
  const clearError = useWorkspaceMembersStore(workspaceMembersSelectors.clearError)
  const clearMembers = useWorkspaceMembersStore(workspaceMembersSelectors.clearMembers)
  const getMembersByWorkspace = useWorkspaceMembersStore(workspaceMembersSelectors.getMembersByWorkspace)
  const getPendingInvitesByWorkspace = useWorkspaceMembersStore(workspaceMembersSelectors.getPendingInvitesByWorkspace)
  const isMember = useWorkspaceMembersStore(workspaceMembersSelectors.isMember)
  const canManageMembers = useWorkspaceMembersStore(workspaceMembersSelectors.canManageMembers)
  const canChangeMemberRole = useWorkspaceMembersStore(workspaceMembersSelectors.canChangeMemberRole)

  // Computed selectors with parameters
  const hasMembers = useCallback((workspaceId: string): boolean => {
    return (members[workspaceId]?.length || 0) > 0
  }, [members])

  const hasPendingInvites = useCallback((workspaceId: string): boolean => {
    return (pendingInvites[workspaceId]?.length || 0) > 0
  }, [pendingInvites])

  const memberCount = useCallback((workspaceId: string): number => {
    return members[workspaceId]?.length || 0
  }, [members])

  const pendingInviteCount = useCallback((workspaceId: string): number => {
    return pendingInvites[workspaceId]?.length || 0
  }, [pendingInvites])

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const listMembers = useCallback(async (workspaceId: string): Promise<void> => {
    return listMembersAction(workspaceId)
  }, [listMembersAction])

  const inviteMember = useCallback(async (workspaceId: string, request: MemberInviteRequest): Promise<MemberInviteResponse> => {
    return inviteMemberAction(workspaceId, request)
  }, [inviteMemberAction])

  const removeMember = useCallback(async (workspaceId: string, userId: number): Promise<MemberRemoveResponse> => {
    return removeMemberAction(workspaceId, userId)
  }, [removeMemberAction])

  const changeMemberRole = useCallback(async (workspaceId: string, userId: number, request: MemberRoleChangeRequest): Promise<MemberRoleChangeResponse> => {
    return changeMemberRoleAction(workspaceId, userId, request)
  }, [changeMemberRoleAction])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    members,
    pendingInvites,
    isLoading,
    isInviting,
    isRemoving,
    isChangingRole,
    error,

    // Computed state
    hasMembers,
    hasPendingInvites,
    memberCount,
    pendingInviteCount,

    // Actions (stable)
    listMembers,
    inviteMember,
    removeMember,
    changeMemberRole,
    clearError,
    clearMembers,

    // Helper methods
    getMembersByWorkspace,
    getPendingInvitesByWorkspace,
    isMember,
    canManageMembers,
    canChangeMemberRole,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for members status only - minimal re-renders
 */
export function useMembersStatus() {
  return {
    isLoading: useWorkspaceMembersStore(workspaceMembersSelectors.isLoading),
    isInviting: useWorkspaceMembersStore(workspaceMembersSelectors.isInviting),
    isRemoving: useWorkspaceMembersStore(workspaceMembersSelectors.isRemoving),
    isChangingRole: useWorkspaceMembersStore(workspaceMembersSelectors.isChangingRole),
    error: useWorkspaceMembersStore(workspaceMembersSelectors.error)
  }
}

/**
 * Hook for members data only - minimal re-renders
 */
export function useMembersData() {
  return {
    members: useWorkspaceMembersStore(workspaceMembersSelectors.members),
    pendingInvites: useWorkspaceMembersStore(workspaceMembersSelectors.pendingInvites)
  }
}

/**
 * Hook for members actions only - no reactive state
 */
export function useMembersActions() {
  const clearError = useWorkspaceMembersStore(workspaceMembersSelectors.clearError)
  const clearMembers = useWorkspaceMembersStore(workspaceMembersSelectors.clearMembers)

  return { clearError, clearMembers }
}

// ============================================================================
// Default Export
// ============================================================================

export default useMembers