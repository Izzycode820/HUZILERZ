/**
 * Workspace Core Types
 * Aligned with backend WORKSPACEPAYLOAD.md API documentation
 * Features: Discriminated unions, type safety, immutable data structures
 */

import { z } from 'zod';

// ============================================================================
// Workspace Status Types
// ============================================================================

export const WorkspaceStatus = {
  ACTIVE: 'active',
  SUSPENDED: 'suspended',
  SUSPENDED_BY_PLAN: 'suspended_by_plan',
  DELETED: 'deleted',
} as const;

export type WorkspaceStatusType = typeof WorkspaceStatus[keyof typeof WorkspaceStatus];

// ============================================================================
// Workspace Type Types
// ============================================================================

export const WorkspaceType = {
  STORE: 'store',
  BLOG: 'blog',
  SERVICES: 'services',
  PORTFOLIO: 'portfolio',
} as const;

export type WorkspaceTypeType = typeof WorkspaceType[keyof typeof WorkspaceType];

// ============================================================================
// Role and Permission Types
// ============================================================================

export const WorkspaceRole = {
  OWNER: 'owner',
  ADMIN: 'admin',
  EDITOR: 'editor',
  VIEWER: 'viewer',
} as const;

export type WorkspaceRoleType = typeof WorkspaceRole[keyof typeof WorkspaceRole];

export const WorkspacePermission = {
  READ: 'read',
  WRITE: 'write',
  ADMIN: 'admin',
  MANAGE_MEMBERS: 'manage_members',
  MANAGE_SETTINGS: 'manage_settings',
  VIEW_ANALYTICS: 'view_analytics',
  CREATE_CONTENT: 'create_content',
  EDIT_CONTENT: 'edit_content',
  DELETE_CONTENT: 'delete_content',
} as const;

export type WorkspacePermissionType = typeof WorkspacePermission[keyof typeof WorkspacePermission];

// ============================================================================
// Core Workspace Data Types
// ============================================================================

/**
 * Workspace data structure matching backend response
 * GET /api/workspaces/<workspace_id>/
 */
/**
 * Deletion info for soft-deleted workspaces
 */
export interface WorkspaceDeletionInfo {
  readonly isDeleted: boolean;
  readonly deletedAt: string;
  readonly scheduledFor: string;
  readonly daysRemaining: number;
  readonly hoursRemaining: number;
  readonly canRestore: boolean;
  readonly gracePeriodDays: number;
  readonly message: string;
}

export interface WorkspaceData {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly description: string;
  readonly type: WorkspaceTypeType;
  readonly status: WorkspaceStatusType;
  readonly permissions: WorkspacePermissionType[];
  readonly member_count: number;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly deletedAt?: string | null;
  readonly deletionScheduledFor?: string | null;
  readonly deletionInfo?: WorkspaceDeletionInfo | null;
}

/**
 * Workspace list item for workspace listing
 * GET /api/workspaces/
 */
export interface WorkspaceListItem {
  readonly id: string;
  readonly name: string;
  readonly type: WorkspaceTypeType;
  readonly status: WorkspaceStatusType;
  readonly role: 'owner' | 'staff';  // User's role in this workspace
  readonly restricted_mode?: boolean; // True if actions are blocked due to subscription
  readonly permissions: WorkspacePermissionType[];
  readonly member_count: number;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly deletedAt?: string | null;
  readonly deletionScheduledFor?: string | null;
  readonly deletionInfo?: WorkspaceDeletionInfo | null;
}

// ============================================================================
// Workspace Request Types
// ============================================================================

/**
 * Create Workspace Request
 * POST /api/workspaces/create/
 */
export const WorkspaceCreateSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  type: z.enum(['store', 'blog', 'services', 'portfolio']),
});

export interface WorkspaceCreateRequest {
  readonly name: string;
  readonly description?: string;
  readonly type: WorkspaceTypeType;
}

/**
 * Update Workspace Request
 * PATCH /api/workspaces/<workspace_id>/update/
 */
export const WorkspaceUpdateSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().optional(),
});

export interface WorkspaceUpdateRequest {
  readonly name?: string;
  readonly description?: string;
}

// ============================================================================
// Workspace Response Types
// ============================================================================

/**
 * List Workspaces Response
 * GET /api/workspaces/
 */
export interface WorkspaceListResponse {
  readonly success: true;
  readonly workspaces: WorkspaceListItem[];
}

/**
 * Create Workspace Response
 * POST /api/workspaces/create/
 */
export interface WorkspaceCreateResponse {
  readonly success: true;
  readonly workspace: WorkspaceData;
  readonly message: string;
}

/**
 * Get Workspace Response
 * GET /api/workspaces/<workspace_id>/
 */
export interface WorkspaceGetResponse {
  readonly success: true;
  readonly workspace: WorkspaceData;
}

/**
 * Update Workspace Response
 * PATCH /api/workspaces/<workspace_id>/update/
 */
export interface WorkspaceUpdateResponse {
  readonly success: true;
  readonly workspace: WorkspaceData;
  readonly message: string;
}

/**
 * Delete Workspace Response
 * DELETE /api/workspaces/<workspace_id>/delete/
 */
export interface WorkspaceDeleteResponse {
  readonly success: true;
  readonly message: string;
  readonly workspace: WorkspaceData;
}

/**
 * Restore Workspace Response
 * POST /api/workspaces/<workspace_id>/restore/
 */
export interface WorkspaceRestoreResponse {
  readonly success: true;
  readonly message: string;
  readonly workspace: WorkspaceData;
}

// ============================================================================
// Workspace Error Types (Simplified)
// ============================================================================

