'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import { PaymentMethodsListPage } from '@/components/workspace/store/settings/payments';

export default function PaymentsPage() {
    return (
        <ApolloProvider client={adminStoreClient}>
            <PaymentMethodsListPage />
        </ApolloProvider>
    );
}
