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
import { Check, ChevronsUpDown, FolderPlus, FolderMinus, MoreHorizontal, Edit, Copy, Trash2, Eye } from 'lucide-react'
import { useMutation, useQuery } from '@apollo/client/react'
import { AddProductsToCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/addProductsToCategory.generated'
import { RemoveProductsFromCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/removeProductsFromCategory.generated'
import { CategoriesDocument } from '@/services/graphql/admin-store/queries/categories/__generated__/categories.generated'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface Product {
  id: string
  name: string
  status: 'published' | 'archived'
}

interface ProductRowActionsProps {
  product: Product
  onEdit?: (productId: string) => void
  onDuplicate?: (productId: string) => void
  onDelete?: (productId: string) => void
  onView?: (productId: string) => void
  onCategoryUpdate?: () => void
}

export function ProductRowActions({
  product,
  onEdit,
  onDuplicate,
  onDelete,
  onView,
  onCategoryUpdate,
}: ProductRowActionsProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
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

  const handleEdit = () => {
    onEdit?.(product.id)
  }

  const handleDuplicate = () => {
    onDuplicate?.(product.id)
  }

  const handleDelete = () => {
    setShowDeleteDialog(true)
  }

  const handleView = () => {
    onView?.(product.id)
  }

  const confirmDelete = () => {
    onDelete?.(product.id)
    setShowDeleteDialog(false)
  }

  const handleAddToCategory = () => {
    setShowAddCategoryDialog(true)
  }

  const handleRemoveFromCategory = () => {
    setShowRemoveCategoryDialog(true)
  }

  const confirmAddToCategory = async () => {
    if (!selectedCategory) {
      toast.error('Please select a category')
      return
    }

    try {
      const { data } = await addProductsToCategory({
        variables: {
          categoryId: selectedCategory,
          productIds: [product.id]
        }
      })

      if (data?.addProductsToCategory?.success) {
        toast.success(`Product added to category`)
        setShowAddCategoryDialog(false)
        setSelectedCategory('')
        onCategoryUpdate?.()
      } else {
        toast.error(data?.addProductsToCategory?.error || 'Failed to add product to category')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to add product to category')
      console.error('Add to category error:', err)
    }
  }

  const confirmRemoveFromCategory = async () => {
    if (!selectedCategory) {
      toast.error('Please select a category')
      return
    }

    try {
      const { data } = await removeProductsFromCategory({
        variables: {
          categoryId: selectedCategory,
          productIds: [product.id]
        }
      })

      if (data?.removeProductsFromCategory?.success) {
        toast.success(`Product removed from category`)
        setShowRemoveCategoryDialog(false)
        setSelectedCategory('')
        onCategoryUpdate?.()
      } else {
        toast.error(data?.removeProductsFromCategory?.error || 'Failed to remove product from category')
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to remove product from category')
      console.error('Remove from category error:', err)
    }
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={handleView}>
            <Eye className="mr-2 h-4 w-4" />
            View
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleEdit}>
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleDuplicate}>
            <Copy className="mr-2 h-4 w-4" />
            Duplicate
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleAddToCategory}>
            <FolderPlus className="mr-2 h-4 w-4" />
            Add to category
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleRemoveFromCategory}>
            <FolderMinus className="mr-2 h-4 w-4" />
            Remove from category
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={handleDelete}
            className="text-destructive focus:text-destructive"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Product</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{product.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add to Category Dialog */}
      <Dialog open={showAddCategoryDialog} onOpenChange={setShowAddCategoryDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add to Category</DialogTitle>
            <DialogDescription>
              Select a category to add "{product.name}" to.
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
            <Button onClick={confirmAddToCategory}>
              Add to Category
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove from Category Dialog */}
      <Dialog open={showRemoveCategoryDialog} onOpenChange={setShowRemoveCategoryDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from Category</DialogTitle>
            <DialogDescription>
              Select a category to remove "{product.name}" from.
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
            <Button onClick={confirmRemoveFromCategory}>
              Remove from Category
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}