'use client'

import { Badge } from '@/components/shadcn-ui/badge'
import { Button } from '@/components/shadcn-ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu'
import { MoreHorizontal, Eye, EyeOff, Edit, Trash } from 'lucide-react'

interface Category {
  id: string
  name: string
  isVisible: boolean
  isFeatured: boolean
  productCount: number
  featuredMedia?: {
    id: string
    url?: string | null
    thumbnailUrl?: string | null
    optimizedUrl?: string | null
    width?: number | null
    height?: number | null
  }
}

interface CategoriesTableProps {
  categories: Category[]
  onEdit?: (categoryId: string) => void
  onView?: (categoryId: string) => void
  onToggleVisibility?: (categoryId: string) => void
  onDelete?: (categoryId: string) => void
}

export function CategoriesTable({
  categories,
  onEdit,
  onView,
  onToggleVisibility,
  onDelete,
}: CategoriesTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-20"></TableHead>
            <TableHead className="w-96">Category</TableHead>
            <TableHead className="text-center">Products</TableHead>
            <TableHead className="text-center">Status</TableHead>
            <TableHead className="text-center">Featured</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {categories.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-8 text-muted-foreground text-sm">
                No categories found
              </TableCell>
            </TableRow>
          ) : (
            categories.map((category) => (
              <TableRow key={category.id}>
                {/* Thumbnail */}
                <TableCell>
                  {category.featuredMedia?.thumbnailUrl || category.featuredMedia?.url ? (
                    <img
                      src={category.featuredMedia.thumbnailUrl || category.featuredMedia.url || undefined}
                      alt={category.name}
                      className="h-16 w-16 rounded-md object-cover border"
                    />
                  ) : (
                    <div className="h-16 w-16 rounded-md bg-muted flex items-center justify-center border">
                      <span className="text-xs text-muted-foreground">No img</span>
                    </div>
                  )}
                </TableCell>

                {/* Name */}
                <TableCell className="font-medium">
                  <button
                    onClick={() => onView?.(category.id)}
                    className="hover:underline text-left"
                  >
                    {category.name}
                  </button>
                </TableCell>

                {/* Product Count */}
                <TableCell className="text-center text-sm">
                  {category.productCount}
                </TableCell>

                {/* Status */}
                <TableCell className="text-center">
                  {category.isVisible ? (
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      Visible
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
                      Hidden
                    </Badge>
                  )}
                </TableCell>

                {/* Featured */}
                <TableCell className="text-center">
                  {category.isFeatured && (
                    <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                      Featured
                    </Badge>
                  )}
                </TableCell>

                {/* Actions */}
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onEdit?.(category.id)}>
                        <Edit className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onToggleVisibility?.(category.id)}>
                        {category.isVisible ? (
                          <>
                            <EyeOff className="mr-2 h-4 w-4" />
                            Hide
                          </>
                        ) : (
                          <>
                            <Eye className="mr-2 h-4 w-4" />
                            Show
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onDelete?.(category.id)}
                        className="text-destructive"
                      >
                        <Trash className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}
