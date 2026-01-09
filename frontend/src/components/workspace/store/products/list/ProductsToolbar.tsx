'use client'

import { useState } from 'react'
import { Button } from '@/components/shadcn-ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/shadcn-ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/shadcn-ui/popover'
import { Check, ChevronsUpDown, Download, Archive, Trash2, MoreHorizontal, FolderPlus, FolderMinus } from 'lucide-react'
import { useMutation, useQuery } from '@apollo/client/react'
import { AddProductsToCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/addProductsToCategory.generated'
import { RemoveProductsFromCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/removeProductsFromCategory.generated'
import { CategoriesDocument } from '@/services/graphql/admin-store/queries/categories/__generated__/categories.generated'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface ProductsToolbarProps {
  selectedCount: number
  selectedProductIds?: string[]
  onBulkAction?: (action: 'archive' | 'delete' | 'export') => void
  onAddProduct?: () => void
  onCategoryUpdate?: () => void
}

export function ProductsToolbar({
  selectedCount,
  selectedProductIds = [],
  onBulkAction,
  onAddProduct,
  onCategoryUpdate,
}: ProductsToolbarProps) {
  const [showAddCategoryDialog, setShowAddCategoryDialog] = useState(false)
  const [showRemoveCategoryDialog, setShowRemoveCategoryDialog] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('')

  // GraphQL mutations
  const [addProductsToCategory] = useMutation(AddProductsToCategoryDocument)
  const [removeProductsFromCategory] = useMutation(RemoveProductsFromCategoryDocument)

  // Fetch categories
  const { data: categoriesData } = useQuery(CategoriesDocument, {
    variables: { first: 100, isVisible: true }
  })

  const categories = categoriesData?.categories?.edges?.map(edge => edge?.node).filter(Boolean) || []

  const handleBulkAction = (action: 'archive' | 'delete' | 'export') => {
    onBulkAction?.(action)
  }

  const handleBulkAddToCategory = () => {
    setShowAddCategoryDialog(true)
  }

  const handleBulkRemoveFromCategory = () => {
    setShowRemoveCategoryDialog(true)
  }

  const confirmBulkAddToCategory = async () => {
    if (!selectedCategory) {
      toast.error('Please select a category')
      return
    }

    if (selectedProductIds.length === 0) {
      toast.error('No products selected')
      return
    }

    try {
      const { data } = await addProductsToCategory({
        variables: {
          categoryId: selectedCategory,
          productIds: selectedProductIds
        }
      })

      if (data?.addProductsToCategory?.success) {
        toast.success(`${selectedProductIds.length} products added to category`)
        setShowAddCategoryDialog(false)
        setSelectedCategory('')
        onCategoryUpdate?.()
      } else {
        toast.error(data?.addProductsToCategory?.error || 'Failed to add products to category')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to add products to category')
      console.error('Bulk add to category error:', err)
    }
  }

  const confirmBulkRemoveFromCategory = async () => {
    if (!selectedCategory) {
      toast.error('Please select a category')
      return
    }

    if (selectedProductIds.length === 0) {
      toast.error('No products selected')
      return
    }

    try {
      const { data } = await removeProductsFromCategory({
        variables: {
          categoryId: selectedCategory,
          productIds: selectedProductIds
        }
      })

      if (data?.removeProductsFromCategory?.success) {
        toast.success(`${selectedProductIds.length} products removed from category`)
        setShowRemoveCategoryDialog(false)
        setSelectedCategory('')
        onCategoryUpdate?.()
      } else {
        toast.error(data?.removeProductsFromCategory?.error || 'Failed to remove products from category')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to remove products from category')
      console.error('Bulk remove from category error:', err)
    }
  }

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        {selectedCount > 0 ? (
          <>
            <div className="text-sm text-muted-foreground">
              {selectedCount} product{selectedCount > 1 ? 's' : ''} selected
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
                  onClick={handleBulkAddToCategory}
                >
                  <FolderPlus className="mr-2 h-4 w-4" />
                  Add to category
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={handleBulkRemoveFromCategory}
                >
                  <FolderMinus className="mr-2 h-4 w-4" />
                  Remove from category
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
            Select products to perform bulk actions
          </div>
        )}
      </div>

      <Button onClick={onAddProduct}>
        Add product
      </Button>

      {/* Bulk Add to Category Dialog */}
      <Dialog open={showAddCategoryDialog} onOpenChange={setShowAddCategoryDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add to Category</DialogTitle>
            <DialogDescription>
              Select a category to add {selectedProductIds.length} selected products to.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  className="w-full justify-between"
                >
                  {selectedCategory
                    ? categories.find((category) => category?.id === selectedCategory)?.name
                    : "Select category..."}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-full p-0">
                <Command>
                  <CommandInput placeholder="Search categories..." />
                  <CommandList>
                    <CommandEmpty>No category found.</CommandEmpty>
                    <CommandGroup>
                      {categories.map((category) => (
                        <CommandItem
                          key={category?.id}
                          value={category?.id || ''}
                          onSelect={() => setSelectedCategory(category?.id || '')}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              selectedCategory === category?.id ? "opacity-100" : "opacity-0"
                            )}
                          />
                          {category?.name}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAddCategoryDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={confirmBulkAddToCategory}>
              Add to Category
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Remove from Category Dialog */}
      <Dialog open={showRemoveCategoryDialog} onOpenChange={setShowRemoveCategoryDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from Category</DialogTitle>
            <DialogDescription>
              Select a category to remove {selectedProductIds.length} selected products from.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  className="w-full justify-between"
                >
                  {selectedCategory
                    ? categories.find((category) => category?.id === selectedCategory)?.name
                    : "Select category..."}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-full p-0">
                <Command>
                  <CommandInput placeholder="Search categories..." />
                  <CommandList>
                    <CommandEmpty>No category found.</CommandEmpty>
                    <CommandGroup>
                      {categories.map((category) => (
                        <CommandItem
                          key={category?.id}
                          value={category?.id || ''}
                          onSelect={() => setSelectedCategory(category?.id || '')}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              selectedCategory === category?.id ? "opacity-100" : "opacity-0"
                            )}
                          />
                          {category?.name}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRemoveCategoryDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={confirmBulkRemoveFromCategory}>
              Remove from Category
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}