/**
 * Route Builder Utilities
 * Helper functions to build dynamic routes
 */

import type { WorkspaceType } from '../core/types'
import { validateWorkspaceId, isValidWorkspaceType } from '../core/validators'
import { WORKSPACE_ROUTES } from '../domains/workspace'
import { STORE_ROUTES } from '../domains/store'

// Enhanced workspace dashboard getter with error handling
export const getWorkspaceDashboard = (type: WorkspaceType, workspaceId: string): string => {
  const dashboardRoutes = {
    store: WORKSPACE_ROUTES.STORE.DASHBOARD,
    blog: WORKSPACE_ROUTES.BLOG.DASHBOARD,
    services: WORKSPACE_ROUTES.SERVICES.DASHBOARD
  } as const

  if (!isValidWorkspaceType(type)) {
    throw new Error(`Invalid workspace type: ${type}`)
  }

  if (!validateWorkspaceId(workspaceId)) {
    throw new Error('Invalid workspace ID format')
  }

  return dashboardRoutes[type](workspaceId)
}

// Helper function to build dynamic routes
export const buildRoute = {
  workspace: {
    dashboard: (workspaceId: string) => WORKSPACE_ROUTES.DASHBOARD(workspaceId),
    store: {
      dashboard: (workspaceId: string) => WORKSPACE_ROUTES.STORE.DASHBOARD(workspaceId),
      products: (workspaceId: string) => WORKSPACE_ROUTES.STORE.PRODUCTS(workspaceId),
      orders: (workspaceId: string) => WORKSPACE_ROUTES.STORE.ORDERS(workspaceId),
      analytics: (workspaceId: string) => WORKSPACE_ROUTES.STORE.ANALYTICS(workspaceId),
      settings: (workspaceId: string) => WORKSPACE_ROUTES.STORE.SETTINGS(workspaceId),
    },
    blog: {
      dashboard: (workspaceId: string) => WORKSPACE_ROUTES.BLOG.DASHBOARD(workspaceId),
      posts: (workspaceId: string) => WORKSPACE_ROUTES.BLOG.POSTS(workspaceId),
      content: (workspaceId: string) => WORKSPACE_ROUTES.BLOG.CONTENT(workspaceId),
      settings: (workspaceId: string) => WORKSPACE_ROUTES.BLOG.SETTINGS(workspaceId),
    },
    services: {
      dashboard: (workspaceId: string) => WORKSPACE_ROUTES.SERVICES.DASHBOARD(workspaceId),
      services: (workspaceId: string) => WORKSPACE_ROUTES.SERVICES.SERVICES(workspaceId),
      bookings: (workspaceId: string) => WORKSPACE_ROUTES.SERVICES.BOOKINGS(workspaceId),
      clients: (workspaceId: string) => WORKSPACE_ROUTES.SERVICES.CLIENTS(workspaceId),
      settings: (workspaceId: string) => WORKSPACE_ROUTES.SERVICES.SETTINGS(workspaceId),
    },
  },
  store: {
    bySlug: (slug: string) => STORE_ROUTES.BY_SLUG(slug),
    product: (slug: string, productId: string) => STORE_ROUTES.PRODUCT(slug, productId),
    cart: (slug: string) => STORE_ROUTES.CART(slug),
    checkout: (slug: string) => STORE_ROUTES.CHECKOUT(slug),
  },
}