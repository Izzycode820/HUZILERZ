'use client';

/**
 * Category Selector List (Smart UI Component)
 *
 * Responsibilities:
 * - Fetches categories from merchant GraphQL (fresh data on every open)
 * - Shows list with loading skeletons
 * - Handles category selection
 * - Emits selected category slug
 *
 * Design:
 * - List view (not grid)
 * - Shows category name + small thumbnail
 * - Radio button selection
 * - Fresh data on every open (no stale data)
 *
 * IMPORTANT: This component must query the adminStoreClient endpoint
 * But the editor page uses themeClient provider.
 * Solution: Wrap in nested ApolloProvider with adminStoreClient.
 */

import React, { useEffect } from 'react';
import { ApolloProvider, useQuery } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';
import { CategoriesDocument } from '@/services/graphql/admin-store/queries/categories/__generated__/categories.generated';
import { ScrollArea } from '@/components/shadcn-ui/scroll-area';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { RadioGroup, RadioGroupItem } from '@/components/shadcn-ui/radio-group';
import { Label } from '@/components/shadcn-ui/label';
import { AlertCircle, Package } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';

interface CategorySelectorListProps {
  selectedSlug?: string;
  onSelect: (slug: string) => void;
  isOpen: boolean; // Controls when to fetch
}

// Internal component that uses the query (inside correct provider)
function CategorySelectorListInner({
  selectedSlug,
  onSelect,
  isOpen,
}: CategorySelectorListProps) {
  // Fetch categories with fresh data on every open
  // This query now correctly uses adminStoreClient from provider
  const { data, loading, error, refetch } = useQuery(CategoriesDocument, {
    variables: {
      first: 100, // Get all categories
      isVisible: undefined, // Include all (visible and hidden)
    },
    skip: !isOpen, // Only query when sheet is open
    fetchPolicy: 'network-only', // Always fetch fresh data, never use cache
    notifyOnNetworkStatusChange: true,
  });

  // Refetch when sheet opens to ensure fresh data
  useEffect(() => {
    if (isOpen) {
      refetch();
    }
  }, [isOpen, refetch]);

  // Transform GraphQL data
  const categories =
    data?.categories?.edges
      ?.map((edge) => ({
        id: edge?.node?.id || '',
        name: edge?.node?.name || '',
        slug: edge?.node?.slug || '',
        description: edge?.node?.description || '',
        isVisible: edge?.node?.isVisible || false,
        productCount: edge?.node?.productCount || 0,
        url: edge?.node?.featuredMedia?.url,
      }))
      .filter(Boolean) || [];

  // Loading state with skeletons
  if (loading) {
    return (
      <div className="space-y-3 p-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center space-x-3">
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-10 w-10 rounded" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-48" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load categories: {error.message}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Empty state
  if (categories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-3">
          <Package className="w-6 h-6 text-muted-foreground" />
        </div>
        <h3 className="text-sm font-medium mb-1">No categories yet</h3>
        <p className="text-xs text-muted-foreground text-center">
          Create categories in your store dashboard first
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[400px] px-4">
      <RadioGroup value={selectedSlug} onValueChange={onSelect}>
        <div className="space-y-2 py-2">
          {categories.map((category) => (
            <div
              key={category.id}
              className="flex items-center space-x-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors cursor-pointer"
              onClick={() => onSelect(category.slug)}
            >
              <RadioGroupItem value={category.slug} id={category.id} />

              {/* Category Thumbnail */}
              {category.url ? (
                <img
                      src={category.url || category.url || undefined}
                      alt={category.name}
                      className="h-16 w-16 rounded-md object-cover border"
                    />
              ) : (
                <div className="w-10 h-10 rounded bg-muted flex items-center justify-center flex-shrink-0">
                  <Package className="w-5 h-5 text-muted-foreground" />
                </div>
              )}

              {/* Category Info */}
              <Label
                htmlFor={category.id}
                className="flex-1 cursor-pointer space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{category.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {category.productCount} products
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {category.slug}
                  </span>
                  {!category.isVisible && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">
                      Hidden
                    </span>
                  )}
                </div>
              </Label>
            </div>
          ))}
        </div>
      </RadioGroup>
    </ScrollArea>
  );
}

// Exported component that wraps with correct Apollo provider
export function CategorySelectorList(props: CategorySelectorListProps) {
  return (
    <ApolloProvider client={adminStoreClient}>
      <CategorySelectorListInner {...props} />
    </ApolloProvider>
  );
}
