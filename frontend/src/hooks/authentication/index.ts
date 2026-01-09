/**
 * Authentication Hooks Index - 2024 Best Practices
 * Clean exports for all authentication-related hooks
 * Following patterns: direct exports only, no re-exports of internals
 */

// ============================================================================
// Main Authentication Hooks
// ============================================================================

export {
  useAuth,
  useAuthStatus,
  useAuthUser,
  useAuthActions,
  type UseAuthReturn
} from './useAuth'

export {
  useWorkspace,
  useCurrentWorkspace,
  useWorkspacePermissions,
  useWorkspaceSwitcher,
  type UseWorkspaceReturn
} from './useWorkspace'

export {
  useSessions,
  useCurrentSession,
  useSessionsList,
  useSessionTermination,
  type UseSessionsReturn
} from './useSessions'

export {
  useEmail,
  useEmailVerificationStatus,
  useEmailVerification,
  usePasswordReset,
  type UseEmailReturn
} from './useEmail'

export {
  useOAuth2,
  useOAuth2Providers,
  useOAuth2Flow,
  useOAuth2Status,
  type UseOAuth2Return
} from './useOAuth2'

// ============================================================================
// Default Export - Main Authentication Hook
// ============================================================================

export { default } from './useAuth'