'use client'

import { Card, CardContent } from '@/components/shadcn-ui/card'
import { Button } from '@/components/shadcn-ui/button'
import { Badge } from '@/components/shadcn-ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu'
import { Eye, EyeOff, Edit, MoreHorizontal, Trash2, Package } from 'lucide-react'

interface Category {
  id: string
  name: string
  description: string
  slug: string
  isVisible: boolean
  isFeatured: boolean
  sortOrder: number
  productCount: number | null
  featuredMedia?: {
    id: string
    url: string
    thumbnailUrl?: string
    optimizedUrl?: string
    width: number | null
    height: number | null
  }
  createdAt: string
  updatedAt: string
}

interface CategoriesGridProps {
  categories: Category[]
  onEdit?: (categoryId: string) => void
  onView?: (categoryId: string) => void
  onToggleVisibility?: (categoryId: string) => void
  onDelete?: (categoryId: string) => void
}

export function CategoriesGrid({
  categories,
  onEdit,
  onView,
  onToggleVisibility,
  onDelete,
}: CategoriesGridProps) {
  const handleEdit = (categoryId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onEdit?.(categoryId)
  }

  const handleToggleVisibility = (categoryId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onToggleVisibility?.(categoryId)
  }

  const handleDelete = (categoryId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onDelete?.(categoryId)
  }

  const handleView = (categoryId: string) => {
    onView?.(categoryId)
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {categories.map((category) => (
        <Card
          key={category.id}
          className="group cursor-pointer hover:shadow-lg transition-all duration-200 overflow-hidden"
          onClick={() => handleView(category.id)}
        >
          {/* Category Image */}
          <div className="relative aspect-[4/3] bg-muted overflow-hidden">
            {category.featuredMedia ? (
              <img
                src={category.featuredMedia.thumbnailUrl || category.featuredMedia.url}
                alt={category.name}
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted/50 to-muted">
                <Package className="h-12 w-12 text-muted-foreground/50" />
              </div>
            )}

            {/* Status Badges */}
            <div className="absolute top-3 left-3 flex flex-col gap-1">
              {!category.isVisible && (
                <Badge variant="secondary" className="bg-destructive/90 text-destructive-foreground">
                  <EyeOff className="h-3 w-3 mr-1" />
                  Hidden
                </Badge>
              )}
              {category.isFeatured && (
                <Badge variant="secondary" className="bg-yellow-500/90 text-yellow-900">
                  Featured
                </Badge>
              )}
            </div>

            {/* Product Count */}
            <div className="absolute top-3 right-3">
              <Badge variant="secondary" className="bg-background/90 backdrop-blur-sm">
                <Package className="h-3 w-3 mr-1" />
                {category.productCount || 0}
              </Badge>
            </div>

            {/* Action Menu */}
            <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 w-8 p-0 bg-background/90 backdrop-blur-sm"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={(e) => handleEdit(category.id, e)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={(e) => handleToggleVisibility(category.id, e)}>
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
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={(e) => handleDelete(category.id, e)}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Category Info */}
          <CardContent className="p-4">
            <div className="space-y-2">
              <h3 className="font-semibold text-lg leading-tight line-clamp-2">
                {category.name}
              </h3>

              {category.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {category.description}
                </p>
              )}

              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  {category.productCount} product{category.productCount !== 1 ? 's' : ''}
                </span>
                <span>
                  Order: {category.sortOrder}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}