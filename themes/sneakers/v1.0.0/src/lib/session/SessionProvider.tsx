'use client';

/**
 * Session Provider - Cameroon SaaS Dual Session Support
 *
 * Manages TWO session types:
 * 1. GuestSession - for cart (7 days, auto-created on first cart action)
 * 2. CustomerSession - for authentication (24 hours, created on login)
 *
 * Uses generated GraphQL mutations directly - no wrappers
 */

import { createContext, useContext, useEffect, useState, useCallback, useMemo, ReactNode } from 'react';
import { useMutation } from '@apollo/client/react';
import {
  CustomerLoginDocument,
  type CustomerLoginMutation,
  type CustomerLoginMutationVariables
} from '@/services/customer/__generated__/customer-login.generated';
import {
  ValidateCustomerSessionDocument,
  type ValidateCustomerSessionMutation,
  type ValidateCustomerSessionMutationVariables
} from '@/services/customer/__generated__/validate-customer-session.generated';
import {
  CustomerLogoutDocument,
  type CustomerLogoutMutation
} from '@/services/customer/__generated__/customer-logout.generated';
import {
  CreateCartDocument,
  type CreateCartMutation,
  type CreateCartMutationVariables
} from '@/services/cart/__generated__/create-cart.generated';
import { sessionStorage } from './storage';

interface SessionContextValue {
  // Guest Session (for cart - 7 days)
  guestSessionId: string | null;
  guestSessionExpiry: string | null;
  createGuestSession: () => Promise<string | null>;

  // Customer Session (for auth - 24 hours)
  customerSessionToken: string | null;
  customer: any | null;
  isAuthenticated: boolean;
  login: (phone: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;

  // Loading states
  isLoading: boolean;
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  // Guest Session State (cart)
  const [guestSessionId, setGuestSessionId] = useState<string | null>(null);
  const [guestSessionExpiry, setGuestSessionExpiry] = useState<string | null>(null);

  // Customer Session State (auth)
  const [customerSessionToken, setCustomerSessionToken] = useState<string | null>(null);
  const [customer, setCustomer] = useState<any | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  // Mutations
  const [createCartMutation] = useMutation<CreateCartMutation, CreateCartMutationVariables>(
    CreateCartDocument
  );

  const [loginMutation] = useMutation<CustomerLoginMutation, CustomerLoginMutationVariables>(
    CustomerLoginDocument
  );

  const [validateMutation] = useMutation<ValidateCustomerSessionMutation, ValidateCustomerSessionMutationVariables>(
    ValidateCustomerSessionDocument
  );

  const [logoutMutation] = useMutation<CustomerLogoutMutation>(
    CustomerLogoutDocument
  );

  // Create guest session for cart (7 days)
  const createGuestSession = useCallback(async (): Promise<string | null> => {
    try {
      const { data } = await createCartMutation();

      if (data?.createCart?.sessionId && data.createCart.expiresAt) {
        const sessionId = data.createCart.sessionId;
        const expiresAt = data.createCart.expiresAt;

        setGuestSessionId(sessionId);
        setGuestSessionExpiry(expiresAt);
        sessionStorage.setGuestSession(sessionId, expiresAt);

        return sessionId;
      }

      return null;
    } catch (error) {
      console.error('Failed to create guest session:', error);
      return null;
    }
  }, [createCartMutation]);

  // Customer login (24 hours)
  const login = useCallback(async (phone: string, password: string): Promise<boolean> => {
    try {
      const { data } = await loginMutation({
        variables: { phone, password }
      });

      if (data?.customerLogin?.success && data.customerLogin.sessionToken) {
        const token = data.customerLogin.sessionToken;
        setCustomerSessionToken(token);
        setCustomer(data.customerLogin.customer);
        sessionStorage.setCustomerSessionToken(token);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  }, [loginMutation]);

  // Customer logout
  const logout = useCallback(async (): Promise<void> => {
    try {
      const currentToken = sessionStorage.getCustomerSessionToken();
      if (currentToken) {
        await logoutMutation({
          variables: { sessionToken: currentToken }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setCustomerSessionToken(null);
      setCustomer(null);
      sessionStorage.clearCustomerSession();
    }
  }, [logoutMutation]);

  // Initialize sessions on mount
  useEffect(() => {
    const initSessions = async () => {
      // Load guest session from localStorage
      const savedGuestSessionId = sessionStorage.getGuestSessionId();
      if (savedGuestSessionId) {
        setGuestSessionId(savedGuestSessionId);
        // Expiry is already checked in getGuestSessionId
      }

      // Load and validate customer session
      const savedCustomerToken = sessionStorage.getCustomerSessionToken();
      if (savedCustomerToken) {
        try {
          const { data } = await validateMutation({
            variables: { sessionToken: savedCustomerToken }
          });

          if (data?.validateCustomerSession?.success && data.validateCustomerSession.customer) {
            setCustomerSessionToken(savedCustomerToken);
            setCustomer(data.validateCustomerSession.customer);
          } else {
            sessionStorage.clearCustomerSession();
          }
        } catch (error) {
          console.error('Customer session validation failed:', error);
          sessionStorage.clearCustomerSession();
        }
      }

      setIsLoading(false);
    };

    initSessions();
  }, [validateMutation]);

  // Memoize context value
  const value: SessionContextValue = useMemo(() => ({
    guestSessionId,
    guestSessionExpiry,
    createGuestSession,
    customerSessionToken,
    customer,
    isAuthenticated: !!customer,
    login,
    logout,
    isLoading,
  }), [guestSessionId, guestSessionExpiry, createGuestSession, customerSessionToken, customer, login, logout, isLoading]);

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within SessionProvider');
  }
  return context;
}
