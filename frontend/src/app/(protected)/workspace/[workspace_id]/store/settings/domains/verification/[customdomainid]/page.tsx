'use client';

import { ApolloProvider } from '@apollo/client/react';
import { hostinClient } from '@/services/graphql/clients';
import { DNSVerificationContainer } from '@/components/workspace/store/settings/domain/verification/DNSVerificationContainer';

export default function DomainVerificationPage() {
  return (
    <ApolloProvider client={hostinClient}>
      <div className="@container/main flex flex-1 flex-col gap-2">
        <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
          <div className="px-4 lg:px-6">
            <DNSVerificationContainer />
          </div>
        </div>
      </div>
    </ApolloProvider>
  );
}
