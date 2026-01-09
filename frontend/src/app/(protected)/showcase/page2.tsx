'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { useTheme } from '@/hooks/theme/useTheme';
import ThemeCard from '@/components/theme/list/ThemeCard';
import { WorkspaceSelectionModal } from '@/components/theme/WorkspaceSelectionModal';
import { ThemeLoadingOverlay } from '@/components/theme/ThemeLoadingOverlay';
import { Search, Filter, Grid3X3, List } from 'lucide-react';

export default function ShowcasePage() {
  const {
    themes,
    searchResults,
    isLoading,
    isSearching,
    error,
    currentPage,
    pageSize,
    hasNextPage,
    hasPreviousPage,
    hasThemes,
    themeCount,
    searchResultCount,
    listThemes,
    searchThemesByQuery,
    getFreeThemes,
    getPaidThemes,
    getExclusiveThemes,
    getThemesByType,
    getThemesPaginated,
    clearError,
    clearSearchResults
  } = useTheme();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [activePriceTier, setActivePriceTier] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Modal and loading states
  const [showWorkspaceModal, setShowWorkspaceModal] = useState(false);
  const [showLoadingOverlay, setShowLoadingOverlay] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<{ id: string; name: string } | null>(null);

  // Load initial themes (stable reference prevents infinite loop)
  useEffect(() => {
    listThemes();
  }, [listThemes]);

  // Compute filtered arrays with useMemo (prevents infinite loops)
  // Following the rule: Never subscribe to computed arrays, compute in component
  // SSR-safe: Add defensive checks for undefined arrays
  // Backend uses template_type (not theme_type)
  const freeThemes = useMemo(() => themes?.filter(t => t.price_tier === 'free') ?? [], [themes]);
  const paidThemes = useMemo(() => themes?.filter(t => t.price_tier === 'paid') ?? [], [themes]);
  const exclusiveThemes = useMemo(() => themes?.filter(t => t.price_tier === 'exclusive') ?? [], [themes]);
  const ecommerceThemes = useMemo(() => themes?.filter(t => t.template_type === 'ecommerce') ?? [], [themes]);
  const servicesThemes = useMemo(() => themes?.filter(t => t.template_type === 'services') ?? [], [themes]);
  const blogThemes = useMemo(() => themes?.filter(t => t.template_type === 'blog') ?? [], [themes]);
  const restaurantThemes = useMemo(() => themes?.filter(t => t.template_type === 'restaurant') ?? [], [themes]);

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      searchThemesByQuery(query.trim());
    } else {
      clearSearchResults();
      listThemes();
    }
  };

  // Handle category filter
  const handleCategoryFilter = (category: string) => {
    setActiveCategory(category);
    if (category === 'all') {
      listThemes();
    } else {
      getThemesByType(category as 'ecommerce' | 'services' | 'blog' | 'restaurant');
    }
  };

  // Handle price tier filter
  const handlePriceTierFilter = (priceTier: string) => {
    setActivePriceTier(priceTier);
    switch (priceTier) {
      case 'free':
        getFreeThemes();
        break;
      case 'paid':
        getPaidThemes();
        break;
      case 'exclusive':
        getExclusiveThemes();
        break;
      default:
        listThemes();
        break;
    }
  };

  // Handle theme preview
  const handlePreview = (themeId: string) => {
    // TODO: Implement theme preview modal
    console.log('Preview theme:', themeId);
  };

  // Handle theme use
  const handleUse = (themeId: string) => {
    const theme = displayThemes.find((t) => t.id === themeId);
    if (theme) {
      setSelectedTheme({ id: theme.id, name: theme.name });
      setShowWorkspaceModal(true);
    }
  };

  // Get display themes (search results or regular themes) - SSR-safe
  const displayThemes = searchQuery.trim() ? (searchResults ?? []) : (themes ?? []);
  const displayCount = searchQuery.trim() ? searchResultCount : themeCount;

  const categories = [
    { id: 'all', name: 'All Categories' },
    { id: 'ecommerce', name: 'E-commerce' },
    { id: 'services', name: 'Services' },
    { id: 'blog', name: 'Blog' },
    { id: 'restaurant', name: 'Restaurant' }
  ];

  const priceTiers = [
    { id: 'all', name: 'All Prices' },
    { id: 'free', name: 'Free' },
    { id: 'paid', name: 'Paid' },
    { id: 'exclusive', name: 'Exclusive' }
  ];

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Theme Store
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Discover and customize beautiful templates for your website
          </p>
        </div>

        {/* Search and Filters */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  type="text"
                  placeholder="Search themes..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* View Mode Toggle */}
              <div className="flex items-center gap-2">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Category and Price Filters */}
            <div className="flex flex-wrap gap-2 mt-4">
              {/* Category Filters */}
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Categories:</span>
                {categories.map((category) => (
                  <Button
                    key={category.id}
                    variant={activeCategory === category.id ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleCategoryFilter(category.id)}
                  >
                    {category.name}
                  </Button>
                ))}
              </div>

              {/* Price Tier Filters */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-muted-foreground">Price:</span>
                {priceTiers.map((tier) => (
                  <Button
                    key={tier.id}
                    variant={activePriceTier === tier.id ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handlePriceTierFilter(tier.id)}
                  >
                    {tier.name}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="mb-6 border-destructive">
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <p className="text-destructive">{error}</p>
                <Button variant="outline" size="sm" onClick={clearError}>
                  Dismiss
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Loading State */}
        {(isLoading || isSearching) && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading themes...</p>
          </div>
        )}

        {/* Results Count */}
        {!isLoading && !isSearching && (
          <div className="mb-6">
            <p className="text-muted-foreground">
              Showing {displayCount} {searchQuery.trim() ? 'search results' : 'themes'}
              {searchQuery.trim() && (
                <span> for &quot;{searchQuery}&quot;</span>
              )}
            </p>
          </div>
        )}

        {/* Themes Grid */}
        {!isLoading && !isSearching && hasThemes && (
          <div className={viewMode === 'grid'
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            : "space-y-4"
          }>
            {displayThemes.map((theme) => (
              <ThemeCard
                key={theme.id}
                name={theme.name}
                description={theme.description}
                template_type={theme.template_type}
                price_tier={theme.price_tier}
                price_amount={theme.price_amount}
                rating={theme.rating}
                preview_image={theme.preview_image}
                onPreview={() => handlePreview(theme.id)}
                onUse={() => handleUse(theme.id)}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !isSearching && !hasThemes && (
          <Card className="text-center py-12">
            <CardContent>
              <h3 className="text-lg font-semibold mb-2">No Themes Found</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery.trim()
                  ? 'No themes match your search criteria. Try adjusting your filters.'
                  : 'No themes available yet. Check back soon!'
                }
              </p>
              {searchQuery.trim() && (
                <Button onClick={() => {
                  setSearchQuery('');
                  clearSearchResults();
                  listThemes();
                }}>
                  Clear Search
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Pagination (TODO: Implement) */}
        {hasNextPage || hasPreviousPage && (
          <div className="flex justify-center mt-8">
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={!hasPreviousPage}
                onClick={() => getThemesPaginated(currentPage - 1, pageSize)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={!hasNextPage}
                onClick={() => getThemesPaginated(currentPage + 1, pageSize)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Workspace Selection Modal */}
      {selectedTheme && (
        <WorkspaceSelectionModal
          open={showWorkspaceModal}
          onOpenChange={setShowWorkspaceModal}
          themeId={selectedTheme.id}
          themeName={selectedTheme.name}
          onNavigate={() => setShowLoadingOverlay(true)}
        />
      )}

      {/* Loading Overlay */}
      <ThemeLoadingOverlay
        show={showLoadingOverlay}
        onComplete={() => setShowLoadingOverlay(false)}
      />
    </div>
  );
}