/**
 * Workspace Members Store - Member management for workspaces
 * Zustand 2024 Best Practices
 * Manages workspace member operations and state
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  MemberData,
  MemberInviteRequest,
  MemberRoleChangeRequest,
  MemberInviteResponse,
  MemberRemoveResponse,
  MemberRoleChangeResponse
} from '../../../types/workspace/core'
import { mapRoleToNumber } from '../../../types/workspace/core/members'
import workspaceMemberService from '../../../services/workspace/core/members'

// ============================================================================
// Workspace Members Store State Interface
// ============================================================================

interface WorkspaceMembersStoreState {
  // Member Data
  members: Record<string, MemberData[]> // workspaceId -> members
  pendingInvites: Record<string, MemberData[]> // workspaceId -> pending invites

  // UI State
  isLoading: boolean
  isInviting: boolean
  isRemoving: boolean
  isChangingRole: boolean
  error: string | null

  // Actions - Member Management
  listMembers: (workspaceId: string) => Promise<void>
  inviteMember: (workspaceId: string, request: MemberInviteRequest) => Promise<MemberInviteResponse>
  removeMember: (workspaceId: string, userId: number) => Promise<MemberRemoveResponse>
  changeMemberRole: (workspaceId: string, userId: number, request: MemberRoleChangeRequest) => Promise<MemberRoleChangeResponse>

  // UI Actions
  setLoading: (loading: boolean) => void
  setInviting: (inviting: boolean) => void
  setRemoving: (removing: boolean) => void
  setChangingRole: (changingRole: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearMembers: (workspaceId?: string) => void

  // Helper Methods
  getMembersByWorkspace: (workspaceId: string) => MemberData[]
  getPendingInvitesByWorkspace: (workspaceId: string) => MemberData[]
  isMember: (workspaceId: string, userId: number) => boolean
  canManageMembers: (workspaceId: string) => boolean
  canChangeMemberRole: (workspaceId: string) => boolean
}

// ============================================================================
// Create Workspace Members Store
// ============================================================================

export const useWorkspaceMembersStore = create<WorkspaceMembersStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      members: {},
      pendingInvites: {},
      isLoading: false,
      isInviting: false,
      isRemoving: false,
      isChangingRole: false,
      error: null,

      // ========================================================================
      // Member Actions
      // ========================================================================

      listMembers: async (workspaceId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const response = await workspaceMemberService.listMembers(workspaceId)

          set((state) => {
            state.members[workspaceId] = response.members
            state.isLoading = false
          })
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to fetch members'
            state.isLoading = false
          })
          throw error
        }
      },

      inviteMember: async (workspaceId, request) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isInviting = true
          state.error = null
        })

        try {
          const response = await workspaceMemberService.inviteMember(workspaceId, request)

          set((state) => {
            // Add to pending invites
            if (!state.pendingInvites[workspaceId]) {
              state.pendingInvites[workspaceId] = []
            }

            const pendingMember: MemberData = {
              id: 'pending-' + Date.now(), // Generate unique ID for pending
              user_id: 0, // Use 0 as placeholder for pending
              user_email: request.email,
              user_name: '', // No name for pending invites
              workspace: workspaceId,
              role: 3, // Default to viewer role
              role_name: request.role || 'viewer',
              permissions: [],
              is_active: false,
              joined_at: new Date().toISOString()
            }

            state.pendingInvites[workspaceId].push(pendingMember)
            state.isInviting = false
          })

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to invite member'
            state.isInviting = false
          })
          throw error
        }
      },

      removeMember: async (workspaceId, userId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        if (!userId) {
          throw new Error('User ID is required')
        }

        set((state) => {
          state.isRemoving = true
          state.error = null
        })

        try {
          const response = await workspaceMemberService.removeMember(workspaceId, userId)

          set((state) => {
            // Remove member from members list
            if (state.members[workspaceId]) {
              state.members[workspaceId] = state.members[workspaceId].filter(
                member => member.user_id !== userId
              )
            }

            // Remove from pending invites if present
            if (state.pendingInvites[workspaceId]) {
              state.pendingInvites[workspaceId] = state.pendingInvites[workspaceId].filter(
                invite => invite.user_id !== userId
              )
            }

            state.isRemoving = false
          })

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to remove member'
            state.isRemoving = false
          })
          throw error
        }
      },

      changeMemberRole: async (workspaceId, userId, request) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        if (!userId) {
          throw new Error('User ID is required')
        }

        set((state) => {
          state.isChangingRole = true
          state.error = null
        })

        try {
          const response = await workspaceMemberService.changeMemberRole(workspaceId, userId, request)

          set((state) => {
            // Update member role in members list
            if (state.members[workspaceId]) {
              const memberIndex = state.members[workspaceId].findIndex(
                member => member.user_id === userId
              )
              if (memberIndex !== -1) {
                state.members[workspaceId][memberIndex].role = mapRoleToNumber(request.role)
                state.members[workspaceId][memberIndex].role_name = request.role
              }
            }

            // Update role in pending invites if present
            if (state.pendingInvites[workspaceId]) {
              const inviteIndex = state.pendingInvites[workspaceId].findIndex(
                invite => invite.user_id === userId
              )
              if (inviteIndex !== -1) {
                state.pendingInvites[workspaceId][inviteIndex].role = mapRoleToNumber(request.role)
                state.pendingInvites[workspaceId][inviteIndex].role_name = request.role
              }
            }

            state.isChangingRole = false
          })

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to change member role'
            state.isChangingRole = false
          })
          throw error
        }
      },

      // ========================================================================
      // UI State Actions
      // ========================================================================

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading
        })
      },

      setInviting: (inviting) => {
        set((state) => {
          state.isInviting = inviting
        })
      },

      setRemoving: (removing) => {
        set((state) => {
          state.isRemoving = removing
        })
      },

      setChangingRole: (changingRole) => {
        set((state) => {
          state.isChangingRole = changingRole
        })
      },

      setError: (error) => {
        set((state) => {
          state.error = error
          if (error) {
            state.isLoading = false
            state.isInviting = false
            state.isRemoving = false
            state.isChangingRole = false
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      clearMembers: (workspaceId) => {
        set((state) => {
          if (workspaceId) {
            delete state.members[workspaceId]
            delete state.pendingInvites[workspaceId]
          } else {
            state.members = {}
            state.pendingInvites = {}
          }
          state.error = null
        })
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      getMembersByWorkspace: (workspaceId) => {
        const { members } = get()
        return members[workspaceId] || []
      },

      getPendingInvitesByWorkspace: (workspaceId) => {
        const { pendingInvites } = get()
        return pendingInvites[workspaceId] || []
      },

      isMember: (workspaceId, userId) => {
        const members = get().getMembersByWorkspace(workspaceId)
        return members.some(member => member.user_id === userId)
      },

      canManageMembers: (workspaceId) => {
        // This would check user permissions
        // For now, assume workspace owners and admins can manage members
        // This would need integration with auth store
        return true // Placeholder
      },

      canChangeMemberRole: (workspaceId) => {
        // This would check user permissions
        // For now, assume workspace owners can change roles
        // This would need integration with auth store
        return true // Placeholder
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const workspaceMembersSelectors = {
  // Core selectors
  members: (state: WorkspaceMembersStoreState) => state.members,
  pendingInvites: (state: WorkspaceMembersStoreState) => state.pendingInvites,
  isLoading: (state: WorkspaceMembersStoreState) => state.isLoading,
  isInviting: (state: WorkspaceMembersStoreState) => state.isInviting,
  isRemoving: (state: WorkspaceMembersStoreState) => state.isRemoving,
  isChangingRole: (state: WorkspaceMembersStoreState) => state.isChangingRole,
  error: (state: WorkspaceMembersStoreState) => state.error,

  // Computed selectors
  hasMembers: (state: WorkspaceMembersStoreState, workspaceId: string) =>
    (state.members[workspaceId]?.length || 0) > 0,
  hasPendingInvites: (state: WorkspaceMembersStoreState, workspaceId: string) =>
    (state.pendingInvites[workspaceId]?.length || 0) > 0,
  memberCount: (state: WorkspaceMembersStoreState, workspaceId: string) =>
    state.members[workspaceId]?.length || 0,
  pendingInviteCount: (state: WorkspaceMembersStoreState, workspaceId: string) =>
    state.pendingInvites[workspaceId]?.length || 0,

  // Action selectors (stable references)
  listMembers: (state: WorkspaceMembersStoreState) => state.listMembers,
  inviteMember: (state: WorkspaceMembersStoreState) => state.inviteMember,
  removeMember: (state: WorkspaceMembersStoreState) => state.removeMember,
  changeMemberRole: (state: WorkspaceMembersStoreState) => state.changeMemberRole,
  clearError: (state: WorkspaceMembersStoreState) => state.clearError,
  clearMembers: (state: WorkspaceMembersStoreState) => state.clearMembers,

  // Helper method selectors
  getMembersByWorkspace: (state: WorkspaceMembersStoreState) => state.getMembersByWorkspace,
  getPendingInvitesByWorkspace: (state: WorkspaceMembersStoreState) => state.getPendingInvitesByWorkspace,
  isMember: (state: WorkspaceMembersStoreState) => state.isMember,
  canManageMembers: (state: WorkspaceMembersStoreState) => state.canManageMembers,
  canChangeMemberRole: (state: WorkspaceMembersStoreState) => state.canChangeMemberRole,
}

// ============================================================================
// Default Export
// ============================================================================

export default useWorkspaceMembersStore