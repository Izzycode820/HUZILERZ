'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Render } from '@measured/puck';
import { useThemeManifest } from '@/hooks/theme';

export default function MarketplacePreviewPage() {
  const params = useParams();
  const marketplaceTemplateId = params.template_id as string;

  const {
    currentTheme,
    isLoading,
    error,
    loadThemeWithFallback,
    clearError
  } = useThemeManifest();

  const [mergedConfig, setMergedConfig] = useState<any>(null);

  useEffect(() => {
    if (marketplaceTemplateId) {
      loadTemplate();
    }
  }, [marketplaceTemplateId]);

  const loadTemplate = async () => {
    try {
      clearError();

      if (!marketplaceTemplateId) return;

      const result = await loadThemeWithFallback(marketplaceTemplateId);

      if (result.config && result.module) {
        const themeComponents = result.module.default?.components || result.module.components;

        if (!themeComponents) {
          throw new Error('Theme components not found');
        }

        const merged = {
          ...result.config,
          components: themeComponents
        };

        setMergedConfig(merged);
      }

    } catch (error) {
      console.error('Template preview loading failed:', error);
    }
  };

  // Show loading spinner
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-sm">Loading template...</p>
        </div>
      </div>
    );
  }

  // Show error if template couldn't be loaded
  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Template Loading Failed</h3>
          <p className="text-red-600 text-sm mb-6">{error}</p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!currentTheme || !mergedConfig) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Template Not Found</h3>
          <p className="text-gray-600 text-sm mb-6">The template you're looking for is not available.</p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 text-sm text-blue-800">
        <span className="font-medium">Previewing:</span> {currentTheme.template_name}
      </div>

      <Render
        config={mergedConfig}
        data={currentTheme.puck_data}
      />
    </div>
  );
}