'use client';

import { ApolloProvider } from '@apollo/client/react';
import { hostinClient } from '@/services/graphql/clients';
import { DomainsListContainer } from '@/components/workspace/store/settings/domain/list/DomainsListContainer';

export default function DomainsPage() {
  return (
    <ApolloProvider client={hostinClient}>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Domains</h1>
      </div>
      <DomainsListContainer />
    </ApolloProvider>
  );
}
