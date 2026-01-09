/**
 * Workspace Service - Core workspace management
 * Aligned with backend WORKSPACEPAYLOAD.md endpoints
 */

import BaseService from '../../base/BaseService'
import type {
  WorkspaceData,
  WorkspaceListItem,
  WorkspaceCreateRequest,
  WorkspaceUpdateRequest,
  WorkspaceListResponse,
  WorkspaceCreateResponse,
  WorkspaceGetResponse,
  WorkspaceUpdateResponse,
  WorkspaceDeleteResponse,
  WorkspaceRestoreResponse,
  WorkspaceError
} from '../../../types/workspace/core'

// ============================================================================
// Workspace Service
// ============================================================================

export class WorkspaceService extends BaseService {
  constructor() {
    super('workspaces')
  }

  /**
   * List all workspaces for current user
   * Backend: GET /api/workspaces/
   */
  async listWorkspaces(): Promise<WorkspaceListResponse> {
    return this.get<WorkspaceListResponse>('/')
  }

  /**
   * Get specific workspace details
   * Backend: GET /api/workspaces/<workspace_id>/
   */
  async getWorkspace(workspaceId: string): Promise<WorkspaceGetResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    return this.get<WorkspaceGetResponse>(`/${workspaceId}/`)
  }

  /**
   * Create new workspace
   * Backend: POST /api/workspaces/create/
   */
  async createWorkspace(request: WorkspaceCreateRequest): Promise<WorkspaceCreateResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['name', 'type'])

    return this.post<WorkspaceCreateResponse>('/create/', request)
  }

  /**
   * Update workspace details
   * Backend: PATCH /api/workspaces/<workspace_id>/update/
   */
  async updateWorkspace(
    workspaceId: string,
    request: WorkspaceUpdateRequest
  ): Promise<WorkspaceUpdateResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    const cleanedUpdates = this.cleanData(request as unknown as Record<string, unknown>)

    if (Object.keys(cleanedUpdates).length === 0) {
      throw new Error('No valid fields to update')
    }

    return this.patch<WorkspaceUpdateResponse>(`/${workspaceId}/update/`, cleanedUpdates)
  }

  /**
   * Delete workspace (soft delete)
   * Backend: DELETE /api/workspaces/<workspace_id>/delete/
   */
  async deleteWorkspace(workspaceId: string): Promise<WorkspaceDeleteResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    return this.delete<WorkspaceDeleteResponse>(`/${workspaceId}/delete/`)
  }

  /**
   * Restore soft-deleted workspace
   * Backend: POST /api/workspaces/<workspace_id>/restore/
   */
  async restoreWorkspace(workspaceId: string): Promise<WorkspaceRestoreResponse> {
    if (!workspaceId) {
      throw new Error('Workspace ID is required')
    }

    return this.post<WorkspaceRestoreResponse>(`/${workspaceId}/restore/`, {})
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const workspaceService = new WorkspaceService()
export default workspaceService