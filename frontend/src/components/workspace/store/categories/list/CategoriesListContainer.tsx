'use client';

/**
 * Categories List Container (Smart Component)
 *
 * Industry Standard Pattern:
 * - Container handles data fetching (GraphQL)
 * - Presentational components handle UI (card grid)
 * - Clean separation of concerns
 */

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CategoriesTable } from './CategoriesTable';
import { CategoriesToolbar } from './CategoriesToolbar';
import { CategoriesFilters } from './CategoriesFilters';
import { MobileCategoriesList } from './mobile';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from '@/components/shadcn-ui/pagination';
import { useQuery, useMutation } from '@apollo/client/react';
import { CategoriesDocument } from '@/services/graphql/admin-store/queries/categories/__generated__/categories.generated';
import { DeleteCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/deleteCategory.generated';
import { ToggleCategoryVisibilityDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/toggleCategoryVisibility.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';

export default function CategoriesListContainer() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);
  const isMobile = useIsMobile();

  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [search, setSearch] = useState('');
  const [visibilityFilter, setVisibilityFilter] = useState<string | undefined>();
  const [featuredFilter, setFeaturedFilter] = useState<string | undefined>();

  // Pagination state
  const pageSize = 20;
  const [currentPage, setCurrentPage] = useState(1);
  const [cursors, setCursors] = useState<{ [page: number]: string }>({});

  // Mutations
  const [deleteCategory] = useMutation(DeleteCategoryDocument);
  const [toggleCategoryVisibility] = useMutation(ToggleCategoryVisibilityDocument);

  // Debug: Log workspace context
  console.log('[CategoriesListContainer] Workspace context:', {
    hasWorkspace: !!currentWorkspace,
    workspaceId: currentWorkspace?.id || '(none)',
    workspaceName: currentWorkspace?.name || '(none)',
  });

  // Fetch categories with GraphQL (skip until workspace is loaded)
  const { data, loading, error, refetch } = useQuery(CategoriesDocument, {
    variables: {
      first: pageSize,
      after: cursors[currentPage] || undefined,
      search: search || undefined,
      isVisible: visibilityFilter ? visibilityFilter === 'visible' : undefined,
      isFeatured: featuredFilter ? featuredFilter === 'featured' : undefined,
    },
    skip: !currentWorkspace, // Don't query until workspace context is available
    onCompleted: (data) => {
      // Store cursor for next page
      if (data?.categories?.pageInfo?.endCursor) {
        setCursors(prev => ({
          ...prev,
          [currentPage + 1]: data.categories.pageInfo.endCursor
        }));
      }
    }
  });

  // Debug: Log query state
  console.log('[CategoriesListContainer] Query state:', {
    loading,
    hasData: !!data,
    hasError: !!error,
    isSkipped: !currentWorkspace,
  });

  // Transform GraphQL data to component format
  const categories = data?.categories?.edges?.map(edge => ({
    id: edge?.node?.id || '',
    name: edge?.node?.name || '',
    description: edge?.node?.description || '',
    slug: edge?.node?.slug || '',
    isVisible: edge?.node?.isVisible || false,
    isFeatured: edge?.node?.isFeatured || false,
    sortOrder: edge?.node?.sortOrder || 0,
    productCount: edge?.node?.productCount || 0,
    featuredMedia: edge?.node?.featuredMedia ? {
      id: edge.node.featuredMedia.id,
      url: edge.node.featuredMedia.url,
      thumbnailUrl: edge.node.featuredMedia.thumbnailUrl,
      optimizedUrl: edge.node.featuredMedia.optimizedUrl,
      width: edge.node.featuredMedia.width,
      height: edge.node.featuredMedia.height,
    } : undefined,
    createdAt: edge?.node?.createdAt || '',
    updatedAt: edge?.node?.updatedAt || '',
  })).filter(Boolean) || [];

  const hasNextPage = data?.categories?.pageInfo?.hasNextPage || false;
  const totalCount = data?.categories?.totalCount || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  // Handlers
  const handleAddCategory = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/products/categories/add`);
  };

  const handleEditCategory = (categoryId: string) => {
    router.push(`/workspace/${currentWorkspace?.id}/store/products/categories/${categoryId}/edit`);
  };

  const handleViewCategory = (categoryId: string) => {
    // Navigate to category detail page (create this later)
    router.push(`/workspace/${currentWorkspace?.id}/store/products/categories/${categoryId}`);
  };

  const handleToggleVisibility = async (categoryId: string) => {
    try {
      const { data: toggleData } = await toggleCategoryVisibility({
        variables: { id: categoryId },
      });

      if (toggleData?.toggleCategoryVisibility?.success) {
        const newVisibility = toggleData.toggleCategoryVisibility.isVisible;
        toast.success(`Category ${newVisibility ? 'published' : 'hidden'}`);
        refetch(); // Refresh the list
      } else {
        toast.error(toggleData?.toggleCategoryVisibility?.error || 'Failed to toggle visibility');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to toggle visibility');
      console.error('Toggle visibility error:', err);
    }
  };

  const handleDeleteCategory = async (categoryId: string) => {
    try {
      const { data: deleteData } = await deleteCategory({
        variables: {
          id: categoryId,
        },
      });

      if (deleteData?.deleteCategory?.success) {
        toast.success('Category deleted successfully');
        refetch(); // Refresh the list
      } else {
        toast.error(deleteData?.deleteCategory?.error || 'Failed to delete category');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete category');
      console.error('Delete category error:', err);
    }
  };

  const handleBulkAction = (action: 'archive' | 'delete' | 'export') => {
    // TODO: Implement bulk actions with GraphQL mutations
    toast.info(`Bulk ${action} ${selectedCategories.length} categories - Coming soon!`);
  };

  // Pagination handlers
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      handlePageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (hasNextPage) {
      handlePageChange(currentPage + 1);
    }
  };

  // Reset to page 1 when filters change
  React.useEffect(() => {
    setCurrentPage(1);
    setCursors({});
  }, [search, visibilityFilter, featuredFilter]);

  // Error state
  if (error) {
    return (
      <div className="px-4 lg:px-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <p>Failed to load categories</p>
              <p className="text-sm text-muted-foreground">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Mobile selection handlers
  const handleSelectCategory = (categoryId: string) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const handleLongPressCategory = (categoryId: string) => {
    if (!selectedCategories.includes(categoryId)) {
      setSelectedCategories([categoryId]);
    }
  };

  const handleClearSelection = () => {
    setSelectedCategories([]);
  };

  // Mobile View
  if (isMobile) {
    return (
      <div className="px-4 pt-4">
        <MobileCategoriesList
          categories={categories as any}
          workspaceId={currentWorkspace?.id || ''}
          searchTerm={search}
          onSearchChange={setSearch}
          selectedCategories={selectedCategories}
          onSelectCategory={handleSelectCategory}
          onLongPressCategory={handleLongPressCategory}
          onClearSelection={handleClearSelection}
          isLoading={loading}
        />
      </div>
    );
  }

  // Desktop View
  return (
    <div className="space-y-4 px-4 lg:px-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Categories</h1>
        <p className="text-sm text-muted-foreground">
          Organize your products into categories ({totalCount} total)
        </p>
      </div>

      {/* Filters */}
      <CategoriesFilters
        searchValue={search}
        onSearchChange={setSearch}
        visibilityFilter={visibilityFilter}
        onVisibilityFilterChange={setVisibilityFilter}
        featuredFilter={featuredFilter}
        onFeaturedFilterChange={setFeaturedFilter}
      />

      {/* Toolbar (Bulk Actions) */}
      <CategoriesToolbar
        selectedCount={selectedCategories.length}
        onBulkAction={handleBulkAction}
        onAddCategory={handleAddCategory}
      />

      {/* Categories Table */}
      {loading && categories.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading categories...</p>
            </div>
          </CardContent>
        </Card>
      ) : categories.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">
                {(search || visibilityFilter || featuredFilter) ? 'No categories found' : 'No categories yet'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <CategoriesTable
          categories={categories}
          onEdit={handleEditCategory}
          onView={handleViewCategory}
          onToggleVisibility={handleToggleVisibility}
          onDelete={handleDeleteCategory}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2">
          <div className="text-sm text-muted-foreground">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} categories
          </div>
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={handlePreviousPage}
                  className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>

              {/* Page Numbers */}
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNumber;
                if (totalPages <= 5) {
                  pageNumber = i + 1;
                } else if (currentPage <= 3) {
                  pageNumber = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNumber = totalPages - 4 + i;
                } else {
                  pageNumber = currentPage - 2 + i;
                }

                return (
                  <PaginationItem key={pageNumber}>
                    <PaginationLink
                      onClick={() => handlePageChange(pageNumber)}
                      isActive={currentPage === pageNumber}
                      className="cursor-pointer"
                    >
                      {pageNumber}
                    </PaginationLink>
                  </PaginationItem>
                );
              })}

              {totalPages > 5 && currentPage < totalPages - 2 && (
                <PaginationItem>
                  <PaginationEllipsis />
                </PaginationItem>
              )}

              <PaginationItem>
                <PaginationNext
                  onClick={handleNextPage}
                  className={!hasNextPage ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}
    </div>
  );
}