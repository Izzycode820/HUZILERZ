/**
 * Theme Entry Point for CDN Bundle
 *
 * This file is the entry point for the theme when deployed to CDN.
 * It initializes the React app and mounts it to the DOM.
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import { ApolloProvider } from '@apollo/client/react';
import { Render } from '@measured/puck';
import config from '../puck.config';
import defaultData from '../puck.data.json';
import { storefrontClient } from './lib/apollo-client';
import { GetPuckDataResolvedDocument } from './services/puck/__generated__/get-puck-data-resolved.generated';

// Import global styles
import './app/globals.css';

// Get store config injected by backend (see storefront_wrapper.html)
declare global {
  interface Window {
    __HUZILERZ_STORE_CONFIG__: {
      siteId: string;
      siteName: string;
      subdomain: string;
      customDomain: string | null;
      apiEndpoint: string;
      graphqlEndpoint: string;
      cdnUrl: string;
      version: string;
    };
  }
}

// Theme initialization function
async function initTheme() {
  console.log('🎨 Initializing Huzilerz Theme...');
  console.log('📦 Store Config:', window.__HUZILERZ_STORE_CONFIG__);

  // Get mount point
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    console.error('❌ Root element not found');
    return;
  }

  // Show loading state (mirrors page.tsx line 14-24)
  const root = createRoot(rootElement);
  root.render(
    <div className="min-h-screen bg-white">
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your store...</p>
        </div>
      </div>
    </div>
  );

  // Fetch puck data from backend
  try {
    const { data } = await storefrontClient.query({
      query: GetPuckDataResolvedDocument,
    });

    // Extract puck data (mirrors page.tsx line 43-50)
    let puckData = null;
    try {
      if (data?.publicPuckDataResolved?.data) {
        puckData = typeof data.publicPuckDataResolved.data === 'string'
          ? JSON.parse(data.publicPuckDataResolved.data)
          : data.publicPuckDataResolved.data;
      }
    } catch (parseError) {
      console.error('❌ Error parsing puck data:', parseError);
    }

    // Fallback to default data if needed (mirrors page.tsx line 53)
    const finalPuckData = puckData || defaultData;
    console.log('🎯 Final data passed to Render:', finalPuckData);

    // Render theme
    root.render(
      <React.StrictMode>
        <ApolloProvider client={storefrontClient}>
          <div className="min-h-screen bg-white">
            <Render config={config as any} data={finalPuckData} />
          </div>
        </ApolloProvider>
      </React.StrictMode>
    );

    console.log('✅ Theme initialized successfully');
  } catch (error) {
    console.error('❌ Error loading theme:', error);

    // Show error to user (mirrors page.tsx line 28-38)
    root.render(
      <div className="min-h-screen bg-white">
        <div className="flex items-center justify-center py-20">
          <div className="text-center max-w-md">
            <p className="text-red-600 mb-4">Error loading store configuration</p>
            <p className="text-gray-500 text-sm">{error instanceof Error ? error.message : 'Please try again later'}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTheme);
} else {
  initTheme();
}

// Export for module systems
export { config };
