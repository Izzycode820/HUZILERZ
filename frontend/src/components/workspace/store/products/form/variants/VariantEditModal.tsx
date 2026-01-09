/**
 * VariantEditModal Component
 * Deep edit modal for variant with all hidden fields
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Button } from '@/components/shadcn-ui/button';
import { Switch } from '@/components/shadcn-ui/switch';
import type { VariantFormState } from './types';

interface VariantEditModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  variant: VariantFormState;
  onSave: (updatedVariant: VariantFormState) => void;
}

export function VariantEditModal({
  open,
  onOpenChange,
  variant,
  onSave
}: VariantEditModalProps) {
  const [formData, setFormData] = useState<VariantFormState>(variant);

  const handleSave = () => {
    onSave(formData);
    onOpenChange(false);
  };

  const variantName = [formData.option1, formData.option2, formData.option3]
    .filter(Boolean)
    .join(' / ');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Variant: {variantName}</DialogTitle>
          <DialogDescription>
            Update pricing, inventory, and other details for this variant
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Pricing Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Pricing</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="price">Price (FCFA)</Label>
                <Input
                  id="price"
                  type="number"
                  value={formData.price || ''}
                  onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || undefined })}
                />
              </div>

              <div>
                <Label htmlFor="compareAtPrice">Compare at price</Label>
                <Input
                  id="compareAtPrice"
                  type="number"
                  value={formData.compareAtPrice || ''}
                  onChange={(e) => setFormData({ ...formData, compareAtPrice: parseFloat(e.target.value) || undefined })}
                />
              </div>

              <div>
                <Label htmlFor="costPrice">Cost per item</Label>
                <Input
                  id="costPrice"
                  type="number"
                  value={formData.costPrice || ''}
                  onChange={(e) => setFormData({ ...formData, costPrice: parseFloat(e.target.value) || undefined })}
                />
              </div>
            </div>
          </div>

          {/* Inventory Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Inventory</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="sku">SKU</Label>
                <Input
                  id="sku"
                  value={(formData as any).sku || ''}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value } as any)}
                  placeholder="SKU-001"
                />
              </div>

              <div>
                <Label htmlFor="barcode">Barcode</Label>
                <Input
                  id="barcode"
                  value={(formData as any).barcode || ''}
                  onChange={(e) => setFormData({ ...formData, barcode: e.target.value } as any)}
                  placeholder="123456789"
                />
              </div>

              <div>
                <Label htmlFor="inventoryQuantity">Quantity</Label>
                <Input
                  id="inventoryQuantity"
                  type="number"
                  value={formData.inventoryQuantity || 0}
                  onChange={(e) => setFormData({ ...formData, inventoryQuantity: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Status</h3>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="isActive">Active</Label>
                <p className="text-sm text-muted-foreground">
                  Allow customers to purchase this variant
                </p>
              </div>
              <Switch
                id="isActive"
                checked={formData.isActive}
                onCheckedChange={(checked) => setFormData({ ...formData, isActive: checked })}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save changes
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
