'use client';

import { ApolloProvider } from '@apollo/client/react';
import { subscriptionClient } from '@/services/graphql/clients';
import { BillingPage } from '@/components/workspace/store/settings/billing/BillingPage';

export default function Billing() {
  return (
    <ApolloProvider client={subscriptionClient}>
      <BillingPage />
    </ApolloProvider>
  );
}
