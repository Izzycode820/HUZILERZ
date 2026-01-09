'use client';

/**
 * Orders List Container (Smart Component)
 *
 * Industry Standard Pattern:
 * - Container handles data fetching (GraphQL)
 * - Presentational components handle UI (list/ folder)
 * - Clean separation of concerns
 */

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { OrdersTable } from './OrdersTable';
import { OrdersFilters } from './OrdersFilters';
import { MobileOrdersList } from './mobile';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from '@/components/shadcn-ui/pagination';
import { Plus, Archive, XCircle, Package, ChevronDown, CreditCard } from 'lucide-react';
import { useQuery, useMutation } from '@apollo/client/react';
import { GetOrdersDocument } from '@/services/graphql/admin-store/queries/orders/__generated__/getOrders.generated';
import { BulkUpdateOrderStatusDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/BulkUpdateOrderStatus.generated';
import { ArchiveOrderDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/ArchiveOrder.generated';
import { UnarchiveOrderDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/UnarchiveOrder.generated';
import { CancelOrderDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/CancelOrder.generated';
import { MarkOrderAsPaidDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/MarkOrderAsPaid.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';

type TabValue = 'all' | 'unfulfilled' | 'unpaid' | 'open' | 'archived';

export default function OrdersListContainer() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);
  const isMobile = useIsMobile();

  // State
  const [selectedOrders, setSelectedOrders] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<TabValue>('all');

  // Pagination state
  const pageSize = 20;
  const [currentPage, setCurrentPage] = useState(1);
  const [cursors, setCursors] = useState<{ [page: number]: string }>({});

  // Filters
  const [paymentStatus, setPaymentStatus] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<string | null>(null);
  const [orderSource, setOrderSource] = useState<string | null>(null);
  const [shippingRegion, setShippingRegion] = useState<string | null>(null);

  // Determine status filter based on active tab
  const getStatusFilter = () => {
    switch (activeTab) {
      case 'unfulfilled':
        return 'UNFULFILLED';
      case 'unpaid':
        return null; // We'll handle this via paymentStatus
      case 'open':
        return 'PENDING';
      case 'archived':
        return null; // Archived is handled via is_archived boolean, not status
      default:
        return null;
    }
  };

  // Override payment status for "unpaid" tab
  const effectivePaymentStatus = activeTab === 'unpaid' ? 'PENDING' : paymentStatus;

  // Determine isArchived filter based on active tab
  const getIsArchivedFilter = () => {
    if (activeTab === 'archived') {
      return true;  // Show only archived orders
    }
    // For all other tabs (including 'all'), exclude archived orders
    return false;  // Show only non-archived orders
  };

  // Fetch orders with GraphQL
  const { data, loading, error, refetch } = useQuery(GetOrdersDocument, {
    variables: {
      first: pageSize,
      after: cursors[currentPage] || undefined,
      status: getStatusFilter() as any,
      paymentStatus: effectivePaymentStatus as any,
      paymentMethod: paymentMethod as any,
      orderSource: orderSource as any,
      shippingRegion: shippingRegion as any,
      isArchived: getIsArchivedFilter(),
    },
    skip: !currentWorkspace,
  });

  // Store cursor for next page when data changes
  React.useEffect(() => {
    const endCursor = data?.orders?.pageInfo?.endCursor;
    if (endCursor) {
      setCursors(prev => ({
        ...prev,
        [currentPage + 1]: endCursor
      }));
    }
  }, [data?.orders?.pageInfo?.endCursor, currentPage]);

  // Mutations for bulk actions
  const [bulkUpdateStatus] = useMutation(BulkUpdateOrderStatusDocument, {
    refetchQueries: ['GetOrders'],
    awaitRefetchQueries: true,
  });

  const [archiveOrder] = useMutation(ArchiveOrderDocument, {
    refetchQueries: ['GetOrders'],
    awaitRefetchQueries: true,
  });

  const [unarchiveOrder] = useMutation(UnarchiveOrderDocument, {
    refetchQueries: ['GetOrders'],
    awaitRefetchQueries: true,
  });

  const [cancelOrder] = useMutation(CancelOrderDocument, {
    refetchQueries: ['GetOrders'],
    awaitRefetchQueries: true,
  });

  const [markOrderAsPaid] = useMutation(MarkOrderAsPaidDocument, {
    refetchQueries: ['GetOrders'],
    awaitRefetchQueries: true,
  });

  // Transform GraphQL data
  const orders = (data?.orders?.edges?.map(edge => edge?.node).filter((node): node is NonNullable<typeof node> => node !== null && node !== undefined)) || [];
  const totalCount = data?.orders?.totalCount || 0;
  const hasNextPage = data?.orders?.pageInfo?.hasNextPage || false;
  const totalPages = Math.ceil(totalCount / pageSize);

  // Handlers
  const handleAddOrder = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/orders/add`);
  };

  const handleSelectOrder = (orderId: string) => {
    setSelectedOrders(prev =>
      prev.includes(orderId)
        ? prev.filter(id => id !== orderId)
        : [...prev, orderId]
    );
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedOrders(orders.filter(Boolean).map(order => order.id));
    } else {
      setSelectedOrders([]);
    }
  };

  // Pagination handlers
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    setSelectedOrders([]);
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
    setSelectedOrders([]);
    setCurrentPage(1);
    setCursors({});
    // Reset payment status when changing tabs (except for unpaid tab)
    if (value !== 'unpaid') {
      setPaymentStatus(null);
    }
  };

  // Long press handler for mobile selection
  const handleLongPressOrder = (orderId: string) => {
    // Start selection mode and select this order
    if (!selectedOrders.includes(orderId)) {
      setSelectedOrders([orderId]);
    }
  };

  // Bulk action handlers
  const handleBulkArchive = async () => {
    if (selectedOrders.length === 0) return;

    if (!confirm(`Are you sure you want to archive ${selectedOrders.length} order(s)?`)) return;

    try {
      // Run all archive operations in parallel
      const results = await Promise.all(
        selectedOrders.map(orderId =>
          archiveOrder({ variables: { orderId } })
        )
      );

      const successCount = results.filter(r => r.data?.archiveOrder?.success).length;
      const failCount = results.length - successCount;

      // Show results
      if (successCount > 0) {
        toast.success(`${successCount} order(s) archived successfully`);
      }
      if (failCount > 0) {
        toast.error(`Failed to archive ${failCount} order(s)`);
      }

      // Clear selection and refetch will happen automatically
      setSelectedOrders([]);
    } catch (e) {
      toast.error('An error occurred during bulk archive');
      console.error('Bulk archive error:', e);
    }
  };

  const handleBulkCancel = async () => {
    if (selectedOrders.length === 0) return;

    if (!confirm(`Are you sure you want to cancel ${selectedOrders.length} order(s)? This action cannot be undone.`)) return;

    try {
      // Run all cancel operations in parallel
      const results = await Promise.all(
        selectedOrders.map(orderId =>
          cancelOrder({ variables: { orderId, reason: 'Bulk cancelled by merchant' } })
        )
      );

      const successCount = results.filter(r => r.data?.cancelOrder?.success).length;
      const failCount = results.length - successCount;

      // Show results
      if (successCount > 0) {
        toast.success(`${successCount} order(s) cancelled successfully`);
      }
      if (failCount > 0) {
        toast.error(`Failed to cancel ${failCount} order(s)`);
      }

      // Clear selection and refetch will happen automatically
      setSelectedOrders([]);
    } catch (e) {
      toast.error('An error occurred during bulk cancel');
      console.error('Bulk cancel error:', e);
    }
  };

  const handleBulkMarkAsPaid = async () => {
    if (selectedOrders.length === 0) return;

    if (!confirm(`Are you sure you want to mark ${selectedOrders.length} order(s) as paid?`)) return;

    try {
      // Run all operations in parallel
      const results = await Promise.all(
        selectedOrders.map(orderId =>
          markOrderAsPaid({ variables: { orderId } })
        )
      );

      const successCount = results.filter(r => r.data?.markOrderAsPaid?.success).length;
      const failCount = results.length - successCount;

      // Show results
      if (successCount > 0) {
        toast.success(`${successCount} order(s) marked as paid`);
      }
      if (failCount > 0) {
        toast.error(`Failed to mark ${failCount} order(s) as paid`);
      }

      // Clear selection and refetch will happen automatically
      setSelectedOrders([]);
    } catch (e) {
      toast.error('An error occurred during bulk mark as paid');
      console.error('Bulk mark as paid error:', e);
    }
  };

  const handleBulkStatusUpdate = async (newStatus: string, statusLabel?: string) => {
    if (selectedOrders.length === 0) return;

    try {
      const result = await bulkUpdateStatus({
        variables: {
          bulkData: {
            updates: selectedOrders.map(orderId => ({
              orderId,
              newStatus,
            })),
          },
        },
      });

      if (result.data?.bulkUpdateOrderStatus?.success) {
        const { successfulUpdates, failedUpdates } = result.data.bulkUpdateOrderStatus;

        if (successfulUpdates && successfulUpdates > 0) {
          const label = statusLabel || newStatus;
          toast.success(`${successfulUpdates} order(s) marked as ${label}`);
        }
        if (failedUpdates && failedUpdates.length > 0) {
          toast.error(`Failed to update ${failedUpdates.length} order(s)`);
        }

        // Clear selection and refetch will happen automatically
        setSelectedOrders([]);
      } else {
        toast.error(result.data?.bulkUpdateOrderStatus?.error || 'Failed to update orders');
      }
    } catch (e) {
      toast.error('An error occurred during bulk update');
      console.error('Bulk status update error:', e);
    }
  };

  // Individual archive/unarchive handlers
  const handleArchiveOrder = async (orderId: string) => {
    try {
      const result = await archiveOrder({ variables: { orderId } });

      if (result.data?.archiveOrder?.success) {
        toast.success('Order archived successfully');
      } else {
        toast.error(result.data?.archiveOrder?.error || 'Failed to archive order');
      }
    } catch (e) {
      toast.error('An error occurred while archiving order');
      console.error('Archive order error:', e);
    }
  };

  const handleUnarchiveOrder = async (orderId: string) => {
    try {
      const result = await unarchiveOrder({ variables: { orderId } });

      if (result.data?.unarchiveOrder?.success) {
        toast.success('Order unarchived successfully');
      } else {
        toast.error(result.data?.unarchiveOrder?.error || 'Failed to unarchive order');
      }
    } catch (e) {
      toast.error('An error occurred while unarchiving order');
      console.error('Unarchive order error:', e);
    }
  };

  // Reset to page 1 when filters change
  React.useEffect(() => {
    setCurrentPage(1);
    setCursors({});
  }, [paymentStatus, paymentMethod, orderSource, shippingRegion]);

  // Error state
  if (error) {
    return (
      <div className="px-4 lg:px-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <p>Failed to load orders</p>
              <p className="text-sm text-muted-foreground">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Mobile filter chips based on tabs
  const mobileFilterChips = [
    { value: 'all', label: 'All' },
    { value: 'unfulfilled', label: 'Unfulfilled' },
    { value: 'unpaid', label: 'Unpaid' },
    { value: 'open', label: 'Open' },
    { value: 'archived', label: 'Archived' },
  ];

  // Mobile View
  if (isMobile) {
    return (
      <div className="px-4 pt-4">
        <MobileOrdersList
          orders={orders}
          workspaceId={currentWorkspace?.id || ''}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          chips={mobileFilterChips}
          activeChip={activeTab}
          onChipChange={handleTabChange}
          selectedOrders={selectedOrders}
          onSelectOrder={handleSelectOrder}
          onLongPressOrder={handleLongPressOrder}
          onClearSelection={() => setSelectedOrders([])}
          onBulkArchive={handleBulkArchive}
          onBulkMarkAsPaid={handleBulkMarkAsPaid}
          onBulkCancel={handleBulkCancel}
          onBulkMarkAsShipped={() => handleBulkStatusUpdate('shipped', 'shipped')}
          onBulkMarkAsDelivered={() => handleBulkStatusUpdate('delivered', 'delivered')}
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
          <h1 className="text-2xl font-bold">Orders</h1>
          <p className="text-sm text-muted-foreground">
            Manage your store orders ({totalCount} total)
          </p>
        </div>
        <Button onClick={handleAddOrder}>
          <Plus className="mr-2 h-4 w-4" />
          Create order
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="unfulfilled">Unfulfilled</TabsTrigger>
          <TabsTrigger value="unpaid">Unpaid</TabsTrigger>
          <TabsTrigger value="open">Open</TabsTrigger>
          <TabsTrigger value="archived">Archived</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Filters */}
      <OrdersFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        paymentStatus={paymentStatus}
        onPaymentStatusChange={setPaymentStatus}
        paymentMethod={paymentMethod}
        onPaymentMethodChange={setPaymentMethod}
        orderSource={orderSource}
        onOrderSourceChange={setOrderSource}
        shippingRegion={shippingRegion}
        onShippingRegionChange={setShippingRegion}
      />

      {/* Bulk Actions Toolbar */}
      {selectedOrders.length > 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">
                {selectedOrders.length} order{selectedOrders.length !== 1 ? 's' : ''} selected
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBulkCancel}
                >
                  <XCircle className="mr-1 h-3 w-3" />
                  Cancel orders
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBulkArchive}
                >
                  <Archive className="mr-1 h-3 w-3" />
                  Archive
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBulkMarkAsPaid}
                >
                  <CreditCard className="mr-1 h-3 w-3" />
                  Mark as paid
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Package className="mr-1 h-3 w-3" />
                      Fulfillment
                      <ChevronDown className="ml-1 h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleBulkStatusUpdate('delivered', 'delivered')}>
                      Mark as delivered
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleBulkStatusUpdate('unfulfilled', 'unfulfilled')}>
                      Mark as not delivered
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkStatusUpdate('on_hold', 'on hold')}
                >
                  Mark on hold
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkStatusUpdate('processing', 'processing')}
                >
                  Mark processing
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedOrders([])}
                >
                  Clear selection
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Orders Table */}
      {loading && orders.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading orders...</p>
            </div>
          </CardContent>
        </Card>
      ) : orders.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-muted-foreground">No orders found</p>
              {(searchTerm || paymentStatus || paymentMethod || orderSource || shippingRegion) ? (
                <p className="text-sm text-muted-foreground mt-2">Try adjusting your filters</p>
              ) : (
                <div className="mt-4">
                  <Button onClick={handleAddOrder}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create your first order
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <OrdersTable
          orders={orders}
          selectedOrders={selectedOrders}
          onSelectOrder={handleSelectOrder}
          onSelectAll={handleSelectAll}
          workspaceId={currentWorkspace?.id || ''}
          onArchiveOrder={handleArchiveOrder}
          onUnarchiveOrder={handleUnarchiveOrder}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2">
          <div className="text-sm text-muted-foreground">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} orders
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
