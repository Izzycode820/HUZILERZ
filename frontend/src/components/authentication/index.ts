/**
 * Authentication Components - Index
 * Core authentication components following 2024 best practices
 * Uses Zustand for state management, Shadcn/UI for components
 */

// Forms
export { LoginForm } from './forms/LoginForm'
export { SignupForm } from './forms/SignupForm'

// Guards
export { AuthGuard } from './guards/AuthGuard'
export { RoleGuard } from './guards/RoleGuard'

// Profile
export { UserProfile } from './profile/UserProfile'
export { AvatarUpload } from './profile/AvatarUpload'

// Verification
export { PhoneVerificationCard, EmailVerificationCard } from './verification'

// Shared
export { AuthLoadingSpinner, TokenManager } from './shared'
export { AuthErrorBoundary } from './shared/AuthErrorBoundary'

// Types
export type { AuthGuardProps } from './guards/AuthGuard'
export type { RoleGuardProps } from './guards/RoleGuard'
export type { UserProfileProps } from './profile/UserProfile'
export type { AvatarUploadProps } from './profile/AvatarUpload'