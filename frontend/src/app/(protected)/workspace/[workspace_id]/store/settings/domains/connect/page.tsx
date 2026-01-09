'use client';

import { useRouter } from 'next/navigation';
import { ApolloProvider } from '@apollo/client/react';
import { hostinClient } from '@/services/graphql/clients';
import { ConnectDomainForm } from '@/components/workspace/store/settings/domain/connect/ConnectDomainForm';

export default function ConnectDomainPage() {
  const router = useRouter();

  return (
    <ApolloProvider client={hostinClient}>
      <ConnectDomainForm
        open={true}
        onOpenChange={(open) => {
          if (!open) {
            router.back();
          }
        }}
      />
    </ApolloProvider>
  );
}
