'use client';

import { ApolloProvider } from '@apollo/client/react';
import { hostinClient } from '@/services/graphql/clients';
import { PreferencesContainer } from '@/components/workspace/store/themes/preferences/PreferencesContainer';

export default function PreferencesPage() {
  return (
    <ApolloProvider client={hostinClient}>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Preferences</h1>
      </div>
      <PreferencesContainer />
    </ApolloProvider>
  );
}
