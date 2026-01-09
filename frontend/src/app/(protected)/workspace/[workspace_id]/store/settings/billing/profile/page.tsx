'use client';

import { ApolloProvider } from '@apollo/client/react';
import { subscriptionClient } from '@/services/graphql/clients';
import { BillingProfilePage } from '@/components/workspace/store/settings/billing/BillingProfilePage';

export default function BillingProfile() {
  return (
    <ApolloProvider client={subscriptionClient}>
      <BillingProfilePage />
    </ApolloProvider>
  );
}
