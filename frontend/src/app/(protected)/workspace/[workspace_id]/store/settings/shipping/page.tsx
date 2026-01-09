'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import { ShippingPackagesListPage } from '@/components/workspace/store/settings/shipping';

export default function ShippingPage() {
    return (
        <ApolloProvider client={adminStoreClient}>
            <ShippingPackagesListPage />
        </ApolloProvider>
    );
}
