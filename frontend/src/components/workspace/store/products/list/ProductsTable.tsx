'use client'

import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table'
import { Badge } from '@/components/shadcn-ui/badge'
import { Checkbox } from '@/components/shadcn-ui/checkbox'
import { Button } from '@/components/shadcn-ui/button'
import { ProductRowActions } from './ProductRowActions'

interface Product {
  id: string
  name: string
  status: 'published' | 'archived'
  price: number
  inventory: number
  category: string
  type: string
  vendor: string
  featuredMedia?: {
    thumbnailUrl?: string
    url?: string
  }
}

interface ProductsTableProps {
  products: Product[]
  onProductSelect?: (selectedIds: string[]) => void
  onEdit?: (productId: string) => void
  onView?: (productId: string) => void
  onDuplicate?: (productId: string) => void
  onDelete?: (productId: string) => void
  onCategoryUpdate?: () => void
}

export function ProductsTable({
  products,
  onProductSelect,
  onEdit,
  onView,
  onDuplicate,
  onDelete,
  onCategoryUpdate
}: ProductsTableProps) {
  const [selectedProducts, setSelectedProducts] = useState<string[]>([])

  const handleSelectAll = (checked: boolean) => {
    const newSelected = checked ? products.map(p => p.id) : []
    setSelectedProducts(newSelected)
    onProductSelect?.(newSelected)
  }

  const handleSelectProduct = (productId: string, checked: boolean) => {
    const newSelected = checked
      ? [...selectedProducts, productId]
      : selectedProducts.filter(id => id !== productId)
    setSelectedProducts(newSelected)
    onProductSelect?.(newSelected)
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      published: 'bg-green-100 text-green-800 border-green-200',
      archived: 'bg-gray-100 text-gray-800 border-gray-200',
    }
    return (
      <Badge variant="outline" className={variants[status as keyof typeof variants]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    )
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-CM', {
      style: 'currency',
      currency: 'XAF',
    }).format(price)
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={selectedProducts.length === products.length && products.length > 0}
                onCheckedChange={handleSelectAll}
                aria-label="Select all"
              />
            </TableHead>
            <TableHead>Product</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Inventory</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Vendor</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {products.map((product) => (
            <TableRow key={product.id}>
              <TableCell>
                <Checkbox
                  checked={selectedProducts.includes(product.id)}
                  onCheckedChange={(checked) => handleSelectProduct(product.id, checked as boolean)}
                  aria-label={`Select ${product.name}`}
                />
              </TableCell>
              <TableCell className="font-medium">
                <div className="flex items-center gap-3">
                  {product.featuredMedia?.thumbnailUrl || product.featuredMedia?.url ? (
                    <img
                      src={product.featuredMedia.thumbnailUrl || product.featuredMedia.url}
                      alt={product.name}
                      className="h-10 w-10 rounded-md object-cover border"
                    />
                  ) : (
                    <div className="h-10 w-10 rounded-md bg-muted flex items-center justify-center border">
                      <span className="text-xs text-muted-foreground">No image</span>
                    </div>
                  )}
                  <div>
                    <div className="font-medium">{product.name}</div>
                  </div>
                </div>
              </TableCell>
              <TableCell>{getStatusBadge(product.status)}</TableCell>
              <TableCell>
                <div className="text-sm">
                  {product.inventory} in stock
                </div>
              </TableCell>
              <TableCell className="font-medium">
                {formatPrice(product.price)}
              </TableCell>
              <TableCell>
                <div className="text-sm">{product.category}</div>
              </TableCell>
              <TableCell>
                <div className="text-sm">{product.type}</div>
              </TableCell>
              <TableCell>
                <div className="text-sm">{product.vendor}</div>
              </TableCell>
              <TableCell>
                <ProductRowActions
                  product={product}
                  onEdit={onEdit}
                  onView={onView}
                  onDuplicate={onDuplicate}
                  onDelete={onDelete}
                  onCategoryUpdate={onCategoryUpdate}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}