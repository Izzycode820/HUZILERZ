'use client';

import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import { GeneralSettingsPage } from '@/components/workspace/store/settings/general/GeneralSettingsPage';

export default function General() {
    return (
        <ApolloProvider client={adminStoreClient}>
            <GeneralSettingsPage />
        </ApolloProvider>
    );
}
