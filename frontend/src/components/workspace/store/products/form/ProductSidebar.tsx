'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Label } from '@/components/shadcn-ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select'

interface ProductSidebarProps {
  status: 'draft' | 'published'
  onStatusChange: (status: 'draft' | 'published') => void
}

export function ProductSidebar({
  status,
  onStatusChange,
}: ProductSidebarProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Product Status */}
        <div className="space-y-2">
          <Label htmlFor="status">Product Status</Label>
          <Select value={status} onValueChange={onStatusChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="published">Published</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Product Availability */}
        <div className="space-y-2">
          <Label>Product Availability</Label>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="online-store"
                defaultChecked
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <Label htmlFor="online-store" className="text-sm font-normal">
                Online store
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="pos"
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <Label htmlFor="pos" className="text-sm font-normal">
                Point of Sale (POS)
              </Label>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
