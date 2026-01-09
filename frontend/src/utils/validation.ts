/**
 * Authentication Type Validation Utilities
 * Ensures frontend types match backend expectations
 */

import type {
  JWTPayload,
  UserData,
  SubscriptionData
} from '../types/authentication/auth';
import type { SECURITY_RISK_LEVELS } from '../types/authentication/security';

/**
 * Validate JWT payload structure matches backend expectations
 */
export function validateJWTPayload(payload: unknown): payload is JWTPayload {
  return (
    typeof payload === 'object' && payload !== null &&
    'user_id' in payload && 'email' in payload && 'username' in payload &&
    'exp' in payload && 'iat' in payload && 'jti' in payload && 'type' in payload &&
    typeof payload.user_id === 'number' && // Backend User.id is IntegerField
    typeof payload.email === 'string' &&
    typeof payload.username === 'string' &&
    typeof payload.exp === 'number' &&
    typeof payload.iat === 'number' &&
    typeof payload.jti === 'string' &&
    (payload.type === 'access' || payload.type === 'refresh')
  );
}

/**
 * Validate subscription data structure from JWT
 */
export function validateSubscriptionData(data: unknown): data is SubscriptionData {
  return (
    typeof data === 'object' && data !== null &&
    'tier' in data && 'status' in data && 'features_bitmap' in data &&
    'usage_hash' in data && 'limits' in data &&
    typeof data.tier === 'string' &&
    ['free', 'beginning', 'pro', 'enterprise'].includes(data.tier) &&
    typeof data.status === 'string' &&
    ['active', 'grace_period', 'inactive', 'expired'].includes(data.status) &&
    typeof data.features_bitmap === 'number' &&
    typeof data.usage_hash === 'string' &&
    typeof data.limits === 'object' && data.limits !== null &&
    'max_workspaces' in data.limits && 'deployment_allowed' in data.limits &&
    typeof data.limits.max_workspaces === 'number' &&
    typeof data.limits.deployment_allowed === 'boolean'
  );
}

/**
 * Validate user data structure matches backend User model
 */
export function validateUserData(data: unknown): data is UserData {
  return (
    typeof data === 'object' && data !== null &&
    'id' in data && 'email' in data && 'username' in data &&
    'first_name' in data && 'last_name' in data &&
    'email_verified' in data && 'two_factor_enabled' in data && 'subscription' in data &&
    typeof data.id === 'number' && // Backend User.id is IntegerField
    typeof data.email === 'string' &&
    typeof data.username === 'string' &&
    typeof data.first_name === 'string' &&
    typeof data.last_name === 'string' &&
    typeof data.email_verified === 'boolean' &&
    typeof data.two_factor_enabled === 'boolean' &&
    validateSubscriptionData(data.subscription)
  );
}

/**
 * Validate risk level matches backend numeric system
 */
export function validateRiskLevel(level: unknown): level is keyof typeof SECURITY_RISK_LEVELS {
  return typeof level === 'number' && level >= 0 && level <= 4;
}

/**
 * Validate feature bitmap is a valid number
 */
export function validateFeatureBitmap(bitmap: unknown): bitmap is number {
  return typeof bitmap === 'number' && bitmap >= 0 && Number.isInteger(bitmap);
}

/**
 * Type guard for auth state discriminated union
 */
export function isAuthenticatedState(state: unknown): state is { status: 'authenticated'; user: UserData } {
  return typeof state === 'object' && state !== null && 'status' in state && 'user' in state && state.status === 'authenticated' && validateUserData(state.user);
}

export function isLoadingState(state: unknown): state is { status: 'loading' } {
  return typeof state === 'object' && state !== null && 'status' in state && state.status === 'loading';
}

export function isErrorState(state: unknown): state is { status: 'error'; error: unknown } {
  return typeof state === 'object' && state !== null && 'status' in state && 'error' in state && state.status === 'error' && state.error !== null;
}

export function isIdleState(state: unknown): state is { status: 'idle' } {
  return typeof state === 'object' && state !== null && 'status' in state && state.status === 'idle';
}

/**
 * Comprehensive validation for API responses
 */
export function validateAPIResponse(response: unknown): boolean {
  return (
    typeof response === 'object' && response !== null &&
    'success' in response &&
    typeof response.success === 'boolean' &&
    // Error responses should have consistent structure
    (!response.success ? ('error' in response && typeof response.error === 'string') : true)
  );
}

/**
 * Validate workspace permissions array
 */
export function validateWorkspacePermissions(permissions: unknown): permissions is string[] {
  return Array.isArray(permissions) && permissions.every(p => typeof p === 'string');
}