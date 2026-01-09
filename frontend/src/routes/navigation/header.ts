/**
 * Header Navigation Configuration
 * Simple, scalable navigation for the header
 * No dropdowns - just direct navigation links using domain routes
 */

import { WORKSPACE_ROUTES } from '../domains/workspace'
import { BILLING_ROUTES } from '../domains/billing'
import { SHOWCASE_ROUTES } from '../domains/showcase'
import { PUBLIC_ROUTES } from '../core/constants'

export interface HeaderNavItem {
  label: string
  href: string
}

// Simple header navigation - direct links only using domain routes
export const HEADER_NAVIGATION: HeaderNavItem[] = [
  {
    label: 'Home',
    href: PUBLIC_ROUTES.HOME,
  },
  {
    label: 'Workspace',
    href: WORKSPACE_ROUTES.ROOT,
  },
  {
    label: 'Showcase',
    href: SHOWCASE_ROUTES.ROOT,
  },
  {
    label: 'Pricing',
    href: BILLING_ROUTES.ROOT,
  },
  {
    label: 'Documentation',
    href: '/docs',
  },
]

// Platform navigation for authenticated users
export const PLATFORM_NAVIGATION: HeaderNavItem[] = [
  {
    label: 'Dashboard',
    href: '/dashboard',
  },
  {
    label: 'Workspaces',
    href: WORKSPACE_ROUTES.ROOT,
  },
  {
    label: 'Billing',
    href: BILLING_ROUTES.ROOT,
  },
]