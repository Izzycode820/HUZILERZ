'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog'
import { Button } from '@/components/shadcn-ui/button'
import { Input } from '@/components/shadcn-ui/input'
import { Label } from '@/components/shadcn-ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/shadcn-ui/select'
import { Checkbox } from '@/components/shadcn-ui/checkbox'
import { Plus } from 'lucide-react'

interface CreatePackageModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (packageData: any) => void
  loading: boolean
}

export function CreatePackageModal({
  open,
  onOpenChange,
  onSubmit,
  loading,
}: CreatePackageModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    packageType: 'box',
    size: 'small',
    weight: '',
    method: '',
    regionFees: [{ region: '', fee: '' }],
    estimatedDays: '',
    useAsDefault: false,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Convert regionFees array to JSON object format
    const regionFeesObject: Record<string, number> = {}
    formData.regionFees.forEach(({ region, fee }) => {
      if (region && fee) {
        regionFeesObject[region] = parseFloat(fee)
      }
    })

    onSubmit({
      ...formData,
      weight: formData.weight ? parseFloat(formData.weight) : null,
      regionFees: JSON.stringify(regionFeesObject),
      estimatedDays: formData.estimatedDays || '3-5',
    })
  }

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleRegionFeeChange = (index: number, field: 'region' | 'fee', value: string) => {
    setFormData(prev => ({
      ...prev,
      regionFees: prev.regionFees.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      )
    }))
  }

  const addRegionFee = () => {
    setFormData(prev => ({
      ...prev,
      regionFees: [...prev.regionFees, { region: '', fee: '' }]
    }))
  }

  const removeRegionFee = (index: number) => {
    setFormData(prev => ({
      ...prev,
      regionFees: prev.regionFees.filter((_, i) => i !== index)
    }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create New Package</DialogTitle>
          <DialogDescription>
            Add a new shipping package to use for this product.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Package Name</Label>
            <Input
              id="name"
              placeholder="e.g., Standard Box"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="packageType">Package Type</Label>
              <Select value={formData.packageType} onValueChange={(value) => handleChange('packageType', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="box">Box</SelectItem>
                  <SelectItem value="envelope">Envelope</SelectItem>
                  <SelectItem value="soft_package">Soft Package</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="size">Size</Label>
              <Select value={formData.size} onValueChange={(value) => handleChange('size', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="small">Small</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="large">Large</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="weight">Weight (kg)</Label>
            <Input
              id="weight"
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              value={formData.weight}
              onChange={(e) => handleChange('weight', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="method">Shipping Method</Label>
            <Input
              id="method"
              placeholder="e.g., Standard, Express"
              value={formData.method}
              onChange={(e) => handleChange('method', e.target.value)}
              required
            />
          </div>

          {/* Region Fees Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Region & Fees</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addRegionFee}
                className="h-7 px-2 text-xs"
              >
                <Plus className="h-3 w-3 mr-1" />
                Add Region
              </Button>
            </div>

            {formData.regionFees.map((regionFee, index) => (
              <div key={index} className="grid grid-cols-2 gap-2 items-end">
                <div className="space-y-1">
                  <Label htmlFor={`region-${index}`} className="text-xs">
                    Region {index + 1}
                  </Label>
                  <Input
                    id={`region-${index}`}
                    placeholder="e.g., Yaounde, Douala"
                    value={regionFee.region}
                    onChange={(e) => handleRegionFeeChange(index, 'region', e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor={`fee-${index}`} className="text-xs">
                    Fee (FCFA)
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      id={`fee-${index}`}
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={regionFee.fee}
                      onChange={(e) => handleRegionFeeChange(index, 'fee', e.target.value)}
                      required
                    />
                    {formData.regionFees.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeRegionFee(index)}
                        className="h-9 px-2 text-red-500 hover:text-red-700"
                      >
                        ×
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <p className="text-xs text-muted-foreground">
              Add multiple regions with their respective shipping fees
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="estimatedDays">Est. Days</Label>
            <Input
              id="estimatedDays"
              placeholder="3-5"
              value={formData.estimatedDays}
              onChange={(e) => handleChange('estimatedDays', e.target.value)}
              required
            />
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="useAsDefault"
              checked={formData.useAsDefault}
              onCheckedChange={(checked) => handleChange('useAsDefault', checked)}
            />
            <Label htmlFor="useAsDefault" className="text-sm">
              Use as default package
            </Label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create Package'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}