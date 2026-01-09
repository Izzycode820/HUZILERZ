'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import MemberDetailsContainer from '@/components/workspace/store/settings/staff/details/MemberDetailsContainer';
import { use } from 'react';

export default function MemberDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <ApolloProvider client={adminStoreClient}>
      <MemberDetailsContainer memberId={id} />
    </ApolloProvider>
  );
}
