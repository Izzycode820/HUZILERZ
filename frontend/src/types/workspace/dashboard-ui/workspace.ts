/**
 * Universal Workspace Type Definitions
 * These types define the structure for all workspace configurations
 * across different workspace types (store, services, blog, restaurant, etc.)
 */

import type { Icon } from "@tabler/icons-react"

/**
 * Main navigation item (primary sidebar navigation)
 */
export interface NavMainItem {
  title: string
  url: string
  icon?: Icon
  items?: NavMainSubItem[]
  defaultOpen?: boolean // For collapsible items
  navigateToFirstChild?: boolean // If true, clicking parent navigates to first child (for label-only parents)
}

/**
 * Sub-navigation item (nested under main nav items)
 */
export interface NavMainSubItem {
  title: string
  url: string
}

/**
 * Secondary navigation item (bottom of sidebar)
 */
export interface NavSecondaryItem {
  title: string
  url: string
  icon: Icon
}

/**
 * Section navigation item (e.g., Sales channels, Apps)
 */
export interface NavSectionItem {
  name: string
  url: string
  icon: Icon
  items?: NavMainSubItem[] // Support for nested sub-items
  defaultOpen?: boolean // For collapsible items
  navigateToFirstChild?: boolean // If true, clicking parent navigates to first child (for label-only parents)
}

/**
 * Section with label and items
 */
export interface NavSectionProps {
  label: string
  items: NavSectionItem[]
  defaultOpen?: boolean // For collapsible sections
}

/**
 * User configuration for sidebar footer
 */
export interface UserConfig {
  name: string
  email: string
  avatar?: string
}

/**
 * Workspace branding configuration
 */
export interface WorkspaceConfig {
  name: string
  icon: Icon
  url?: string
}

/**
 * Complete sidebar configuration for a workspace
 */
export interface WorkspaceSidebarConfig {
  user: UserConfig
  navMain: NavMainItem[]
  navSections?: NavSectionProps[]
  navSecondary: NavSecondaryItem[]
  workspaceConfig: WorkspaceConfig
  footerActions: React.ReactNode  // Required: Security actions like Leave Workspace button
}

/**
 * Header configuration
 */
export interface WorkspaceHeaderConfig {
  title: string
  showGitHubLink?: boolean
  customActions?: React.ReactNode
}

/**
 * Workspace type enum
 */
export type WorkspaceType = "store" | "services" | "blog" | "restaurant"
