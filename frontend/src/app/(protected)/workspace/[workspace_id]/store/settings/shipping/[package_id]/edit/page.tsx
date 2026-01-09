'use client';

import { use } from 'react';
import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import { PackageFormPage } from '@/components/workspace/store/settings/shipping';

interface EditPackagePageProps {
    params: Promise<{ package_id: string }>;
}

export default function EditPackagePage({ params }: EditPackagePageProps) {
    const resolvedParams = use(params);

    return (
        <ApolloProvider client={adminStoreClient}>
            <PackageFormPage mode="edit" packageId={resolvedParams.package_id} />
        </ApolloProvider>
    );
}
