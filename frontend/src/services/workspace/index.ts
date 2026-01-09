/**
 * Workspace Services Index
 * Main entry point for all workspace-related services
 */

// ============================================================================
// Core Services (Most commonly used)
// ============================================================================

export {
  workspaceService,
  workspaceMemberService,
} from './core'

// ============================================================================
// Service Types
// ============================================================================

export type {
  WorkspaceService,
  WorkspaceMemberService,
} from './core'