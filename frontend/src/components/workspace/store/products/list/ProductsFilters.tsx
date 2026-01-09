'use client'

import { useState } from 'react'
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu'
import { Search, Filter, X } from 'lucide-react'

interface ProductsFiltersProps {
  searchValue?: string
  onSearchChange?: (search: string) => void
  statusFilter?: string
  onStatusFilterChange?: (status: string) => void
  categoryFilter?: string
  onCategoryFilterChange?: (category: string) => void
  typeFilter?: string
  onTypeFilterChange?: (type: string) => void
}

export function ProductsFilters({
  searchValue = '',
  onSearchChange,
  statusFilter = '',
  onStatusFilterChange,
  categoryFilter = '',
  onCategoryFilterChange,
  typeFilter = '',
  onTypeFilterChange,
}: ProductsFiltersProps) {
  // Use props directly, no internal state for values


  const handleSearchChange = (value: string) => {
    onSearchChange?.(value)
  }

  const handleStatusChange = (value: string) => {
    onStatusFilterChange?.(value)
  }

  const handleCategoryChange = (value: string) => {
    onCategoryFilterChange?.(value)
  }

  const handleTypeChange = (value: string) => {
    onTypeFilterChange?.(value)
  }

  const clearFilters = () => {
    onSearchChange?.('')
    onStatusFilterChange?.('')
    onCategoryFilterChange?.('')
    onTypeFilterChange?.('')
  }

  const hasActiveFilters = searchValue || statusFilter || categoryFilter || typeFilter

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search products by name or SKU..."
            value={searchValue}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Filters
              {hasActiveFilters && (
                <div className="h-2 w-2 rounded-full bg-primary"></div>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-80 p-4 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select value={statusFilter} onValueChange={handleStatusChange}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All statuses</SelectItem>
                  <SelectItem value="published">Published</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <Select value={categoryFilter} onValueChange={handleCategoryChange}>
                <SelectTrigger>
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All categories</SelectItem>
                  <SelectItem value="electronics">Electronics</SelectItem>
                  <SelectItem value="clothing">Clothing</SelectItem>
                  <SelectItem value="home">Home & Garden</SelectItem>
                  <SelectItem value="books">Books</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Type</label>
              <Select value={typeFilter} onValueChange={handleTypeChange}>
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All types</SelectItem>
                  <SelectItem value="physical">Physical</SelectItem>
                  <SelectItem value="digital">Digital</SelectItem>
                  <SelectItem value="service">Service</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {hasActiveFilters && (
              <Button
                variant="outline"
                onClick={clearFilters}
                className="w-full flex items-center gap-2"
              >
                <X className="h-4 w-4" />
                Clear filters
              </Button>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {hasActiveFilters && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Active filters:</span>
          {searchValue && (
            <span className="bg-muted px-2 py-1 rounded text-xs">
              Search: "{searchValue}"
            </span>
          )}
          {statusFilter && (
            <span className="bg-muted px-2 py-1 rounded text-xs">
              Status: {statusFilter}
            </span>
          )}
          {categoryFilter && (
            <span className="bg-muted px-2 py-1 rounded text-xs">
              Category: {categoryFilter}
            </span>
          )}
          {typeFilter && (
            <span className="bg-muted px-2 py-1 rounded text-xs">
              Type: {typeFilter}
            </span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-6 px-2 text-xs"
          >
            Clear all
          </Button>
        </div>
      )}
    </div>
  )
}