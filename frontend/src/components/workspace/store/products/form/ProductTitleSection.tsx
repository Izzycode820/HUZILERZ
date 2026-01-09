'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Textarea } from '@/components/shadcn-ui/textarea'
import { Label } from '@/components/shadcn-ui/label'

interface ProductTitleSectionProps {
  name: string
  description: string
  onNameChange: (name: string) => void
  onDescriptionChange: (description: string) => void
}

export function ProductTitleSection({
  name,
  description,
  onNameChange,
  onDescriptionChange,
}: ProductTitleSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Product Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="product-name">Product Name *</Label>
          <Input
            id="product-name"
            placeholder="Enter product name"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="product-description">Description</Label>
          <Textarea
            id="product-description"
            placeholder="Describe your product..."
            value={description}
            onChange={(e) => onDescriptionChange(e.target.value)}
            rows={6}
          />
          <p className="text-sm text-muted-foreground">
            Customers will see this on your product page.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}