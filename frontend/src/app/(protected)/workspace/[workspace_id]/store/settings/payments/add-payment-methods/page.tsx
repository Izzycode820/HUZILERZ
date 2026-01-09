'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import { AddPaymentMethodsPage } from '@/components/workspace/store/settings/payments';

export default function AddPaymentMethodsRoute() {
    return (
        <ApolloProvider client={adminStoreClient}>
            <AddPaymentMethodsPage />
        </ApolloProvider>
    );
}
