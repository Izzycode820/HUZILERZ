/**
 * Workspace Member Management Types
 * Aligned with backend WORKSPACEPAYLOAD.md API documentation
 * Features: Discriminated unions, RBAC validation, rate limiting
 */

import { z } from 'zod';

// ============================================================================
// Member Role Types
// ============================================================================

export const MemberRole = {
  ADMIN: 'admin',
  EDITOR: 'editor',
  VIEWER: 'viewer',
} as const;

export type MemberRoleType = typeof MemberRole[keyof typeof MemberRole];

// ============================================================================
// Member Data Types
// ============================================================================

/**
 * Member data structure from backend
 * GET /api/workspaces/<workspace_id>/members/
 */
export interface MemberData {
  readonly id: string;
  readonly user_id: number;
  readonly user_email: string;
  readonly user_name: string;
  readonly workspace: string;
  readonly role: number;
  readonly role_name: MemberRoleType;
  readonly permissions: string[];
  readonly is_active: boolean;
  readonly joined_at: string;
}

// ============================================================================
// Member Request Types
// ============================================================================

/**
 * Invite Member Request
 * POST /api/workspaces/<workspace_id>/members/invite/
 */
export const MemberInviteSchema = z.object({
  email: z.string().email(),
  role: z.enum(['admin', 'editor', 'viewer']).optional().default('viewer'),
});

export interface MemberInviteRequest {
  readonly email: string;
  readonly role?: MemberRoleType;
}

/**
 * Change Member Role Request
 * PATCH /api/workspaces/<workspace_id>/members/<user_id>/role/
 */
export const MemberRoleChangeSchema = z.object({
  role: z.enum(['admin', 'editor', 'viewer']),
});

export interface MemberRoleChangeRequest {
  readonly role: MemberRoleType;
}

// ============================================================================
// Member Response Types
// ============================================================================

/**
 * List Members Response
 * GET /api/workspaces/<workspace_id>/members/
 */
export interface MemberListResponse {
  readonly success: true;
  readonly members: MemberData[];
  readonly total: number;
}

/**
 * Invite Member Response
 * POST /api/workspaces/<workspace_id>/members/invite/
 */
export interface MemberInviteResponse {
  readonly success: true;
  readonly message: string;
  readonly membership: MemberData;
}

/**
 * Remove Member Response
 * DELETE /api/workspaces/<workspace_id>/members/<user_id>/
 */
export interface MemberRemoveResponse {
  readonly success: true;
  readonly message: string;
  readonly removed_user: {
    readonly user_email: string;
    readonly user_id: number;
  };
}

/**
 * Change Member Role Response
 * PATCH /api/workspaces/<workspace_id>/members/<user_id>/role/
 */
export interface MemberRoleChangeResponse {
  readonly success: true;
  readonly message: string;
  readonly membership: MemberData;
}

// ============================================================================
// Member Error Types (Simplified)
// ============================================================================

/**
 * Simplified member error structure
 * Follows auth.ts pattern with error codes
 */
export interface MemberError {
  readonly success: false;
  readonly error: string;
  readonly code?: string;
  readonly detail?: string;
}

/**
 * Member error codes for consistent error handling
 */
export const MEMBER_ERRORS = {
  MISSING_EMAIL: 'MISSING_EMAIL',
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  ALREADY_MEMBER: 'ALREADY_MEMBER',
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',
  RATE_LIMITED: 'RATE_LIMITED',
  CANNOT_REMOVE_SELF: 'CANNOT_REMOVE_SELF',
  CANNOT_REMOVE_OWNER: 'CANNOT_REMOVE_OWNER',
  NOT_MEMBER: 'NOT_MEMBER',
  MISSING_ROLE: 'MISSING_ROLE',
  CANNOT_CHANGE_OWN_ROLE: 'CANNOT_CHANGE_OWN_ROLE',
  CANNOT_CHANGE_OWNER_ROLE: 'CANNOT_CHANGE_OWNER_ROLE',
  CANNOT_ASSIGN_OWNER_ROLE: 'CANNOT_ASSIGN_OWNER_ROLE',
  ROLE_NOT_FOUND: 'ROLE_NOT_FOUND',
  ONLY_OWNER_CAN_ASSIGN_ADMIN: 'ONLY_OWNER_CAN_ASSIGN_ADMIN',
} as const;

