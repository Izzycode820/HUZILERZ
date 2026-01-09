/**
 * Workspace Core Types Index
 * Optimized exports to prevent circular dependencies and improve tree-shaking
 * For complex types, import directly from specific modules
 */

// ============================================================================
// CORE TYPES ONLY - Most commonly used
// ============================================================================

// Essential workspace types (no re-export of everything)
export type {
  // Workspace CRUD types
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
  WorkspaceDeletionInfo,

  // Workspace state (discriminated union only)
  WorkspaceState,
  WorkspaceError,
} from './workspaceManagement';

export type {
  // Member management types
  MemberData,
  MemberInviteRequest,
  MemberRoleChangeRequest,
  MemberListResponse,
  MemberInviteResponse,
  MemberRemoveResponse,
  MemberRoleChangeResponse,
  MemberError,
  MemberState,
} from './members';

export {
  // Type guards from workspace
  isWorkspaceData,
  isWorkspaceError,
} from './workspaceManagement';

export {
  // Type guards from members
  isMemberData,
  isMemberError,
} from './members';

// ============================================================================
// SPECIALIZED IMPORTS - Import directly from modules for these:
// ============================================================================
// import { WorkspaceCreateSchema, WorkspaceUpdateSchema } from './workspace'
// import { MemberInviteSchema, MemberRoleChangeSchema } from './members'
// import { isWorkspaceValidationError, isMemberMissingEmailError } from './workspace'

// ============================================================================
// Common Workspace Types
// ============================================================================

export interface WorkspaceConfig {
  readonly apiBaseUrl: string;
  readonly enableMemberManagement: boolean;
  readonly maxWorkspaces: number;
  readonly defaultWorkspaceType: 'store' | 'blog' | 'services' | 'portfolio';
  readonly enableAnalytics: boolean;
  readonly enableAuditLogging: boolean;
}

export interface WorkspaceEvent {
  readonly type: 'workspace_created' | 'workspace_updated' | 'workspace_deleted' | 'member_invited' | 'member_removed' | 'role_changed';
  readonly payload?: unknown;
  readonly timestamp: number;
  readonly workspaceId: string;
}

export interface WorkspaceEventHandler {
  (event: WorkspaceEvent): void;
}

// ============================================================================
// Constants
// ============================================================================
// Performance optimized with const assertions
export const WORKSPACE_CONSTANTS = {
  MAX_WORKSPACE_NAME_LENGTH: 255,
  MAX_WORKSPACE_DESCRIPTION_LENGTH: 1000,
  INVITE_RATE_LIMIT_MINUTES: 20,
  DEFAULT_WORKSPACE_TYPE: 'store',
  WORKSPACE_SWITCH_TIMEOUT: 10 * 1000, // 10 seconds
} as const;

export const WORKSPACE_STORAGE_KEYS = {
  CURRENT_WORKSPACE: 'huzilerz_current_workspace',
  WORKSPACE_LIST: 'huzilerz_workspace_list',
  WORKSPACE_PREFERENCES: 'huzilerz_workspace_preferences',
} as const;

