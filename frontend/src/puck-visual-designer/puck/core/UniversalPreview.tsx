'use client';

import React, { useState, useEffect } from 'react';
import { Render, type Data, type Config } from '@measured/puck';
import '@measured/puck/puck.css';
import { loadThemeConfig } from '@/registry/theme-registry';

/**
 * UniversalPreview - Customer-Facing Storefront Renderer
 *
 * Renders user's customized store to end customers.
 *
 * Flow:
 * 1. Load master puck.config.tsx from registry (shared)
 * 2. Load user's puck_data from props (from DB)
 * 3. Render with <Render> component (no editor UI)
 */
interface PreviewProps {
  themeSlug: string;          // Which theme
  puckData: Data;             // User's customized data
  className?: string;
}

export default function UniversalPreview({
  themeSlug,
  puckData,
  className = ''
}: PreviewProps) {
  const [config, setConfig] = useState<Config | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMasterConfig();
  }, [themeSlug]);

  const loadMasterConfig = async () => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('🔵 [UniversalPreview] Loading master config for:', themeSlug);

      // Load master config from registry (shared by all users)
      const masterConfig = await loadThemeConfig(themeSlug);

      console.log('✅ [UniversalPreview] Master config loaded');
      setConfig(masterConfig);
      setIsLoading(false);

    } catch (err: any) {
      console.error('❌ [UniversalPreview] Failed to load config:', err);
      setError(err.message || 'Failed to load theme');
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-gray-50 ${className}`}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-sm">Loading store...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-gray-50 ${className}`}>
        <div className="text-center max-w-md px-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Store Unavailable</h3>
          <p className="text-gray-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-gray-50 ${className}`}>
        <p className="text-gray-600">Store configuration not available</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <Render config={config} data={puckData} />
    </div>
  );
}
