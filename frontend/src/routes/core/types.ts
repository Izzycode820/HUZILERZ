/**
 * Core Route Types
 * Type definitions for route parameters and workspace types
 */

// Type helpers for route parameters
export type RouteParams = {
  workspaceId?: string
  storeSlug?: string
  productId?: string
  orderId?: string
}

// Workspace type for type safety
export type WorkspaceType = 'store' | 'blog' | 'services'

// Route metadata structure
export interface RouteMetadata {
  title: string
  breadcrumb: string[]
  description: string
}

// Navigation item structure
export interface NavigationItem {
  label: string
  href: string
  description: string
}

// Navigation group structure
export interface NavigationGroup {
  title: string
  items: NavigationItem[]
}

// Theme type
export type Theme = 'light' | 'dark'