/**
 * Workspace Service - Workspace Context Switching and JWT Management
 * Aligned with backend auth_service.py switch_workspace functionality
 */

import BaseService from '../base/BaseService'
import { apiClient } from '../api/client'
import type {
  WorkspaceSwitchRequest,
  WorkspaceSwitchResponse,
  LeaveWorkspaceResponse,
  WorkspaceListResponse,
  AvailableWorkspace,
  WorkspaceAuthContext,
  WorkspaceRole
} from '../../types/authentication/workspace'

// ============================================================================
// Workspace Service (Context Switching Only)
// ============================================================================

export class WorkspaceService extends BaseService {
  constructor() {
    super('auth')
  }

  /**
   * Switch to different workspace context (Industry Standard: Shopify/Stripe/Linear)
   * Backend: POST /api/auth/workspace-switch/
   *
   * v3.0 - NO token regeneration:
   * - Backend validates user has access to workspace
   * - Returns workspace details + membership (role, permissions)
   * - Frontend updates Zustand + sends X-Workspace-Id header on next request
   */
  async switchWorkspace(workspaceId: string): Promise<WorkspaceSwitchResponse> {
    this.validateRequired({ workspace_id: workspaceId }, ['workspace_id'])

    const request: WorkspaceSwitchRequest = { workspace_id: workspaceId }
    const response = await this.post<WorkspaceSwitchResponse>('/workspace-switch/', request)

    // NO token handling - workspace context managed via header (v3.0)
    return response
  }

  /**
   * Leave current workspace context (Industry Standard: Stateless)
   * Backend: POST /api/auth/workspace-leave/
   *
   * v3.0 - NO token regeneration:
   * - Backend logs the event for audit trail
   * - Frontend clears workspace from Zustand
   * - Frontend stops sending X-Workspace-Id header on next request
   */
  async leaveWorkspace(): Promise<LeaveWorkspaceResponse> {
    const response = await this.post<LeaveWorkspaceResponse>('/workspace-leave/')

    // NO token handling - workspace context managed via header (v3.0)
    return response
  }

  /**
   * Get user's available workspaces
   * Backend: GET /api/auth/workspaces/
   */
  async getAvailableWorkspaces(): Promise<WorkspaceListResponse> {
    return this.get<WorkspaceListResponse>('/workspaces/')
  }
}

// ============================================================================
// Workspace Permissions Utility
// ============================================================================

export class WorkspacePermissionsUtil {
  private static ROLE_PERMISSIONS: Record<WorkspaceRole, string[]> = {
    owner: [
      'workspace:manage',
      'workspace:delete',
      'members:manage',
      'members:invite',
      'members:remove',
      'settings:manage',
      'billing:manage',
      'content:create',
      'content:edit',
      'content:delete',
      'analytics:view'
    ],
    admin: [
      'workspace:manage',
      'members:manage',
      'members:invite',
      'members:remove',
      'settings:manage',
      'content:create',
      'content:edit',
      'content:delete',
      'analytics:view'
    ],
    editor: [
      'content:create',
      'content:edit',
      'content:delete'
    ],
    viewer: [
      'content:view'
    ]
  }

  /**
   * Check if role has permission
   */
  static hasPermission(role: WorkspaceRole, permission: string): boolean {
    return this.ROLE_PERMISSIONS[role]?.includes(permission) || false
  }

  /**
   * Check if role has any of the permissions
   */
  static hasAnyPermission(role: WorkspaceRole, permissions: string[]): boolean {
    return permissions.some(permission => this.hasPermission(role, permission))
  }

  /**
   * Check if role has all permissions
   */
  static hasAllPermissions(role: WorkspaceRole, permissions: string[]): boolean {
    return permissions.every(permission => this.hasPermission(role, permission))
  }

  /**
   * Get all permissions for role
   */
  static getPermissions(role: WorkspaceRole): string[] {
    return this.ROLE_PERMISSIONS[role] || []
  }
}

// ============================================================================
// Workspace Context Manager
// ============================================================================

class WorkspaceContextManager {
  private static currentWorkspace: WorkspaceAuthContext | null = null
  private static currentRole: WorkspaceRole | null = null

  /**
   * Set current workspace context
   */
  static setContext(workspace: WorkspaceAuthContext, role: WorkspaceRole): void {
    this.currentWorkspace = workspace
    this.currentRole = role
  }

  /**
   * Get current workspace
   */
  static getCurrentWorkspace(): WorkspaceAuthContext | null {
    return this.currentWorkspace
  }

  /**
   * Get current role
   */
  static getCurrentRole(): WorkspaceRole | null {
    return this.currentRole
  }

  /**
   * Clear workspace context
   */
  static clearContext(): void {
    this.currentWorkspace = null
    this.currentRole = null
  }

  /**
   * Check if user has permission in current workspace
   */
  static hasPermission(permission: string): boolean {
    if (!this.currentRole) return false
    return WorkspacePermissionsUtil.hasPermission(this.currentRole, permission)
  }

  /**
   * Check if current workspace is personal (deprecated - no longer supported)
   */
  static isPersonalWorkspace(): boolean {
    // Workspace types are now: store, blog, services, portfolio
    return false
  }

  /**
   * Check if current workspace is team (deprecated - all workspaces are team workspaces)
   */
  static isTeamWorkspace(): boolean {
    return this.currentWorkspace !== null
  }

  /**
   * Check if user is workspace owner
   */
  static isWorkspaceOwner(): boolean {
    return this.currentRole === 'owner'
  }

  /**
   * Check if user is workspace admin
   */
  static isWorkspaceAdmin(): boolean {
    return this.currentRole === 'admin' || this.currentRole === 'owner'
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const workspaceService = new WorkspaceService()
export { WorkspacePermissionsUtil as WorkspacePermissions, WorkspaceContextManager }
export default workspaceService