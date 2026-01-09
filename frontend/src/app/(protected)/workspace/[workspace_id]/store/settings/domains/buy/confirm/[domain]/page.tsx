'use client';

import { useParams } from 'next/navigation';
import { ApolloProvider } from '@apollo/client/react';
import { hostinClient } from '@/services/graphql/clients';
import { PurchaseConfirmation } from '@/components/workspace/store/settings/domain/buy/PurchaseConfirmation';

export default function PurchaseConfirmationPage() {
  const params = useParams();
  const domain = decodeURIComponent(params.domain as string);

  return (
    <ApolloProvider client={hostinClient}>
      <div className="@container/main flex flex-1 flex-col gap-2">
        <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
          <div className="px-4 lg:px-6">
            <PurchaseConfirmation domain={domain} />
          </div>
        </div>
      </div>
    </ApolloProvider>
  );
}
