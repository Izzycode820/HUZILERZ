'use client';

import { ApolloProvider } from '@apollo/client/react';
import { subscriptionClient } from '@/services/graphql/clients';
import { PlanPage } from '@/components/workspace/store/settings/billing/PlanPage';

export default function Plan() {
  return (
    <ApolloProvider client={subscriptionClient}>
      <PlanPage />
    </ApolloProvider>
  );
}
