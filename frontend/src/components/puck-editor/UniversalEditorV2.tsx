'use client';

import React, { useState, useEffect } from 'react';
import { Puck, type Data, type Config } from '@measured/puck';
import '@measured/puck/puck.css';
import { loadThemeConfig } from '@/registry/theme-registry';
import { puckOverrides } from './overrides/puck-overrides';
import { Button } from '@/components/shadcn-ui/button';
import { MediaLibraryProvider } from './MediaLibraryProvider';

/**
 * UniversalEditorV2 - Production Multi-Tenant Architecture with Shopify-style sidebar
 *
 * Loads master theme config (shared) + user's customized data (unique).
 * Uses Shopify-inspired left sidebar (Outline/Blocks/Fields) instead of default Puck UI.
 */
interface EditorProps {
  themeSlug: string;          // Which theme (e.g., 'ecommerce-sneakers')
  puckData: Data;             // User's customized data from DB
  className?: string;
  onSave?: (data: Data) => void;
  onPublish?: () => void;
  onChange?: (data: Data) => void;
  onPreview?: () => void;
  isSaving?: boolean;
  isPublishing?: boolean;
}

export default function UniversalEditorV2({
  themeSlug,
  puckData,
  className = '',
  onSave,
  onPublish,
  onChange,
  onPreview,
  isSaving = false,
  isPublishing = false
}: EditorProps) {
  const [config, setConfig] = useState<Config | null>(null);
  const [data, setData] = useState<Data>(puckData);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMasterConfig();
  }, [themeSlug]);

  const loadMasterConfig = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load master config from registry (shared by all users)
      const masterConfig = await loadThemeConfig(themeSlug);

      setConfig(masterConfig);
      setIsLoading(false);

    } catch (err: any) {
      setError(err.message || 'Failed to load theme');
      setIsLoading(false);
    }
  };

  const handleSave = (newData: Data) => {
    setData(newData);
    onSave?.(newData);
  };

  const handlePublish = async (newData: Data) => {
    // Save the data first
    setData(newData);
    await onSave?.(newData);

    // Then call publish to change status
    onPublish?.();
  };

  const handleChange = (newData: Data) => {
    setData(newData);
    onChange?.(newData);
  };

  if (isLoading) {
    return (
      <div className={`h-screen flex items-center justify-center bg-gray-50 ${className}`}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Editor</h3>
          <p className="text-gray-500">Loading theme configuration...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`h-screen flex items-center justify-center bg-red-50 ${className}`}>
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Editor Error</h3>
          <p className="text-red-600 text-sm mb-6">{error}</p>
          <button
            onClick={loadMasterConfig}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className={`h-screen flex items-center justify-center bg-gray-50 ${className}`}>
        <p className="text-gray-600">Theme configuration not available</p>
      </div>
    );
  }

  return (
    <MediaLibraryProvider>
      <div className={`puck-editor force-light ${className}`} style={{ height: '100vh' }}>
        <Puck
          config={config}
          data={data}
          onPublish={handlePublish}
          onChange={handleChange}
          overrides={{
            ...puckOverrides,
            headerActions: ({ children }) => (
              <>
                {onPreview && (
                  <Button
                    variant="outline"
                    size="default"
                    onClick={onPreview}
                    title="Preview changes in a new window"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    Preview
                  </Button>
                )}
                {onSave && (
                  <Button
                    variant="outline"
                    size="default"
                    onClick={() => onSave(data)}
                    disabled={isSaving}
                  >
                    {isSaving ? (
                      <>
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        Save
                      </>
                    )}
                  </Button>
                )}
                {children}
              </>
            ),
          }}
          // Viewport Configuration
          viewports={[
            {
              width: 360,
              height: "auto",
              label: "Mobile",
              icon: (
                <svg width="16" height="16" viewBox="0 0 24 24">
                  <path d="M17 2H7c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM7 4h10v11H7V4zm0 13h10v3H7v-3z" />
                </svg>
              )
            },
            {
              width: 768,
              height: "auto",
              label: "Tablet",
              icon: (
                <svg width="16" height="16" viewBox="0 0 24 24">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM5 5h14v10H5V5zm0 12h14v2H5v-2z" />
                </svg>
              )
            },
            {
              width: 1280,
              height: "auto",
              label: "Desktop",
              icon: (
                <svg width="16" height="16" viewBox="0 0 24 24">
                  <path d="M21 3H3c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h7l-2 3v1h8v-1l-2-3h7c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM3 5h18v9H3V5z" />
                </svg>
              )
            }
          ]}
          // Enable iframe for proper viewport simulation
          iframe={{
            enabled: true,
            waitForStyles: true
          }}
          // UI Configuration - Both sidebars visible
          // Left: Outline/Blocks tabs | Right: Fields (custom enhanced fields)
          ui={{
            leftSideBarVisible: true,
            rightSideBarVisible: true
          }}
        />
      </div>
    </MediaLibraryProvider>
  );
}