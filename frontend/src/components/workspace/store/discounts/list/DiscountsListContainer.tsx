'use client';

/**
 * Discounts List Container (Smart Component)
 *
 * Industry Standard Pattern:
 * - Container handles data fetching (GraphQL)
 * - Presentational components handle UI (list/ folder)
 * - Clean separation of concerns
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DiscountsTable } from './DiscountsTable';
import { DiscountsFilters } from './DiscountsFilters';
import { DiscountsEmptyState } from './DiscountsEmptyState';
import { MobileDiscountsList } from './mobile';
import { SelectDiscountTypeModal } from '../create/SelectDiscountTypeModal';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
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
import { GetDiscountsListDocument } from '@/services/graphql/admin-store/queries/discounts/__generated__/GetDiscountsList.generated';
import { DeleteDiscountDocument } from '@/services/graphql/admin-store/mutations/discounts/__generated__/DeleteDiscount.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';
import * as Types from '@/types/workspace/store/graphql-base';

export default function DiscountsListContainer() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);
  const isMobile = useIsMobile();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [showTypeModal, setShowTypeModal] = useState(false);
  const [selectedDiscounts, setSelectedDiscounts] = useState<string[]>([]);

  // Pagination state
  const pageSize = 20;
  const [currentPage, setCurrentPage] = useState(1);
  const [cursors, setCursors] = useState<{ [page: number]: string }>({});

  // Mutations
  const [deleteDiscount] = useMutation(DeleteDiscountDocument);

  // Map string status to enum
  const getStatusEnum = (status: string | undefined): Types.WorkspaceStoreDiscountStatusChoices | undefined => {
    if (!status) return undefined;
    const enumMap: Record<string, Types.WorkspaceStoreDiscountStatusChoices> = {
      active: Types.WorkspaceStoreDiscountStatusChoices.Active,
      scheduled: Types.WorkspaceStoreDiscountStatusChoices.Scheduled,
      expired: Types.WorkspaceStoreDiscountStatusChoices.Expired,
      inactive: Types.WorkspaceStoreDiscountStatusChoices.Inactive,
    };
    return enumMap[status];
  };

  // Fetch discounts with GraphQL (skip until workspace is loaded)
  const { data, loading, error, refetch } = useQuery(GetDiscountsListDocument, {
    variables: {
      first: pageSize,
      after: cursors[currentPage] || undefined,
      search: search || undefined,
      status: getStatusEnum(statusFilter),
    },
    skip: !currentWorkspace,
  });

  // Store cursor for next page when data changes
  useEffect(() => {
    const endCursor = data?.discounts?.pageInfo?.endCursor;
    if (endCursor) {
      setCursors((prev) => ({
        ...prev,
        [currentPage + 1]: endCursor,
      }));
    }
  }, [data, currentPage]);

  // Smart inline refresh: refetch when component mounts or page is re-entered
  useEffect(() => {
    if (currentWorkspace) {
      refetch();
    }
  }, [currentWorkspace, refetch]);

  // Transform GraphQL data to component format
  const discounts =
    data?.discounts?.edges
      ?.map((edge) => edge?.node)
      .filter((node): node is NonNullable<typeof node> => !!node)
      .map((node) => ({
        id: node.id,
        code: node.code,
        name: node.name,
        method: node.method,
        discountType: node.discountType,
        status: node.status,
        discountValueType: node.discountValueType,
        value: node.value,
        customerBuysQuantity: node.customerBuysQuantity,
        customerBuysValue: node.customerBuysValue,
        customerGetsQuantity: node.customerGetsQuantity,
        minimumPurchaseAmount: node.minimumPurchaseAmount,
        minimumQuantityItems: node.minimumQuantityItems,
        limitOnePerCustomer: node.limitOnePerCustomer,
        usageCount: node.usageCount,
        canCombineWithProductDiscounts: node.canCombineWithProductDiscounts,
        canCombineWithOrderDiscounts: node.canCombineWithOrderDiscounts,
        isActive: node.isActive,
        isExpired: node.isExpired,
      })) || [];

  const hasNextPage = data?.discounts?.pageInfo?.hasNextPage || false;
  const totalCount = data?.discounts?.totalCount || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  // Handlers
  const handleAddDiscount = () => {
    setShowTypeModal(true);
  };

  const handleEditDiscount = (discountId: string) => {
    router.push(`/workspace/${currentWorkspace?.id}/store/discounts/${discountId}/edit`);
  };

  const handleDeleteDiscount = async (discountId: string) => {
    try {
      const { data: deleteData } = await deleteDiscount({
        variables: { discountId },
      });

      if (deleteData?.deleteDiscount?.success) {
        toast.success('Discount deleted successfully');
        refetch();
      } else {
        toast.error(deleteData?.deleteDiscount?.error || 'Failed to delete discount');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete discount');
      console.error('Delete discount error:', err);
    }
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
  }, [search, statusFilter]);

  // Error state
  if (error) {
    return (
      <div className="px-4 lg:px-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <p>Failed to load discounts</p>
              <p className="text-sm text-muted-foreground">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Empty state
  if (!loading && discounts.length === 0 && !search && !statusFilter) {
    return (
      <>
        <div className="px-4 lg:px-6">
          <DiscountsEmptyState onAddDiscount={handleAddDiscount} />
        </div>
        <SelectDiscountTypeModal open={showTypeModal} onOpenChange={setShowTypeModal} />
      </>
    );
  }

  // Mobile selection handlers
  const handleSelectDiscount = (discountId: string) => {
    setSelectedDiscounts(prev =>
      prev.includes(discountId)
        ? prev.filter(id => id !== discountId)
        : [...prev, discountId]
    );
  };

  const handleLongPressDiscount = (discountId: string) => {
    if (!selectedDiscounts.includes(discountId)) {
      setSelectedDiscounts([discountId]);
    }
  };

  const handleClearSelection = () => {
    setSelectedDiscounts([]);
  };

  // Mobile filter chips
  const mobileFilterChips = [
    { value: 'all', label: 'All' },
    { value: 'active', label: 'Active' },
    { value: 'scheduled', label: 'Scheduled' },
    { value: 'expired', label: 'Expired' },
  ];

  // Handle chip change for mobile
  const handleChipChange = (value: string) => {
    setStatusFilter(value === 'all' ? undefined : value);
  };

  // Mobile View
  if (isMobile) {
    return (
      <div className="px-4 pt-4">
        <MobileDiscountsList
          discounts={discounts as any}
          workspaceId={currentWorkspace?.id || ''}
          searchTerm={search}
          onSearchChange={setSearch}
          chips={mobileFilterChips}
          activeChip={statusFilter || 'all'}
          onChipChange={handleChipChange}
          selectedDiscounts={selectedDiscounts}
          onSelectDiscount={handleSelectDiscount}
          onLongPressDiscount={handleLongPressDiscount}
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Discounts</h1>
        </div>
        <Button onClick={handleAddDiscount}>Create discount</Button>
      </div>

      {/* Filters */}
      <DiscountsFilters
        searchValue={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
      />

      {/* Discounts Table */}
      {loading && discounts.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading discounts...</p>
            </div>
          </CardContent>
        </Card>
      ) : discounts.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-muted-foreground">No discounts found</p>
              <p className="text-sm text-muted-foreground">Try adjusting your filters</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <DiscountsTable
          discounts={discounts}
          onEdit={handleEditDiscount}
          onDelete={handleDeleteDiscount}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2">
          <div className="text-sm text-muted-foreground">
            Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalCount)} of{' '}
            {totalCount} discounts
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

      {/* Select Discount Type Modal */}
      <SelectDiscountTypeModal open={showTypeModal} onOpenChange={setShowTypeModal} />
    </div>
  );
}
