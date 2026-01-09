"use client";

import { useQuery } from "@apollo/client/react";
import { Render } from "@measured/puck";
import config from "../../puck.config";
import defaultData from "../../puck.data.json";
import { GetPuckDataResolvedDocument } from "@/services/puck/__generated__/get-puck-data-resolved.generated";

export default function Home() {
  // Fetch puck data with resolved section data from backend
  const { data, loading, error } = useQuery(GetPuckDataResolvedDocument);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your store...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-white">
        <div className="flex items-center justify-center py-20">
          <div className="text-center max-w-md">
            <p className="text-red-600 mb-4">Error loading store configuration</p>
            <p className="text-gray-500 text-sm">{error.message || 'Please try again later'}</p>
          </div>
        </div>
      </div>
    );
  }

  // Extract puck data from GraphQL response (now with resolvedData injected)
  // Backend returns JSONString, so we need to parse it
  let puckData = null;
  try {
    if (data?.publicPuckDataResolved?.data) {
      puckData = JSON.parse(data.publicPuckDataResolved.data as string);
    }
  } catch (parseError) {
    console.error('❌ Error parsing puck data:', parseError);
  }

  // Fallback to default data if needed
  const finalPuckData = puckData || defaultData;
  console.log('🎯 Final data passed to Render:', finalPuckData);

  // Render the page with all sections from Puck data
  return (
    <div className="min-h-screen bg-white">
      {/*
        Puck.Render component:
        - Reads puckData.content array (list of sections)
        - Renders each section in order: NavBar → HeroSection → CollectionSection_A → SaleBannerSection → CollectionSection_B → CategoriesSection → Footer
        - Uses component definitions from puck.config.tsx
      */}
      <Render
        config={config as any}
        data={finalPuckData}
      />
    </div>
  );
}
