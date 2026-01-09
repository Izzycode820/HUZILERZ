'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import { PackageFormPage } from '@/components/workspace/store/settings/shipping';

export default function AddPackagePage() {
    return (
        <ApolloProvider client={adminStoreClient}>
            <PackageFormPage mode="create" />
        </ApolloProvider>
    );
}
