'use client'

import { Input } from '@/components/shadcn-ui/input'
import { Label } from '@/components/shadcn-ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select'
import { Search, ArrowUpDown, SortAsc } from 'lucide-react'
import { Button } from '@/components/shadcn-ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/shadcn-ui/popover'
import { cn } from '@/lib/utils'

interface SearchAndFiltersProps {
  /** Search query */
  search: string

  /** Search change handler */
  onSearchChange: (value: string) => void

  /** Sort by */
  sortBy: 'date' | 'name' | 'size'

  /** Sort by change handler */
  onSortByChange: (value: 'date' | 'name' | 'size') => void

  /** Sort order */
  sortOrder: 'asc' | 'desc'

  /** Sort order change handler */
  onSortOrderChange: (value: 'asc' | 'desc') => void

  /** Compact mode for mobile - inline layout */
  compact?: boolean
}

export function SearchAndFilters({
  search,
  onSearchChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onSortOrderChange,
  compact = false,
}: SearchAndFiltersProps) {
  // Compact mode: horizontal layout for mobile
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Filter by title"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 h-9"
          />
        </div>

        {/* Sort Popover */}
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" size="icon" className="h-9 w-9 shrink-0">
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-48 p-2">
            <div className="space-y-2">
              <Select value={sortBy} onValueChange={onSortByChange}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="size">Size</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sortOrder} onValueChange={onSortOrderChange}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">
                    {sortBy === 'date' ? 'Newest' : 'Largest'}
                  </SelectItem>
                  <SelectItem value="asc">
                    {sortBy === 'date' ? 'Oldest' : 'Smallest'}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    )
  }

  // Default: vertical layout for desktop sidebar
  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="space-y-2">
        <Label htmlFor="media-search">Search files</Label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            id="media-search"
            type="text"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Sort By */}
      <div className="space-y-2">
        <Label>Sort by</Label>
        <Select value={sortBy} onValueChange={onSortByChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date">Date uploaded</SelectItem>
            <SelectItem value="name">File name</SelectItem>
            <SelectItem value="size">File size</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Sort Order */}
      <div className="space-y-2">
        <Label>Order</Label>
        <Select value={sortOrder} onValueChange={onSortOrderChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">
              {sortBy === 'date' ? 'Newest first' : 'Largest first'}
            </SelectItem>
            <SelectItem value="asc">
              {sortBy === 'date' ? 'Oldest first' : 'Smallest first'}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
