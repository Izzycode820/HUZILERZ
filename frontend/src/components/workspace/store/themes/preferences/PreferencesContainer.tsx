'use client';

import { useQuery } from '@apollo/client/react';
import { useParams } from 'next/navigation';
import { StorefrontSettingsDocument } from '@/services/graphql/hosting/queries/storefront/__generated__/storefrontSettings.generated';
import { StoreAccessCard } from './StoreAccessCard';
import { SeoSettingsCard } from './SeoSettingsCard';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Alert } from '@/components/shadcn-ui/alert';

export function PreferencesContainer() {
  const params = useParams();
  const workspaceId = params?.workspace_id as string;

  const { data, loading, error } = useQuery(StorefrontSettingsDocument, {
    variables: { workspaceId },
    skip: !workspaceId,
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-96 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <div className="font-semibold">Error loading preferences</div>
        <div className="text-sm">{error.message}</div>
      </Alert>
    );
  }

  const settings = data?.storefrontSettings;

  if (!settings) {
    return (
      <Alert>
        <div className="text-sm">No storefront settings found</div>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <StoreAccessCard
        initialPassword={settings.password}
        assignedDomain={settings.assignedDomain}
        initialEnabled={settings.passwordEnabled}
        initialDescription={settings.passwordDescription}
      />
      <SeoSettingsCard
        initialSeoTitle={settings.seoTitle}
        initialSeoDescription={settings.seoDescription}
        initialSeoImageUrl={settings.seoImageUrl}
        assignedDomain={settings.assignedDomain}
      />
    </div>
  );
}
