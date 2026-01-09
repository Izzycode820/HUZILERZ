/**
 * Route Validation Utilities
 * Validate route formats and parameters
 */

import type { WorkspaceType } from './types'

// Route validation utilities
export const validateRoute = (route: string): boolean => {
  // Validate basic route format
  if (!route.startsWith('/')) return false

  // Validate workspace routes
  const workspaceRegex = /^\/workspace\/[a-zA-Z0-9-]+\/[a-zA-Z0-9-]+\/[a-zA-Z0-9-]+$/
  if (route.includes('/workspace/') && !workspaceRegex.test(route)) return false

  // Validate store routes
  const storeRegex = /^\/store\/[a-zA-Z0-9-]+/
  if (route.includes('/store/') && !storeRegex.test(route)) return false

  return true
}

// Validate workspace type
export const isValidWorkspaceType = (type: string): type is WorkspaceType => {
  return ['store', 'blog', 'services'].includes(type)
}

// Validate workspace ID
export const validateWorkspaceId = (workspaceId: string): boolean => {
  if (!workspaceId || workspaceId.trim() === '') return false
  return /^[a-zA-Z0-9-]+$/.test(workspaceId)
}