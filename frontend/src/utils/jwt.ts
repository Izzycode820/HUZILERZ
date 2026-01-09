import type { JWTPayload, SubscriptionData } from '../types/authentication/auth';

/**
 * Decode JWT payload without verification (client-side only)
 * For security: Never trust decoded data without server verification
 */
export function decodeJWTPayload(token: string): JWTPayload | null {
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload as JWTPayload;
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

/**
 * Extract subscription data from JWT token
 */
export function extractSubscriptionFromJWT(token: string): SubscriptionData | null {
  const payload = decodeJWTPayload(token);
  return payload?.subscription || null;
}

/**
 * Extract workspace context from JWT token
 */
export function extractWorkspaceFromJWT(token: string): {
  id: string;
  type: string;
  permissions: string[];
  role: string;
} | null {
  const payload = decodeJWTPayload(token);

  // v3.0: Workspace context is no longer in JWT.
  // Context is passed via X-Workspace-Id header and fetched via API.
  // This function is kept for backward compatibility but always returns null
  // to enforce reliance on server-validated context switching.
  return null;
}

/**
 * Check if JWT token is expired (with 30 second buffer)
 */
export function isTokenExpired(token: string): boolean {
  if (!token) return true;

  try {
    const payload = decodeJWTPayload(token);
    if (!payload?.exp) return true;

    const now = Math.floor(Date.now() / 1000);
    const bufferTime = 30; // 30 second buffer
    return (payload.exp - bufferTime) <= now;
  } catch {
    return true;
  }
}

/**
 * Get time until token expires (in seconds)
 */
export function getTokenExpiryTime(token: string): number {
  if (!token) return 0;

  try {
    const payload = decodeJWTPayload(token);
    if (!payload?.exp) return 0;

    const now = Math.floor(Date.now() / 1000);
    return Math.max(0, payload.exp - now);
  } catch {
    return 0;
  }
}