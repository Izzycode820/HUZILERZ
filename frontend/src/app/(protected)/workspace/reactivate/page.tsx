'use client';

import { ApolloProvider } from '@apollo/client/react';
import { subscriptionClient } from '@/services/graphql/clients';
import { ReactivatePage } from '@/components/workspace/reactivate/ReactivatePage';

export default function Reactivate() {
  return (
    <ApolloProvider client={subscriptionClient}>
      <ReactivatePage />
    </ApolloProvider>
  );
}
