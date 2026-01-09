'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Textarea } from '@/components/shadcn-ui/textarea'
import { Label } from '@/components/shadcn-ui/label'

interface CategoryTitleSectionProps {
  name: string
  description: string
  onNameChange: (name: string) => void
  onDescriptionChange: (description: string) => void
}

export function CategoryTitleSection({
  name,
  description,
  onNameChange,
  onDescriptionChange,
}: CategoryTitleSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="category-name">Category Name *</Label>
          <Input
            id="category-name"
            placeholder="Enter category name"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="category-description">Description</Label>
          <Textarea
            id="category-description"
            placeholder="Describe this category..."
            value={description}
            onChange={(e) => onDescriptionChange(e.target.value)}
            rows={6}
          />
          <p className="text-sm text-muted-foreground">
            Customers will see this on your category page.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}