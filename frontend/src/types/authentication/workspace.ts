/**
 * Workspace Authentication Context Types
 * ONLY workspace-related types needed for authentication context
 * Aligned with backend WORKSPACEPAYLOAD.md API documentation
 */

// ============================================================================
// Workspace Context for Auth (from API Response + JWT)
// ============================================================================

export interface WorkspaceAuthContext {
  // From API response
  readonly id: string;
  readonly name: string;
  readonly type: 'store' | 'blog' | 'services' | 'portfolio';
  readonly status: 'active' | 'suspended' | 'suspended_by_plan';

  // From JWT claims (workspace_role, workspace_permissions)
  readonly role?: string;
  readonly permissions?: string[];
  readonly is_default?: boolean;

  // Restriction state (from backend gating)
  readonly restricted_mode?: boolean;
}

// ============================================================================
// Workspace Switching for Auth (Industry Standard: Shopify/Stripe/Linear)
// ============================================================================

export interface WorkspaceSwitchRequest {
  readonly workspace_id: string;
}

/**
 * Workspace Switch Response (v3.0 - Header-Based Context)
 *
 * NO JWT regeneration - backend validates access and returns workspace details
 * Frontend updates Zustand + sends X-Workspace-Id header on next request
 *
 * Response includes:
 * - workspace: Full workspace details for UI/routing
 * - membership: User's role and permissions in this workspace
 */
export interface WorkspaceSwitchResponse {
  readonly success: boolean;
  readonly workspace?: {
    readonly id: string;
    readonly name: string;
    readonly type: 'store' | 'blog' | 'services' | 'portfolio';
    readonly status: 'active' | 'suspended' | 'suspended_by_plan';
    readonly owner_id: string;
    readonly created_at: string | null;
    readonly restricted_mode?: boolean;
  };
  readonly membership?: {
    readonly role: 'owner' | 'admin' | 'member' | 'viewer';
    readonly permissions: string[];
    readonly joined_at: string | null;
  };
  readonly message?: string;
  readonly error?: string;
  // Structured error fields for gating (aligned with backend)
  readonly error_code?: 'WORKSPACE_RESTRICTED' | 'WORKSPACE_NONCOMPLIANT' | 'SUBSCRIPTION_RESTRICTED' | 'WORKSPACE_NOT_FOUND' | 'ACCESS_DENIED';
  readonly suggestion?: string;
  readonly reactivation_required?: boolean;
}

/**
 * Leave Workspace Response (v3.0 - Stateless)
 *
 * NO JWT regeneration - endpoint exists only for audit logging
 * Frontend just stops sending X-Workspace-Id header
 */
export interface LeaveWorkspaceResponse {
  readonly success: boolean;
  readonly message?: string;
  readonly error?: string;
}

// ============================================================================
// Available Workspaces for Auth Context
// ============================================================================

export interface AvailableWorkspace {
  readonly id: string;
  readonly name: string;
  readonly type: 'store' | 'blog' | 'services' | 'portfolio';
  readonly is_default: boolean;
  readonly user_role: string;
  readonly role: 'owner' | 'staff';  // Staff-aware role
  readonly status: 'active' | 'suspended' | 'suspended_by_plan';
  readonly restricted_mode?: boolean;
  readonly permissions: string[];
  readonly member_count: number;
  readonly createdAt: string;
  readonly updatedAt: string;
}

export interface WorkspaceListResponse {
  readonly success: boolean;
  readonly workspaces?: readonly AvailableWorkspace[];
  readonly current_workspace_id?: string;
  readonly error?: string;
}

// ============================================================================
// Hook Return Types for Auth Context
// ============================================================================

export interface UseWorkspaceSwitchReturn {
  availableWorkspaces: AvailableWorkspace[];
  currentWorkspace: WorkspaceAuthContext | null;
  isLoading: boolean;
  error: string | null;
  switchWorkspace: (workspaceId: string) => Promise<WorkspaceSwitchResponse>;
  refreshWorkspaces: () => Promise<void>;
  clearError: () => void;
}

// ============================================================================
// Workspace Auth State
// ============================================================================

export interface WorkspaceAuthState {
  current: WorkspaceAuthContext | null;
  available: AvailableWorkspace[];
  isSwitching: boolean;
  error: string | null;
}

// ============================================================================
// Constants for Auth Context
// ============================================================================

export const WORKSPACE_TYPES = {
  STORE: 'store',
  BLOG: 'blog',
  SERVICES: 'services',
  PORTFOLIO: 'portfolio',
} as const;

export const WORKSPACE_ROLES = {
  OWNER: 'owner',
  ADMIN: 'admin',
  EDITOR: 'editor',
  VIEWER: 'viewer',
} as const;

export const WORKSPACE_STATUS = {
  ACTIVE: 'active',
  SUSPENDED: 'suspended',
  SUSPENDED_BY_PLAN: 'suspended_by_plan',
} as const;

export type WorkspaceType = typeof WORKSPACE_TYPES[keyof typeof WORKSPACE_TYPES];
export type WorkspaceRole = typeof WORKSPACE_ROLES[keyof typeof WORKSPACE_ROLES];
export type WorkspaceStatus = typeof WORKSPACE_STATUS[keyof typeof WORKSPACE_STATUS];