'use client'

/**
 * Inventory Management Page
 *
 * Features:
 * - Lists all inventory records (variant × location combinations)
 * - Inline editing for onhand and available quantities
 * - Real-time updates with optimistic UI
 * - Filters by location and stock status
 * - Cursor-based pagination
 */

import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@apollo/client/react'
import { Card, CardContent } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Button } from '@/components/shadcn-ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select'
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from '@/components/shadcn-ui/pagination'
import { InventoryTable } from '@/components/workspace/store/inventory/InventoryTable'
import { MobileInventoryList } from '@/components/workspace/store/inventory/mobile'
import { useIsMobile } from '@/hooks/shadcn/use-mobile'
import { GetInventoryDocument } from '@/services/graphql/admin-store/queries/inventory/__generated__/GetInventory.generated'
import { GetLocationsDocument } from '@/services/graphql/admin-store/queries/inventory/__generated__/GetLocations.generated'
import { UpdateInventoryDocument } from '@/services/graphql/admin-store/mutations/inventory/__generated__/UpdateInventory.generated'
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore'
import { toast } from 'sonner'
import { Search, Package } from 'lucide-react'

export default function InventoryPage() {
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace)
  const isMobile = useIsMobile()

  const [searchQuery, setSearchQuery] = useState('')
  const [locationFilter, setLocationFilter] = useState<string | undefined>()
  const [stockStatusFilter, setStockStatusFilter] = useState<string | undefined>()
  const [selectedItems, setSelectedItems] = useState<string[]>([])

  // Pagination state
  const pageSize = 20
  const [currentPage, setCurrentPage] = useState(1)
  const [cursors, setCursors] = useState<{ [page: number]: string | undefined }>({})

  // Fetch locations for filter
  const { data: locationsData } = useQuery(GetLocationsDocument, {
    skip: !currentWorkspace,
  })

  // Fetch inventory
  const { data, loading, error, refetch } = useQuery(GetInventoryDocument, {
    variables: {
      first: pageSize,
      after: cursors[currentPage] || undefined,
      location: locationFilter,
    },
    skip: !currentWorkspace,
  })

  // Store cursor for next page when data changes
  useEffect(() => {
    const endCursor = data?.inventory?.pageInfo?.endCursor;
    if (endCursor && typeof endCursor === 'string') {
      setCursors(prev => ({
        ...prev,
        [currentPage + 1]: endCursor
      }))
    }
  }, [data, currentPage])

  // Update inventory mutation
  const [updateInventory] = useMutation(UpdateInventoryDocument)

  // Transform GraphQL data
  const inventory = data?.inventory?.edges
    ?.map((edge) => edge?.node)
    .filter((node): node is NonNullable<typeof node> => node !== null && node !== undefined) || []

  // Apply client-side filters (search and stock status)
  const filteredInventory = inventory.filter((item) => {
    // Search filter (product name, SKU, variant options)
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchesProduct = item.productName?.toLowerCase().includes(query)
      const matchesSku = item.sku?.toLowerCase().includes(query)
      const matchesVariant =
        item.variant?.option1?.toLowerCase().includes(query) ||
        item.variant?.option2?.toLowerCase().includes(query) ||
        item.variant?.option3?.toLowerCase().includes(query)

      if (!matchesProduct && !matchesSku && !matchesVariant) {
        return false
      }
    }

    // Stock status filter
    if (stockStatusFilter && stockStatusFilter !== 'all') {
      if (item.stockStatus !== stockStatusFilter) {
        return false
      }
    }

    return true
  })

  const hasNextPage = data?.inventory?.pageInfo?.hasNextPage || false
  const totalCount = data?.inventory?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)
  const locations = (locationsData?.locations || []).filter((loc): loc is NonNullable<typeof loc> => loc !== null && loc !== undefined)

  // Handle inventory update
  const handleUpdateInventory = async (
    inventoryId: string,
    variantId: string,
    locationId: string,
    field: 'onhand' | 'available',
    value: number
  ) => {
    try {
      const { data: updateData } = await updateInventory({
        variables: {
          updateData: {
            variantId,
            locationId,
            [field]: value,
          },
        },
      })

      if (updateData?.updateInventory?.success) {
        toast.success(`${field === 'onhand' ? 'On Hand' : 'Available'} updated successfully`)
        refetch() // Refresh to get computed fields
      } else {
        toast.error(updateData?.updateInventory?.error || 'Failed to update inventory')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to update inventory')
      console.error('Update inventory error:', err)
    }
  }

  // Pagination handlers
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      handlePageChange(currentPage - 1)
    }
  }

  const handleNextPage = () => {
    if (hasNextPage) {
      handlePageChange(currentPage + 1)
    }
  }

  // Clear filters
  const handleClearFilters = () => {
    setSearchQuery('')
    setLocationFilter(undefined)
    setStockStatusFilter(undefined)
    setCurrentPage(1)
    setCursors({})
  }

  // Reset to page 1 when location filter changes
  useEffect(() => {
    setCurrentPage(1)
    setCursors({})
  }, [locationFilter])

  const hasFilters = searchQuery || locationFilter || stockStatusFilter

  // Error state
  if (error) {
    return (
      <div className="px-4 lg:px-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <p>Failed to load inventory</p>
              <p className="text-sm text-muted-foreground">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Mobile selection handlers
  const handleSelectItem = (itemId: string) => {
    setSelectedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleLongPressItem = (itemId: string) => {
    if (!selectedItems.includes(itemId)) {
      setSelectedItems([itemId]);
    }
  };

  const handleClearSelection = () => {
    setSelectedItems([]);
  };

  // Mobile filter chips
  const mobileFilterChips = [
    { value: 'all', label: 'All' },
    { value: 'in_stock', label: 'In Stock' },
    { value: 'low_stock', label: 'Low Stock' },
    { value: 'out_of_stock', label: 'Out of Stock' },
  ];

  // Handle chip change for mobile
  const handleChipChange = (value: string) => {
    setStockStatusFilter(value === 'all' ? undefined : value);
  };

  // Mobile View
  if (isMobile) {
    return (
      <div className="px-4 pt-4">
        <MobileInventoryList
          inventory={filteredInventory}
          workspaceId={currentWorkspace?.id || ''}
          searchTerm={searchQuery}
          onSearchChange={setSearchQuery}
          chips={mobileFilterChips}
          activeChip={stockStatusFilter || 'all'}
          onChipChange={handleChipChange}
          selectedItems={selectedItems}
          onSelectItem={handleSelectItem}
          onLongPressItem={handleLongPressItem}
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
        <h1 className="text-2xl font-bold">Inventory</h1>
        <p className="text-sm text-muted-foreground">
          Manage inventory across all locations ({totalCount} total records)
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by product, SKU, or variant..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Location Filter */}
            <Select value={locationFilter || 'all'} onValueChange={(v) => setLocationFilter(v === 'all' ? undefined : v)}>
              <SelectTrigger className="w-full sm:w-[200px]">
                <SelectValue placeholder="All Locations" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Locations</SelectItem>
                {locations.map((location) => (
                  <SelectItem key={location.id} value={location.id}>
                    {location.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Stock Status Filter */}
            <Select
              value={stockStatusFilter || 'all'}
              onValueChange={(v) => setStockStatusFilter(v === 'all' ? undefined : v)}
            >
              <SelectTrigger className="w-full sm:w-[200px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="in_stock">In Stock</SelectItem>
                <SelectItem value="low_stock">Low Stock</SelectItem>
                <SelectItem value="out_of_stock">Out of Stock</SelectItem>
              </SelectContent>
            </Select>

            {/* Clear Filters */}
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={handleClearFilters}>
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Inventory Table */}
      {loading && filteredInventory.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12">
              <Package className="h-12 w-12 text-muted-foreground mb-4" />
              <div className="animate-pulse text-muted-foreground">Loading inventory...</div>
            </div>
          </CardContent>
        </Card>
      ) : filteredInventory.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12">
              <Package className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No inventory records found</p>
              <p className="text-sm text-muted-foreground">
                {hasFilters ? 'Try adjusting your filters' : 'Add products to create inventory records'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <InventoryTable inventory={filteredInventory} onUpdateInventory={handleUpdateInventory} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-2">
              <div className="text-sm text-muted-foreground">
                Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} records
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
        </>
      )}
    </div>
  )
}
