/**
 * Session Storage Utilities
 * Handles TWO session types:
 * 1. GuestSession - for cart (7 days, DB-backed)
 * 2. CustomerSession - for auth (24 hours, cache-backed)
 */

// GuestSession for cart persistence (7 days)
const GUEST_SESSION_KEY = 'sneakers_guest_session_id';
const GUEST_SESSION_EXPIRY_KEY = 'sneakers_guest_session_expiry';

// Customer auth session (24 hours)
const CUSTOMER_SESSION_KEY = 'sneakers_customer_session_token';

export const sessionStorage = {
  // Guest Session (for cart)
  getGuestSessionId: (): string | null => {
    if (typeof window === 'undefined') return null;
    const sessionId = localStorage.getItem(GUEST_SESSION_KEY);
    const expiry = localStorage.getItem(GUEST_SESSION_EXPIRY_KEY);

    // Check if expired
    if (sessionId && expiry) {
      if (new Date(expiry) > new Date()) {
        return sessionId;
      } else {
        // Expired, clear it
        sessionStorage.clearGuestSession();
        return null;
      }
    }
    return null;
  },

  setGuestSession: (sessionId: string, expiresAt: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(GUEST_SESSION_KEY, sessionId);
    localStorage.setItem(GUEST_SESSION_EXPIRY_KEY, expiresAt);
  },

  clearGuestSession: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(GUEST_SESSION_KEY);
    localStorage.removeItem(GUEST_SESSION_EXPIRY_KEY);
  },

  // Customer Session (for authentication)
  getCustomerSessionToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(CUSTOMER_SESSION_KEY);
  },

  setCustomerSessionToken: (token: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(CUSTOMER_SESSION_KEY, token);
  },

  clearCustomerSession: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(CUSTOMER_SESSION_KEY);
  },

  // Clear all sessions
  clearAll: (): void => {
    sessionStorage.clearGuestSession();
    sessionStorage.clearCustomerSession();
  },
};
