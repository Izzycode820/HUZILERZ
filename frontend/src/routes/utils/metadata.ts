/**
 * Route Metadata Utilities
 * Metadata for SEO, breadcrumbs, and page information
 */

import type { RouteMetadata, WorkspaceType } from '../core/types'
import { PUBLIC_ROUTES } from '../core/constants'
import { AUTH_ROUTES } from '../domains/auth'
import { BILLING_ROUTES } from '../domains/billing'
import { WORKSPACE_ROUTES } from '../domains/workspace'

// Route metadata for breadcrumbs and SEO
export const ROUTE_METADATA: Record<string, RouteMetadata> = {
  // Home and Auth
  [PUBLIC_ROUTES.HOME]: {
    title: 'Huzilerz - Build Your Digital Presence',
    breadcrumb: ['Home'],
    description: 'Create stores, blogs, and service platforms with ease'
  },
  [AUTH_ROUTES.ROOT]: {
    title: 'Authentication',
    breadcrumb: ['Home', 'Auth'],
    description: 'Sign in to your account'
  },
  [BILLING_ROUTES.ROOT]: {
    title: 'Billing & Subscriptions',
    breadcrumb: ['Home', 'Billing'],
    description: 'Manage your subscription and billing'
  },

  // Workspace Management
  [WORKSPACE_ROUTES.ROOT]: {
    title: 'Workspace Management',
    breadcrumb: ['Home', 'Workspace'],
    description: 'Manage all your workspaces'
  },
  [WORKSPACE_ROUTES.CREATE]: {
    title: 'Create Workspace',
    breadcrumb: ['Home', 'Workspace', 'Create'],
    description: 'Create a new workspace'
  },

} as const

// Dynamic route metadata generators
export const getWorkspaceMetadata = (
  type: WorkspaceType,
  workspaceId: string,
  section?: string
): RouteMetadata => {
  const baseTitle = `${type.charAt(0).toUpperCase() + type.slice(1)} Workspace`
  const baseBreadcrumb = ['Home', 'Workspace', baseTitle]

  if (section) {
    return {
      title: `${section} - ${baseTitle}`,
      breadcrumb: [...baseBreadcrumb, section],
      description: `Manage your ${type} ${section.toLowerCase()}`
    }
  }

  return {
    title: `${baseTitle} Dashboard`,
    breadcrumb: [...baseBreadcrumb, 'Dashboard'],
    description: `Overview and management for your ${type} workspace`
  }
}

// Helper to get metadata for any route
export const getRouteMetadata = (route: string): RouteMetadata | null => {
  return ROUTE_METADATA[route] || null
}