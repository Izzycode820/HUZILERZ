/**
 * Authentication Domain Routes
 * All authentication-related routes
 */

// Authentication routes
export const AUTH_ROUTES = {
  ROOT: '/auth',
  LOGIN: '/auth/login',
  SIGNUP: '/auth/signup',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',
  MFA_SETUP: '/auth/mfa-setup',
  OAUTH2_CALLBACK: '/auth/oauth2/callback',
} as const