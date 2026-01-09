'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CustomersTable } from './CustomersTable';
import { CustomersFilters } from './CustomersFilters';
import { MobileCustomersList } from './mobile';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from '@/components/shadcn-ui/pagination';
import { Plus } from 'lucide-react';
import { useQuery } from '@apollo/client/react';
import { GetCustomersDocument } from '@/services/graphql/admin-store/queries/customers/__generated__/GetCustomers.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';

type TabValue = 'all' | 'active' | 'inactive';

export default function CustomersListContainer() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);
  const isMobile = useIsMobile();

  // State
  const [selectedCustomers, setSelectedCustomers] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<TabValue>('all');

  // Pagination state
  const pageSize = 20;
  const [currentPage, setCurrentPage] = useState(1);
  const [cursors, setCursors] = useState<{ [page: number]: string }>({});

  // Filters
  const [customerType, setCustomerType] = useState<string | null>(null);
  const [region, setRegion] = useState<string | null>(null);

  // Determine isActive filter based on active tab
  const getIsActiveFilter = () => {
    switch (activeTab) {
      case 'active':
        return true;
      case 'inactive':
        return false;
      default:
        return undefined;
    }
  };

  // Fetch customers with GraphQL
  const { data, loading, error, refetch } = useQuery(GetCustomersDocument, {
    variables: {
      first: pageSize,
      after: cursors[currentPage] || undefined,
      name_Icontains: searchTerm || undefined,
      customerType: customerType as any,
      region: region as any,
      isActive: getIsActiveFilter(),
    },
    skip: !currentWorkspace,
    skip: !currentWorkspace,
  });

  // Store cursor for next page when data changes
  React.useEffect(() => {
    if (data?.customers?.pageInfo?.endCursor) {
      setCursors(prev => ({
        ...prev,
        [currentPage + 1]: data.customers.pageInfo.endCursor! // Non-null assertion safe due to check
      }));
    }
  }, [data, currentPage]);

  // Transform GraphQL data
  const customers = data?.customers?.edges?.map(edge => edge?.node).filter((node): node is NonNullable<typeof node> => !!node) || [];
  const totalCount = data?.customers?.totalCount || 0;
  const hasNextPage = data?.customers?.pageInfo?.hasNextPage || false;
  const totalPages = Math.ceil(totalCount / pageSize);

  // Handlers
  const handleAddCustomer = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/customers/add`);
  };

  const handleSelectCustomer = (customerId: string) => {
    setSelectedCustomers(prev =>
      prev.includes(customerId)
        ? prev.filter(id => id !== customerId)
        : [...prev, customerId]
    );
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedCustomers(customers.map(customer => customer.id).filter((id): id is string => !!id));
    } else {
      setSelectedCustomers([]);
    }
  };

  // Pagination handlers
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    setSelectedCustomers([]);
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

  const handleTabChange = (value: string) => {
    setActiveTab(value as TabValue);
    setSelectedCustomers([]);
    setCurrentPage(1);
    setCursors({});
  };

  // Reset to page 1 when filters change
  React.useEffect(() => {
    setCurrentPage(1);
    setCursors({});
  }, [searchTerm, customerType, region]);

  // Error state
  if (error) {
    return (
      <div className="px-4 lg:px-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <p>Failed to load customers</p>
              <p className="text-sm text-muted-foreground">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Long press handler for mobile selection
  const handleLongPressCustomer = (customerId: string) => {
    if (!selectedCustomers.includes(customerId)) {
      setSelectedCustomers([customerId]);
    }
  };

  // Clear selection handler
  const handleClearSelection = () => {
    setSelectedCustomers([]);
  };

  // Mobile filter chips
  const mobileFilterChips = [
    { value: 'all', label: 'All' },
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
  ];

  // Handle chip change for mobile (maps to tab)
  const handleChipChange = (value: string) => {
    handleTabChange(value);
  };

  // Mobile View
  if (isMobile) {
    return (
      <div className="px-4 pt-4">
        <MobileCustomersList
          customers={customers as any}
          workspaceId={currentWorkspace?.id || ''}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          chips={mobileFilterChips}
          activeChip={activeTab}
          onChipChange={handleChipChange}
          selectedCustomers={selectedCustomers}
          onSelectCustomer={handleSelectCustomer}
          onLongPressCustomer={handleLongPressCustomer}
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
          <h1 className="text-2xl font-bold">Customers</h1>
          <p className="text-sm text-muted-foreground">
            Manage your store customers ({totalCount} total)
          </p>
        </div>
        <Button onClick={handleAddCustomer}>
          <Plus className="mr-2 h-4 w-4" />
          Add customer
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="inactive">Inactive</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Filters */}
      <CustomersFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        customerType={customerType}
        onCustomerTypeChange={setCustomerType}
        region={region}
        onRegionChange={setRegion}
      />

      {/* Bulk Actions Toolbar */}
      {selectedCustomers.length > 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">
                {selectedCustomers.length} customer{selectedCustomers.length !== 1 ? 's' : ''} selected
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  Export
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedCustomers([])}
                >
                  Clear selection
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Customers Table */}
      {loading && customers.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading customers...</p>
            </div>
          </CardContent>
        </Card>
      ) : customers.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">
                {(searchTerm || customerType || region) ? 'No customers found' : 'No customers yet'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <CustomersTable
          customers={customers}
          selectedCustomers={selectedCustomers}
          onSelectCustomer={handleSelectCustomer}
          onSelectAll={handleSelectAll}
          workspaceId={currentWorkspace?.id || ''}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2">
          <div className="text-sm text-muted-foreground">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} customers
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
