/**
 * Workspace Member Service - Member management for workspaces
 * Aligned with backend WORKSPACEPAYLOAD.md endpoints
 */

import BaseService from '../../base/BaseService'
import type {
  MemberData,
  MemberInviteRequest,
  MemberRoleChangeRequest,
  MemberListResponse,
  MemberInviteResponse,
  MemberRemoveResponse,
  MemberRoleChangeResponse,
  MemberError
} from '../../../types/workspace/core'

// ============================================================================
// Workspace Member Service
// ============================================================================

export class WorkspaceMemberService extends BaseService {
  constructor() {
    super('workspaces')
  }

  /**
   * List workspace members
   * Backend: GET /api/workspaces/<workspace_id>/members/
   */
  async listMembers(workspaceId: string): Promise<MemberListResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    return this.get<MemberListResponse>(`/${workspaceId}/members/`)
  }

  /**
   * Invite member to workspace
   * Backend: POST /api/workspaces/<workspace_id>/members/invite/
   */
  async inviteMember(
    workspaceId: string,
    request: MemberInviteRequest
  ): Promise<MemberInviteResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    this.validateRequired(request as unknown as Record<string, unknown>, ['email'])

    return this.post<MemberInviteResponse>(`/${workspaceId}/members/invite/`, request)
  }

  /**
   * Remove member from workspace
   * Backend: DELETE /api/workspaces/<workspace_id>/members/<user_id>/
   */
  async removeMember(workspaceId: string, userId: number): Promise<MemberRemoveResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    if (!userId) {
      throw new Error('User ID is required')
    }

    return this.delete<MemberRemoveResponse>(`/${workspaceId}/members/${userId}/`)
  }

  /**
   * Change member role
   * Backend: PATCH /api/workspaces/<workspace_id>/members/<user_id>/role/
   */
  async changeMemberRole(
    workspaceId: string,
    userId: number,
    request: MemberRoleChangeRequest
  ): Promise<MemberRoleChangeResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    if (!userId) {
      throw new Error('User ID is required')
    }

    this.validateRequired(request as unknown as Record<string, unknown>, ['role'])

    return this.patch<MemberRoleChangeResponse>(`/${workspaceId}/members/${userId}/role/`, request)
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const workspaceMemberService = new WorkspaceMemberService()
export default workspaceMemberService