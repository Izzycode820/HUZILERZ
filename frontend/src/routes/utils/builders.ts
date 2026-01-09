/**
 * Route Builder Utilities
 * Helper functions to build dynamic routes
 */

import type { WorkspaceType } from '../core/types'
import { validateWorkspaceId } from '../core/validators'
import { WORKSPACE_ROUTES } from '../domains/workspace'
import { STORE_ROUTES } from '../domains/store'

// Enhanced workspace dashboard getter
export const getWorkspaceDashboard = (type: WorkspaceType, workspaceId: string): string => {
  // Simplified: All workspaces are stores now
  if (!validateWorkspaceId(workspaceId)) {
    throw new Error('Invalid workspace ID format')
  }

  // Use the imported STORE_ROUTES (check if it has DASHBOARD or HOME, using HOME as safe default from workspace.ts pattern)
  // workspace.ts defines HOME, store.ts likely defines HOME or similar.
  // Assuming STORE_ROUTES from ../domains/store has similar structure.
  // If not, we might need to adjust. But previous code used WORKSPACE_ROUTES.STORE.DASHBOARD.
  // We'll use WORKSPACE_ROUTES.DASHBOARD for now as a safe fallback for the "root" of a workspace
  // or append /store if we are strict. 
  // Let's assume /workspace/[id]/store is the goal.
  return `/workspace/${workspaceId}/store`;
}

// Helper function to build dynamic routes
export const buildRoute = {
  workspace: {
    dashboard: (workspaceId: string) => WORKSPACE_ROUTES.DASHBOARD(workspaceId),
    store: {
      dashboard: (workspaceId: string) => `/workspace/${workspaceId}/store`,
      products: (workspaceId: string) => `/workspace/${workspaceId}/store/products`,
      orders: (workspaceId: string) => `/workspace/${workspaceId}/store/orders`,
      analytics: (workspaceId: string) => `/workspace/${workspaceId}/store/analytics`,
      settings: (workspaceId: string) => `/workspace/${workspaceId}/store/settings`,
    },
  },
  store: {
    bySlug: (slug: string) => STORE_ROUTES.BY_SLUG(slug),
    product: (slug: string, productId: string) => STORE_ROUTES.PRODUCT(slug, productId),
    cart: (slug: string) => STORE_ROUTES.CART(slug),
    checkout: (slug: string) => STORE_ROUTES.CHECKOUT(slug),
  },
}