/**
 * Simplified workspace error structure
 * Follows auth.ts pattern with error codes
 */
export interface WorkspaceError {
  readonly success: false;
  readonly error: string;
  readonly code?: string;
  readonly detail?: string;
}

/**
 * Workspace error codes for consistent error handling
 */
export const WORKSPACE_ERRORS = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  LIMIT_REACHED: 'LIMIT_REACHED',
  WORKSPACE_LIMIT_EXCEEDED: 'WORKSPACE_LIMIT_EXCEEDED', // Subscription limit exceeded
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  NOT_FOUND: 'NOT_FOUND',
  INVALID_FIELDS: 'INVALID_FIELDS',
  NO_VALID_FIELDS: 'NO_VALID_FIELDS',
  INVALID_NAME: 'INVALID_NAME',
  // Subscription restriction errors (aligned with backend gating.py)
  WORKSPACE_RESTRICTED: 'WORKSPACE_RESTRICTED',
  WORKSPACE_NONCOMPLIANT: 'WORKSPACE_NONCOMPLIANT',
  SUBSCRIPTION_RESTRICTED: 'SUBSCRIPTION_RESTRICTED',
  WORKSPACE_NOT_FOUND: 'WORKSPACE_NOT_FOUND',
  ACCESS_DENIED: 'ACCESS_DENIED',
} as const;

export type WorkspaceErrorCode = typeof WORKSPACE_ERRORS[keyof typeof WORKSPACE_ERRORS];

// ============================================================================
// Type Guards for Workspace Errors
// ============================================================================

/**
 * Check if error is a workspace error
 */
export function isWorkspaceError(error: unknown): error is WorkspaceError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'success' in error &&
    error.success === false &&
    'error' in error &&
    typeof error.error === 'string'
  );
}

/**
 * Check if error has specific error code
 */
export function hasWorkspaceErrorCode(
  error: unknown,
  code: WorkspaceErrorCode
): boolean {
  return isWorkspaceError(error) && error.code === code;
}

// ============================================================================
// Workspace State Types (Discriminated Unions)
// ============================================================================

/**
 * Workspace Loading State
 */
export interface WorkspaceLoadingState {
  readonly status: 'loading';
  readonly data: null;
  readonly error: null;
  readonly isLoading: true;
}

/**
 * Workspace Success State
 */
export interface WorkspaceSuccessState<T> {
  readonly status: 'success';
  readonly data: T;
  readonly error: null;
  readonly isLoading: false;
}

/**
 * Workspace Error State
 */
export interface WorkspaceErrorState {
  readonly status: 'error';
  readonly data: null;
  readonly error: WorkspaceError;
  readonly isLoading: false;
}

/**
 * Workspace Idle State
 */
export interface WorkspaceIdleState {
  readonly status: 'idle';
  readonly data: null;
  readonly error: null;
  readonly isLoading: false;
}

/**
 * Discriminated Union for Workspace State Management
 */
export type WorkspaceState<T> =
  | WorkspaceLoadingState
  | WorkspaceSuccessState<T>
  | WorkspaceErrorState
  | WorkspaceIdleState;

// ============================================================================
// Type Guards for Workspace States
// ============================================================================

export function isWorkspaceLoadingState(
  state: unknown
): state is WorkspaceLoadingState {
  return (
    typeof state === 'object' &&
    state !== null &&
    'status' in state &&
    state.status === 'loading' &&
    'isLoading' in state &&
    state.isLoading === true
  );
}

export function isWorkspaceSuccessState<T>(
  state: unknown
): state is WorkspaceSuccessState<T> {
  return (
    typeof state === 'object' &&
    state !== null &&
    'status' in state &&
    state.status === 'success' &&
    'data' in state &&
    'isLoading' in state &&
    state.isLoading === false
  );
}

export function isWorkspaceErrorState(
  state: unknown
): state is WorkspaceErrorState {
  return (
    typeof state === 'object' &&
    state !== null &&
    'status' in state &&
    state.status === 'error' &&
    'error' in state &&
    'isLoading' in state &&
    state.isLoading === false
  );
}

export function isWorkspaceIdleState(
  state: unknown
): state is WorkspaceIdleState {
  return (
    typeof state === 'object' &&
    state !== null &&
    'status' in state &&
    state.status === 'idle' &&
    'isLoading' in state &&
    state.isLoading === false
  );
}

// ============================================================================
// Basic Type Guards
// ============================================================================

export const isWorkspaceData = (data: unknown): data is WorkspaceData => {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'name' in data &&
    'type' in data &&
    'status' in data &&
    'permissions' in data
  );
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if workspace has specific permission
 */
export function hasWorkspacePermission(
  workspace: WorkspaceData,
  permission: WorkspacePermissionType
): boolean {
  return workspace.permissions.includes(permission);
}

/**
 * Check if workspace is active
 */
export function isWorkspaceActive(workspace: WorkspaceData): boolean {
  return workspace.status === WorkspaceStatus.ACTIVE;
}

/**
 * Check if user can manage workspace
 */
export function canManageWorkspace(workspace: WorkspaceData): boolean {
  return hasWorkspacePermission(workspace, WorkspacePermission.ADMIN) ||
    hasWorkspacePermission(workspace, WorkspacePermission.MANAGE_SETTINGS);
}

/**
 * Check if user can manage members
 */
export function canManageMembers(workspace: WorkspaceData): boolean {
  return hasWorkspacePermission(workspace, WorkspacePermission.ADMIN) ||
    hasWorkspacePermission(workspace, WorkspacePermission.MANAGE_MEMBERS);
}