export type MemberErrorCode = typeof MEMBER_ERRORS[keyof typeof MEMBER_ERRORS];

// ============================================================================
// Type Guards for Member Errors
// ============================================================================

/**
 * Check if error is a member error
 */
export function isMemberError(error: unknown): error is MemberError {
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
export function hasMemberErrorCode(
  error: unknown,
  code: MemberErrorCode
): boolean {
  return isMemberError(error) && error.code === code;
}

// ============================================================================
// Member State Types (Discriminated Unions)
// ============================================================================

/**
 * Member Loading State
 */
export interface MemberLoadingState {
  readonly status: 'loading';
  readonly data: null;
  readonly error: null;
  readonly isLoading: true;
}

/**
 * Member Success State
 */
export interface MemberSuccessState<T> {
  readonly status: 'success';
  readonly data: T;
  readonly error: null;
  readonly isLoading: false;
}

/**
 * Member Error State
 */
export interface MemberErrorState {
  readonly status: 'error';
  readonly data: null;
  readonly error: MemberError;
  readonly isLoading: false;
}

/**
 * Member Idle State
 */
export interface MemberIdleState {
  readonly status: 'idle';
  readonly data: null;
  readonly error: null;
  readonly isLoading: false;
}

/**
 * Discriminated Union for Member State Management
 */
export type MemberState<T> =
  | MemberLoadingState
  | MemberSuccessState<T>
  | MemberErrorState
  | MemberIdleState;

// ============================================================================
// Role Mapping Utilities
// ============================================================================

/**
 * Role string to number mapping
 * Based on backend role IDs from WORKSPACEPAYLOAD.md
 */
export const ROLE_MAPPING = {
  [MemberRole.ADMIN]: 2,
  [MemberRole.EDITOR]: 3,
  [MemberRole.VIEWER]: 4,
} as const;

/**
 * Role number to string mapping
 */
export const ROLE_REVERSE_MAPPING = {
  2: MemberRole.ADMIN,
  3: MemberRole.EDITOR,
  4: MemberRole.VIEWER,
} as const;

/**
 * Map role string to role number
 */
export function mapRoleToNumber(role: MemberRoleType): number {
  return ROLE_MAPPING[role];
}

/**
 * Map role number to role string
 */
export function mapRoleToString(role: number): MemberRoleType {
  return ROLE_REVERSE_MAPPING[role as keyof typeof ROLE_REVERSE_MAPPING] || MemberRole.VIEWER;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if user can invite members
 */
export function canInviteMembers(role: MemberRoleType): boolean {
  return role === MemberRole.ADMIN;
}

/**
 * Check if user can remove members
 */
export function canRemoveMembers(role: MemberRoleType): boolean {
  return role === MemberRole.ADMIN;
}

/**
 * Check if user can change member roles
 */
export function canChangeMemberRoles(role: MemberRoleType): boolean {
  return role === MemberRole.ADMIN;
}

/**
 * Check if user can assign admin role
 * Only workspace owners can assign admin role
 */
export function canAssignAdminRole(role: MemberRoleType): boolean {
  return role === MemberRole.ADMIN;
}

/**
 * Get role display name
 */
export function getRoleDisplayName(role: MemberRoleType): string {
  const displayNames = {
    [MemberRole.ADMIN]: 'Admin',
    [MemberRole.EDITOR]: 'Editor',
    [MemberRole.VIEWER]: 'Viewer',
  };
  return displayNames[role];
}

/**
 * Get role description
 */
export function getRoleDescription(role: MemberRoleType): string {
  const descriptions = {
    [MemberRole.ADMIN]: 'Can manage members and settings',
    [MemberRole.EDITOR]: 'Can create and edit content',
    [MemberRole.VIEWER]: 'Read-only access',
  };
  return descriptions[role];
}

// ============================================================================
// Basic Type Guards
// ============================================================================

export const isMemberData = (data: unknown): data is MemberData => {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'user_id' in data &&
    'user_email' in data &&
    'role_name' in data &&
    'permissions' in data
  );
};