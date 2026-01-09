'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@apollo/client/react';
import { ThemeDetailsDocument } from '@/services/graphql/themes/queries/showcase/__generated__/themeDetails.generated';
import { ThemeDetailsHeader } from '@/components/theme/details/ThemeDetailsHeader';
import { ThemeHeroSection } from '@/components/theme/details/ThemeHeroSection';
import { ThemeDetailsSection } from '@/components/theme/details/ThemeDetailsSection';
import { ThemeFeaturesSection } from '@/components/theme/details/ThemeFeaturesSection';
import { ReviewsPlaceholder } from '@/components/theme/details/ReviewsPlaceholder';
import { RelatedThemesPlaceholder } from '@/components/theme/details/RelatedThemesPlaceholder';
import { WorkspaceSelectionModal } from '@/components/theme/details/WorkspaceSelectionModal';

export default function ThemeDetailsPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data, loading, error } = useQuery(ThemeDetailsDocument, {
    variables: { slug },
  });

  const handleUseTheme = () => {
    setIsModalOpen(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error loading theme</h2>
          <p className="text-gray-600">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!data?.themeDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Theme not found</h2>
          <p className="text-gray-600">The theme you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  const theme = data.themeDetails;

  return (
    <div className="min-h-screen bg-white">
      {/* Header with Navigation */}
      <ThemeDetailsHeader
        themeName={theme.name}
        demoUrl={theme.demoUrl}
        onUseTheme={handleUseTheme}
      />

      {/* Hero Section - Preview Image */}
      <ThemeHeroSection
        previewImage={theme.previewImage}
        themeName={theme.name}
      />

      {/* Details Section - Title, Price, Showcase */}
      <ThemeDetailsSection
        name={theme.name}
        description={theme.description}
        author={theme.author}
        priceTier={theme.priceTier}
        priceAmount={theme.priceAmount || 0}
        showcaseSections={(theme.showcaseSections || []).filter((s): s is NonNullable<typeof s> => s !== null)}
        demoUrl={theme.demoUrl}
        onUseTheme={handleUseTheme}
      />

      {/* Features Section */}
      <ThemeFeaturesSection features={(theme.features || []).filter((f): f is NonNullable<typeof f> => f !== null)} />

      {/* Reviews Placeholder */}
      <ReviewsPlaceholder />

      {/* Related Themes Placeholder */}
      <RelatedThemesPlaceholder />

      {/* Workspace Selection Modal */}
      <WorkspaceSelectionModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        themeSlug={theme.slug}
        themeName={theme.name}
      />
    </div>
  );
}
