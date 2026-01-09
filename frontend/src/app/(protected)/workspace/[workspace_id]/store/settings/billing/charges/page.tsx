'use client';

import { ApolloProvider } from '@apollo/client/react';
import { subscriptionClient } from '@/services/graphql/clients';
import { ChargesPage } from '@/components/workspace/store/settings/billing/ChargesPage';

export default function Charges() {
  return (
    <ApolloProvider client={subscriptionClient}>
      <ChargesPage />
    </ApolloProvider>
  );
}
