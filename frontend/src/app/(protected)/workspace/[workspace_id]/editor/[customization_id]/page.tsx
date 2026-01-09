'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client/react';
import { ApolloProvider } from '@apollo/client/react';
import { themeClient } from '@/services/graphql/clients';
import { ThemeCustomizationDocument } from '@/services/graphql/themes/queries/mythemes/__generated__/themeCustomization.generated';
import { UpdateThemeCustomizationDocument } from '@/services/graphql/themes/mutations/mythemes/__generated__/updateThemeCustomization.generated';
import { PublishThemeDocument } from '@/services/graphql/themes/mutations/mythemes/__generated__/publishTheme.generated';
import UniversalEditorV2 from '@/components/puck-editor/UniversalEditorV2';
import { type Data } from '@measured/puck';
import { toast } from 'sonner';
import { WorkspaceContextLoader } from '@/components/workspace/unique/WorkspaceContextLoader';

function EditorContent() {
  const params = useParams();
  const customizationId = params.customization_id as string;

  const [updateCustomization, { loading: isSaving }] = useMutation(UpdateThemeCustomizationDocument);
  const [publishTheme, { loading: isPublishing }] = useMutation(PublishThemeDocument);

  // Fetch customization data
  const { data: customizationData, loading, error } = useQuery(ThemeCustomizationDocument, {
    variables: { id: customizationId },
    skip: !customizationId,
  });

  const handlePublish = async (newData: Data) => {
    try {
      console.log('📝 Saving theme customization...');

      const { data: result } = await updateCustomization({
        variables: {
          id: customizationId,
          input: {
            puckData: JSON.stringify(newData),
          },
        },
      });

      if (result?.updateThemeCustomization?.success) {
        toast.success('Theme saved successfully!');
        console.log('✅ Save successful');
      } else {
        toast.error(result?.updateThemeCustomization?.error || 'Failed to save theme');
      }
    } catch (error: any) {
      console.error('❌ Save failed:', error);
      toast.error('Failed to save theme');
    }
  };

  const handlePreview = () => {
    const workspaceId = params.workspace_id as string;
    const previewUrl = `/workspace/${workspaceId}/preview/${customizationId}`;
    window.open(previewUrl, '_blank', 'width=1280,height=800');
  };

  const handlePublishTheme = async () => {
    try {
      console.log('🚀 Publishing theme...');

      const { data: result } = await publishTheme({
        variables: { id: customizationId },
      });

      if (result?.publishTheme?.success) {
        toast.success(result.publishTheme.message || 'Theme published successfully!');
        console.log('✅ Publish successful');
      } else {
        toast.error(result?.publishTheme?.error || 'Failed to publish theme');
      }
    } catch (error: any) {
      console.error('❌ Publish failed:', error);
      toast.error('Failed to publish theme');
    }
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Editor</h3>
          <p className="text-gray-500">Fetching theme data...</p>
        </div>
      </div>
    );
  }

  if (error || !customizationData?.themeCustomization) {
    return (
      <div className="h-screen flex items-center justify-center bg-red-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to Load</h3>
          <p className="text-red-600 text-sm">{error?.message || 'Theme customization not found'}</p>
        </div>
      </div>
    );
  }

  const { themeSlug, puckData } = customizationData.themeCustomization;

  // Parse puckData from GraphQL
  const parsedPuckData = typeof puckData === 'string' ? JSON.parse(puckData) : puckData;

  // Handle missing themeSlug
  if (!themeSlug) {
    return (
      <div className="h-screen flex items-center justify-center bg-red-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Invalid Theme</h3>
          <p className="text-red-600 text-sm">Theme customization is missing theme slug</p>
        </div>
      </div>
    );
  }

  return (
    <UniversalEditorV2
      themeSlug={themeSlug}
      puckData={parsedPuckData}
      onSave={handlePublish}
      onPublish={handlePublishTheme}
      onPreview={handlePreview}
      isSaving={isSaving}
      isPublishing={isPublishing}
    />
  );
}

export default function ThemeEditorPage() {
  return (
    <WorkspaceContextLoader>
      <ApolloProvider client={themeClient}>
        <EditorContent />
      </ApolloProvider>
    </WorkspaceContextLoader>
  );
}