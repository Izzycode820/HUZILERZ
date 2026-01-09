'use client';

import { ApolloProvider } from '@apollo/client/react';
import { subscriptionClient } from '@/services/graphql/clients';
import { AuthGuard } from '@/components/authentication/guards/AuthGuard';
import { CheckoutFlow } from '@/components/subscription/checkout/CheckoutFlow';

/**
 * Platform Checkout Page - V1 (Following Industry Guide)
 *
 * Pattern: Wrapper page with Apollo provider
 * Matches: billing/page.tsx structure
 *
 * Flow:
 * 1. User clicks plan on /billing → Auth gate redirects here with INTENT params
 * 2. CheckoutFlow component handles the heavy lifting (GraphQL mutation, payment)
 * 3. Protected by AuthGuard + Middleware + Auth redirect system
 *
 * See: c:\S.T.E.V.E\V2\HUZILERZ\ZCHAT\p.md (industry guide)
 */
export default function CheckoutPage() {
  return (
    <AuthGuard>
      <ApolloProvider client={subscriptionClient}>
        <CheckoutFlow />
      </ApolloProvider>
    </AuthGuard>
  );
}
