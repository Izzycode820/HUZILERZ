/**
 * Role-Based Access Control Guard
 * Protects routes based on workspace permissions and roles
 * Uses existing workspace store and permissions
 */

'use client'

import React from 'react'
import { useAuthStore, authSelectors } from '@/stores/authentication/authStore'
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore'
import { AuthLoadingSpinner } from '../shared/AuthLoadingSpinner'

export interface RoleGuardProps {
  children: React.ReactNode
  requiredPermissions?: string[]
  requiredRole?: 'owner' | 'admin' | 'member' | 'viewer'
  requireWorkspace?: boolean
  fallback?: React.ReactNode
  onUnauthorized?: () => void
  mode?: 'any' | 'all' // any = user needs ANY of the permissions, all = user needs ALL permissions
}

export function RoleGuard({
  children,
  requiredPermissions = [],
  requiredRole,
  requireWorkspace = true,
  fallback,
  onUnauthorized,
  mode = 'any'
}: RoleGuardProps) {
  // Auth state
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const isLoading = useAuthStore(authSelectors.isLoading)

  // Workspace state
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace)
  const isWorkspaceLoading = useWorkspaceStore(workspaceSelectors.isLoading)
  const hasPermission = useWorkspaceStore(state => state.hasPermission)
  const isWorkspaceOwner = useWorkspaceStore(state => state.isWorkspaceOwner)
  const isWorkspaceAdmin = useWorkspaceStore(state => state.isWorkspaceAdmin)

  const hasAccess = React.useMemo(() => {
    // Must be authenticated first
    if (!isAuthenticated) return false

    // If workspace is required but not available
    if (requireWorkspace && !currentWorkspace) return false

    // Check role requirements
    if (requiredRole) {
      const currentRole = currentWorkspace?.role

      switch (requiredRole) {
        case 'owner':
          if (!isWorkspaceOwner()) return false
          break
        case 'admin':
          if (!isWorkspaceAdmin()) return false
          break
        case 'member':
          if (!['owner', 'admin', 'member'].includes(currentRole || '')) return false
          break
        case 'viewer':
          // All roles include viewer permissions
          break
        default:
          return false
      }
    }

    // Check permission requirements
    if (requiredPermissions.length > 0) {
      if (mode === 'all') {
        // User must have ALL permissions
        return requiredPermissions.every(permission => hasPermission(permission))
      } else {
        // User must have ANY permission
        return requiredPermissions.some(permission => hasPermission(permission))
      }
    }

    return true
  }, [
    isAuthenticated,
    currentWorkspace,
    requireWorkspace,
    requiredRole,
    requiredPermissions,
    mode,
    hasPermission,
    isWorkspaceOwner,
    isWorkspaceAdmin
  ])

  React.useEffect(() => {
    if (!isLoading && !isWorkspaceLoading && !hasAccess) {
      onUnauthorized?.()
    }
  }, [isLoading, isWorkspaceLoading, hasAccess, onUnauthorized])

  // Show loading while checking permissions
  if (isLoading || isWorkspaceLoading) {
    return fallback || <AuthLoadingSpinner text="Checking permissions..." />
  }

  // Show access denied
  if (!hasAccess) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="mx-auto w-12 h-12 bg-orange-100 dark:bg-orange-900/20 rounded-full flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-orange-600 dark:text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>

          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Access Denied
          </h3>

          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            {requiredRole
              ? `You need ${requiredRole} permissions to access this resource.`
              : requiredPermissions.length > 0
                ? `You don't have the required permissions to access this resource.`
                : 'You don\'t have permission to access this resource.'
            }
          </p>

          <button
            onClick={() => window.history.back()}
            className="text-primary hover:underline text-sm"
          >
            Go back
          </button>
        </div>
      </div>
    )
  }

  // User has access
  return <>{children}</>
}

/**
 * Hook for checking permissions in components
 */
export function useRoleGuard() {
  const isAuthenticated = useAuthStore(authSelectors.isAuthenticated)
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace)
  const hasPermission = useWorkspaceStore(state => state.hasPermission)
  const isWorkspaceOwner = useWorkspaceStore(state => state.isWorkspaceOwner)
  const isWorkspaceAdmin = useWorkspaceStore(state => state.isWorkspaceAdmin)

  const checkPermission = React.useCallback((permission: string) => {
    return isAuthenticated && hasPermission(permission)
  }, [isAuthenticated, hasPermission])

  const checkRole = React.useCallback((role: 'owner' | 'admin' | 'member' | 'viewer') => {
    if (!isAuthenticated || !currentWorkspace) return false

    const currentRole = currentWorkspace.role

    switch (role) {
      case 'owner':
        return isWorkspaceOwner()
      case 'admin':
        return isWorkspaceAdmin()
      case 'member':
        return ['owner', 'admin', 'member'].includes(currentRole || '')
      case 'viewer':
        return true // All roles include viewer permissions
      default:
        return false
    }
  }, [isAuthenticated, currentWorkspace, isWorkspaceOwner, isWorkspaceAdmin])

  const checkPermissions = React.useCallback((
    permissions: string[],
    mode: 'any' | 'all' = 'any'
  ) => {
    if (!isAuthenticated) return false

    if (mode === 'all') {
      return permissions.every(permission => hasPermission(permission))
    } else {
      return permissions.some(permission => hasPermission(permission))
    }
  }, [isAuthenticated, hasPermission])

  return {
    isAuthenticated,
    currentWorkspace,
    currentRole: currentWorkspace?.role || null,
    checkPermission,
    checkRole,
    checkPermissions,
    isWorkspaceOwner: isWorkspaceOwner(),
    isWorkspaceAdmin: isWorkspaceAdmin()
  }
}