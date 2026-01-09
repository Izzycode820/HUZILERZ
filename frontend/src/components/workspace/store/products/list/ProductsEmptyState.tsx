'use client'

import { Button } from '@/components/shadcn-ui/button'
import { Package, Plus } from 'lucide-react'

interface ProductsEmptyStateProps {
  onAddProduct?: () => void
  hasFilters?: boolean
  onClearFilters?: () => void
}

export function ProductsEmptyState({
  onAddProduct,
  hasFilters = false,
  onClearFilters,
}: ProductsEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-muted p-6 mb-4">
        <Package className="h-12 w-12 text-muted-foreground" />
      </div>

      <h3 className="text-lg font-semibold mb-2">
        {hasFilters ? 'No products match your filters' : 'No products yet'}
      </h3>

      <p className="text-muted-foreground max-w-md mb-6">
        {hasFilters
          ? 'Try adjusting your search or filter criteria to find what you\'re looking for.'
          : 'Get started by creating your first product to showcase in your store.'
        }
      </p>

      <div className="flex gap-3">
        {hasFilters ? (
          <Button variant="outline" onClick={onClearFilters}>
            Clear filters
          </Button>
        ) : (
          <Button onClick={onAddProduct} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add your first product
          </Button>
        )}
      </div>
    </div>
  )
}