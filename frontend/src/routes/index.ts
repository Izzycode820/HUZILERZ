/**
 * Routes - Barrel Exports
 * Clean and organized route exports
 */

// Core exports
export * from './core/types'
export * from './core/validators'

// Domain exports - explicit re-exports to avoid naming conflicts
export { AUTH_ROUTES } from './domains/auth'
export { BILLING_ROUTES } from './domains/billing'
export { SHOWCASE_ROUTES } from './domains/showcase'
export { STORE_ROUTES } from './domains/store'
export { WORKSPACE_ROUTES } from './domains/workspace'

// Core constants - explicit re-exports
export { PUBLIC_ROUTES, PROTECTED_ROUTES } from './core/constants'

// Navigation exports
export * from './navigation/header'

// Utility exports
export * from './utils/builders'
export * from './utils/metadata'
