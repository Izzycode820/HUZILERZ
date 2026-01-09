'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@apollo/client/react';
import { ApolloProvider } from '@apollo/client/react';
import { themeClient } from '@/services/graphql/clients';
import { ThemeCustomizationDocument } from '@/services/graphql/themes/queries/mythemes/__generated__/themeCustomization.generated';
import { Preview } from '@/puck-visual-designer/puck';

function PreviewContent() {
  const params = useParams();
  const customizationId = params.customization_id as string;

  // Fetch customization data (draft version)
  const { data: customizationData, loading, error } = useQuery(ThemeCustomizationDocument, {
    variables: { id: customizationId },
    skip: !customizationId,
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-sm">Loading preview...</p>
        </div>
      </div>
    );
  }

  if (error || !customizationData?.themeCustomization) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md px-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Preview Unavailable</h3>
          <p className="text-gray-600 text-sm">{error?.message || 'Theme customization not found'}</p>
        </div>
      </div>
    );
  }

  const { themeSlug, puckData } = customizationData.themeCustomization;

  // Parse puckData from GraphQL
  const parsedPuckData = typeof puckData === 'string' ? JSON.parse(puckData) : puckData;

  return (
    <>
      {/* Preview Mode Banner */}
      <div className="sticky top-0 z-50 bg-blue-600 text-white px-6 py-3 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <span className="font-medium">Preview Mode</span>
          <span className="text-blue-200 text-sm">Draft changes (not published)</span>
        </div>
        <button
          onClick={() => window.close()}
          className="flex items-center gap-2 px-4 py-1.5 bg-white/10 hover:bg-white/20 rounded-md transition-colors"
        >
          <span className="text-sm">Close Preview</span>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Preview Content */}
      <Preview
        themeSlug={themeSlug}
        puckData={parsedPuckData}
      />
    </>
  );
}

export default function ThemePreviewPage() {
  return (
    <ApolloProvider client={themeClient}>
      <PreviewContent />
    </ApolloProvider>
  );
}
