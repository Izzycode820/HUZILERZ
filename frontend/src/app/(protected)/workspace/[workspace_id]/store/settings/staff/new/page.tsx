'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import AddStaffForm from '@/components/workspace/store/settings/staff/add/AddStaffForm';

export default function AddStaffPage() {
  return (
    <ApolloProvider client={adminStoreClient}>
      <AddStaffForm />
    </ApolloProvider>
  );
}
