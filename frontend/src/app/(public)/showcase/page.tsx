'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@apollo/client/react';
import { Input } from '@/components/shadcn-ui/input';
import { Search } from 'lucide-react';
import { ThemeCard } from '@/components/theme/list/ThemeCard';
import { ThemeFilters } from '@/components/theme/list/ThemeFilters';
import { ThemePagination } from '@/components/theme/list/ThemePagination';
import { ThemeEmptyState } from '@/components/theme/list/ThemeEmptyState';
import { ThemesDocument } from '@/services/graphql/themes/queries/showcase/__generated__/themes.generated';

const ITEMS_PER_PAGE = 24;

export default function ThemeStorePage() {
  const router = useRouter();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplateType, setSelectedTemplateType] = useState<string | undefined>();
  const [selectedPriceTier, setSelectedPriceTier] = useState<string | undefined>();
  const [currentPage, setCurrentPage] = useState(1);

  // Fetch themes with GraphQL
  const { data, loading, error, fetchMore } = useQuery(ThemesDocument, {
    variables: {
      first: ITEMS_PER_PAGE,
      name_Icontains: searchQuery || undefined,
      templateType: selectedTemplateType,
      priceTier: selectedPriceTier,
    },
  });

  // Transform data
  const themes = data?.themes?.edges?.map(edge => edge?.node).filter(Boolean) || [];
  const totalCount = data?.themes?.totalCount || 0;
  const hasNextPage = data?.themes?.pageInfo?.hasNextPage || false;
  const hasPreviousPage = currentPage > 1;
  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

  // Handlers
  const handleThemeClick = (slug: string) => {
    router.push(`/showcase/${slug}`);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);

    if (page > currentPage && hasNextPage && data?.themes?.pageInfo?.endCursor) {
      fetchMore({
        variables: {
          after: data.themes.pageInfo.endCursor,
        },
      });
    }
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedTemplateType(undefined);
    setSelectedPriceTier(undefined);
    setCurrentPage(1);
  };

  const hasActiveFilters = searchQuery || selectedTemplateType || selectedPriceTier;

  // Loading state
  if (loading && !data) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading themes...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-destructive py-12">
            <p className="text-lg font-semibold mb-2">Failed to load themes</p>
            <p className="text-sm text-muted-foreground">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Browse all themes</h1>
          <p className="text-muted-foreground">
            {totalCount} {totalCount === 1 ? 'theme' : 'themes'}
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              type="text"
              placeholder="Search themes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Main Content: Grid on left, Filters on right */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6">
          {/* Left: Theme Grid */}
          <div>
            {themes.length === 0 ? (
              <ThemeEmptyState
                hasFilters={!!hasActiveFilters}
                onClearFilters={handleClearFilters}
              />
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
                  {themes.map((theme) => (
                    <ThemeCard
                      key={theme!.id}
                      name={theme!.name}
                      slug={theme!.slug}
                      previewImage={theme!.previewImage}
                      templateType={theme!.templateType}
                      priceTier={theme!.priceTier}
                      priceAmount={theme!.priceAmount}
                      onClick={() => handleThemeClick(theme!.slug)}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <ThemePagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    hasNextPage={hasNextPage}
                    hasPreviousPage={hasPreviousPage}
                    onPageChange={handlePageChange}
                  />
                )}
              </>
            )}
          </div>

          {/* Right: Filters Sidebar */}
          <div>
            <ThemeFilters
              selectedTemplateType={selectedTemplateType}
              selectedPriceTier={selectedPriceTier}
              onTemplateTypeChange={setSelectedTemplateType}
              onPriceTierChange={setSelectedPriceTier}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
