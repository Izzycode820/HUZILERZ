'use client'

/**
 * Category Products Section
 *
 * Features:
 * - Search input with Browse button
 * - Sort dropdown
 * - Multi-select products via ProductSearchModal (collection mode)
 * - Display numbered list of selected products
 * - Remove products from selection
 */

import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Button } from '@/components/shadcn-ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select'
import { ProductSearchModal } from '../../../shared/products/ProductSearchModal'
import { useQuery } from '@apollo/client/react'
import { GetProductsPickerDocument } from '@/services/graphql/admin-store/queries/products/__generated__/GetProductsPicker.generated'
import type { CategoryProductsSectionProps, SortOption } from './types'
import { SORT_OPTIONS } from './types'

export function CategoryProductsSection({
  selectedProductIds,
  onProductsChange,
  errors,
}: CategoryProductsSectionProps) {
  const [searchModalOpen, setSearchModalOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<SortOption>('best-selling')

  // Fetch product details for selected IDs
  const { data } = useQuery(GetProductsPickerDocument, {
    variables: {
      first: 100,
    },
    skip: selectedProductIds.length === 0,
  })

  // Filter to get only selected products
  const selectedProducts = data?.products?.edges
    ?.map(edge => edge?.node)
    .filter((node): node is NonNullable<typeof node> =>
      node != null && selectedProductIds.includes(node.id)
    ) || []

  const handleRemoveProduct = (productId: string) => {
    onProductsChange(selectedProductIds.filter(id => id !== productId))
  }

  const handleAddProducts = (newProductIds: string[]) => {
    // Merge existing and new IDs, removing duplicates
    const mergedIds = Array.from(new Set([...selectedProductIds, ...newProductIds]))
    onProductsChange(mergedIds)
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Products</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search, Browse, Sort Controls */}
          <div className="flex items-center gap-2">
            {/* Search Input */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search products"
                value={searchTerm}
                onChange={(e) => {
                  const value = e.target.value;
                  setSearchTerm(value);
                  // Only open modal when user starts typing
                  if (value.length > 0) {
                    setSearchModalOpen(true);
                  }
                }}
                className="pl-9"
              />
            </div>

            {/* Browse Button */}
            <Button
              variant="outline"
              onClick={() => setSearchModalOpen(true)}
            >
              Browse
            </Button>

            {/* Sort Dropdown */}
            <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Selected Products List */}
          {selectedProducts.length > 0 ? (
            <div className="space-y-2">
              {selectedProducts.map((product, index) => (
                <div
                  key={product.id}
                  className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/30 transition-colors"
                >
                  {/* Number */}
                  <span className="text-sm font-medium text-muted-foreground w-6">
                    {index + 1}.
                  </span>

                  {/* Product Image */}
                  <div className="flex-shrink-0 w-10 h-10 bg-muted rounded overflow-hidden">
                    {product.mediaGallery?.[0]?.thumbnailUrl ? (
                      <img
                        src={product.mediaGallery[0].thumbnailUrl}
                        alt={product.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-muted" />
                    )}
                  </div>

                  {/* Product Name */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{product.name}</p>
                  </div>

                  {/* Active Badge */}
                  <div className="px-2.5 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                    Active
                  </div>

                  {/* Remove Button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 flex-shrink-0"
                    onClick={() => handleRemoveProduct(product.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-muted-foreground border rounded-lg">
              No products selected
            </div>
          )}

          {errors?.products && (
            <p className="text-sm text-red-500">{errors.products}</p>
          )}
        </CardContent>
      </Card>

      {/* Product Search Modal - Collection Mode */}
      <ProductSearchModal
        mode="collection"
        open={searchModalOpen}
        onOpenChange={setSearchModalOpen}
        selectedProductIds={selectedProductIds}
        onAddProducts={handleAddProducts}
      />
    </>
  )
}
