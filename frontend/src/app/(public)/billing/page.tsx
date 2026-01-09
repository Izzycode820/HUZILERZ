'use client';

import { ApolloProvider } from '@apollo/client/react';
import { subscriptionClient } from '@/services/graphql/clients';
import { PricingPage } from '@/components/subscription/pricing/PricingPage';

export default function BillingPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-16 px-6">
        <ApolloProvider client={subscriptionClient}>
          <PricingPage />
        </ApolloProvider>
      </div>
    </div>
  );
}
