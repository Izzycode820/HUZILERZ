'use client'

/**
 * CategorySidebar Component
 *
 * Clean sidebar matching Shopify design
 * - Publishing: Visibility and Featured toggles
 * - Organization: Sort order for category positioning
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Label } from '@/components/shadcn-ui/label'
import { Switch } from '@/components/shadcn-ui/switch'

interface CategorySidebarProps {
  isVisible: boolean
  isFeatured: boolean
  sortOrder: number
  onIsVisibleChange: (isVisible: boolean) => void
  onIsFeaturedChange: (isFeatured: boolean) => void
  onSortOrderChange: (sortOrder: number) => void
}

export function CategorySidebar({
  isVisible,
  isFeatured,
  sortOrder,
  onIsVisibleChange,
  onIsFeaturedChange,
  onSortOrderChange,
}: CategorySidebarProps) {
  return (
    <>
      {/* Publishing */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Publishing</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="sidebar-visible">Visible</Label>
              <p className="text-xs text-muted-foreground">
                Show on store
              </p>
            </div>
            <Switch
              id="sidebar-visible"
              checked={isVisible}
              onCheckedChange={onIsVisibleChange}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="sidebar-featured">Featured</Label>
              <p className="text-xs text-muted-foreground">
                Show on homepage
              </p>
            </div>
            <Switch
              id="sidebar-featured"
              checked={isFeatured}
              onCheckedChange={onIsFeaturedChange}
            />
          </div>
        </CardContent>
      </Card>

      {/* Organization */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Organization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="sidebar-sort-order">Sort Order</Label>
            <Input
              id="sidebar-sort-order"
              type="number"
              placeholder="0"
              value={sortOrder}
              onChange={(e) => onSortOrderChange(Number(e.target.value))}
              min="0"
              max="999"
            />
            <p className="text-xs text-muted-foreground">
              Lower numbers appear first
            </p>
          </div>
        </CardContent>
      </Card>
    </>
  )
}