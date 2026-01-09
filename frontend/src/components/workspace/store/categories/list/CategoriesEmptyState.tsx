'use client'

import { Card, CardContent } from '@/components/shadcn-ui/card'
import { Button } from '@/components/shadcn-ui/button'
import { Package, Plus } from 'lucide-react'

interface CategoriesEmptyStateProps {
  onAddCategory?: () => void
}

export function CategoriesEmptyState({
  onAddCategory,
}: CategoriesEmptyStateProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-center py-12">
          <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
            <Package className="h-8 w-8 text-muted-foreground" />
          </div>

          <h3 className="text-lg font-semibold mb-2">No categories yet</h3>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            Create your first category to organize your products and make them easier to find for your customers.
          </p>

          <Button onClick={onAddCategory} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create your first category
          </Button>

          <div className="mt-8 text-sm text-muted-foreground max-w-lg mx-auto space-y-2">
            <p><strong>Why create categories?</strong></p>
            <ul className="text-left space-y-1">
              <li>• Organize products for better customer navigation</li>
              <li>• Create featured collections for your homepage</li>
              <li>• Improve SEO with structured product organization</li>
              <li>• Make bulk product management easier</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}