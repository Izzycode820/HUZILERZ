'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import StaffListContainer from '@/components/workspace/store/settings/staff/list/StaffListContainer';

export default function StaffPage() {
  return (
    <ApolloProvider client={adminStoreClient}>
      <StaffListContainer />
    </ApolloProvider>
  );
}
