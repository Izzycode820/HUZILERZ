'use client'

import { Button } from '@/components/shadcn-ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu'
import { Download, Archive, Trash2, MoreHorizontal } from 'lucide-react'

interface CategoriesToolbarProps {
  selectedCount: number
  onBulkAction?: (action: 'archive' | 'delete' | 'export') => void
  onAddCategory?: () => void
}

export function CategoriesToolbar({
  selectedCount,
  onBulkAction,
  onAddCategory,
}: CategoriesToolbarProps) {
  const handleBulkAction = (action: 'archive' | 'delete' | 'export') => {
    onBulkAction?.(action)
  }

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        {selectedCount > 0 ? (
          <>
            <div className="text-sm text-muted-foreground">
              {selectedCount} categor{selectedCount > 1 ? 'ies' : 'y'} selected
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <MoreHorizontal className="mr-2 h-4 w-4" />
                  Bulk actions
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem
                  onClick={() => handleBulkAction('archive')}
                >
                  <Archive className="mr-2 h-4 w-4" />
                  Archive
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => handleBulkAction('export')}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => handleBulkAction('delete')}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        ) : (
          <div className="text-sm text-muted-foreground">
            Select categories to perform bulk actions
          </div>
        )}
      </div>

      <Button onClick={onAddCategory}>
        Add category
      </Button>
    </div>
  )
}