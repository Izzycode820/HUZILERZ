'use client';

/**
 * Variant Editor Form (Right Panel)
 *
 * Shopify-style variant editor with collapsible sections
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Button } from '@/components/shadcn-ui/button';
import { Switch } from '@/components/shadcn-ui/switch';
import { Badge } from '@/components/shadcn-ui/badge';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/shadcn-ui/collapsible';
import { Package, Loader2, ChevronRight } from 'lucide-react';

interface VariantEditorFormProps {
  variant: any;
  optionNames: string[];
  productChargeTax?: boolean;
  onUpdate: (updateData: any) => Promise<void>;
  isSaving: boolean;
}

export function VariantEditorForm({
  variant,
  optionNames,
  productChargeTax,
  onUpdate,
  isSaving,
}: VariantEditorFormProps) {
  // Form state
  const [formData, setFormData] = useState({
    option1: variant?.option1 || '',
    option2: variant?.option2 || '',
    option3: variant?.option3 || '',
    price: variant?.price?.toString() || '',
    compareAtPrice: variant?.compareAtPrice?.toString() || '',
    costPrice: variant?.costPrice?.toString() || '',
    sku: variant?.sku || '',
    barcode: variant?.barcode || '',
    trackInventory: variant?.trackInventory ?? true,
  });

  const [showPriceDetails, setShowPriceDetails] = useState(false);
  const [showSkuDetails, setShowSkuDetails] = useState(false);

  const [inventoryData, setInventoryData] = useState<Record<string, { onhand: number; available: number }>>({});

  // Initialize inventory data
  useEffect(() => {
    if (variant?.inventory) {
      const invData: Record<string, { onhand: number; available: number }> = {};
      variant.inventory.forEach((inv: any) => {
        if (inv?.location?.id) {
          invData[inv.location.id] = {
            onhand: inv.onhand ?? inv.quantity ?? 0,
            available: inv.available ?? inv.quantity ?? 0,
          };
        }
      });
      setInventoryData(invData);
    }
  }, [variant]);

  // Reset form when variant changes
  useEffect(() => {
    setFormData({
      option1: variant?.option1 || '',
      option2: variant?.option2 || '',
      option3: variant?.option3 || '',
      price: variant?.price?.toString() || '',
      compareAtPrice: variant?.compareAtPrice?.toString() || '',
      costPrice: variant?.costPrice?.toString() || '',
      sku: variant?.sku || '',
      barcode: variant?.barcode || '',
      trackInventory: variant?.trackInventory ?? true,
    });
  }, [variant]);

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleInventoryChange = (locationId: string, field: 'onhand' | 'available', value: string) => {
    const numValue = parseInt(value) || 0;
    setInventoryData((prev) => ({
      ...prev,
      [locationId]: {
        ...prev[locationId],
        [field]: numValue,
      },
    }));
  };

  const handleSave = async () => {
    const updateData: any = {
      option1: formData.option1 || null,
      option2: formData.option2 || null,
      option3: formData.option3 || null,
      price: formData.price ? parseFloat(formData.price) : null,
      compareAtPrice: formData.compareAtPrice ? parseFloat(formData.compareAtPrice) : null,
      costPrice: formData.costPrice ? parseFloat(formData.costPrice) : null,
      sku: formData.sku || null,
      barcode: formData.barcode || null,
      trackInventory: formData.trackInventory,
    };

    if (formData.trackInventory && Object.keys(inventoryData).length > 0) {
      updateData.inventoryUpdates = Object.entries(inventoryData).map(([locationId, data]) => ({
        locationId,
        onhand: data.onhand,
        available: data.available,
      }));
    }

    await onUpdate(updateData);
  };

  const hasChanges = () => {
    return (
      formData.option1 !== (variant?.option1 || '') ||
      formData.option2 !== (variant?.option2 || '') ||
      formData.option3 !== (variant?.option3 || '') ||
      formData.price !== (variant?.price?.toString() || '') ||
      formData.compareAtPrice !== (variant?.compareAtPrice?.toString() || '') ||
      formData.costPrice !== (variant?.costPrice?.toString() || '') ||
      formData.sku !== (variant?.sku || '') ||
      formData.barcode !== (variant?.barcode || '') ||
      formData.trackInventory !== (variant?.trackInventory ?? true)
    );
  };

  const displayName = [formData.option1, formData.option2, formData.option3].filter(Boolean).join(' / ');

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 bg-muted rounded-lg overflow-hidden border flex-shrink-0">
            {variant?.featuredMedia?.thumbnailUrl || variant?.featuredMedia?.url ? (
              <img
                src={variant.featuredMedia.thumbnailUrl || variant.featuredMedia.url}
                alt={displayName}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Package className="h-7 w-7 text-muted-foreground" />
              </div>
            )}
          </div>

          <div>
            <h2 className="text-lg font-semibold">{displayName}</h2>
            {variant?.sku && (
              <p className="text-xs text-muted-foreground">SKU: {variant.sku}</p>
            )}
          </div>
        </div>

        <Button onClick={handleSave} disabled={!hasChanges() || isSaving} size="sm">
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save'
          )}
        </Button>
      </div>

      {/* Options */}
      {optionNames.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pb-4">
            {optionNames[0] && (
              <div className="space-y-1.5">
                <Label htmlFor="option1" className="text-sm">{optionNames[0]}</Label>
                <Input
                  id="option1"
                  value={formData.option1}
                  onChange={(e) => handleInputChange('option1', e.target.value)}
                  placeholder={optionNames[0]}
                  className="h-9"
                />
              </div>
            )}

            {optionNames[1] && (
              <div className="space-y-1.5">
                <Label htmlFor="option2" className="text-sm">{optionNames[1]}</Label>
                <Input
                  id="option2"
                  value={formData.option2}
                  onChange={(e) => handleInputChange('option2', e.target.value)}
                  placeholder={optionNames[1]}
                  className="h-9"
                />
              </div>
            )}

            {optionNames[2] && (
              <div className="space-y-1.5">
                <Label htmlFor="option3" className="text-sm">{optionNames[2]}</Label>
                <Input
                  id="option3"
                  value={formData.option3}
                  onChange={(e) => handleInputChange('option3', e.target.value)}
                  placeholder={optionNames[2]}
                  className="h-9"
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Pricing */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Price</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 pb-4">
          {/* Main Price */}
          <div className="space-y-1.5">
            <Label htmlFor="price" className="text-sm">Price</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-sm text-muted-foreground">
                FCFA
              </span>
              <Input
                id="price"
                type="number"
                value={formData.price}
                onChange={(e) => handleInputChange('price', e.target.value)}
                placeholder="0"
                className="h-9 pl-14"
              />
            </div>
          </div>

          {/* Collapsible - Compare at / Cost / Tax */}
          <Collapsible open={showPriceDetails} onOpenChange={setShowPriceDetails}>
            <CollapsibleTrigger className="w-full border rounded-md px-3 py-2 hover:bg-muted/30 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ChevronRight className={`h-4 w-4 transition-transform ${showPriceDetails ? 'rotate-90' : ''}`} />
                  <span className="text-sm">Compare at</span>
                  <span className="text-sm">Cost per item</span>
                  {productChargeTax !== undefined && <span className="text-sm">Charge tax</span>}
                </div>
                <div className="flex items-center gap-2">
                  {formData.compareAtPrice && (
                    <Badge variant="secondary" className="text-xs">
                      FCFA {parseFloat(formData.compareAtPrice).toFixed(2)}
                    </Badge>
                  )}
                  {formData.costPrice && (
                    <Badge variant="secondary" className="text-xs">
                      FCFA {parseFloat(formData.costPrice).toFixed(2)}
                    </Badge>
                  )}
                  {productChargeTax !== undefined && (
                    <Badge variant="outline" className="text-xs">
                      {productChargeTax ? 'Yes' : 'No'}
                    </Badge>
                  )}
                </div>
              </div>
            </CollapsibleTrigger>

            <CollapsibleContent>
              <div className="border border-t-0 rounded-b-md px-3 py-3 space-y-3 bg-muted/10">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="compareAtPrice" className="text-xs">Compare at price</Label>
                    <div className="relative">
                      <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground">
                        FCFA
                      </span>
                      <Input
                        id="compareAtPrice"
                        type="number"
                        value={formData.compareAtPrice}
                        onChange={(e) => handleInputChange('compareAtPrice', e.target.value)}
                        placeholder="0"
                        className="h-8 text-xs pl-12"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="costPrice" className="text-xs">Cost per item</Label>
                    <div className="relative">
                      <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground">
                        FCFA
                      </span>
                      <Input
                        id="costPrice"
                        type="number"
                        value={formData.costPrice}
                        onChange={(e) => handleInputChange('costPrice', e.target.value)}
                        placeholder="0"
                        className="h-8 text-xs pl-12"
                      />
                    </div>
                  </div>
                </div>

                {productChargeTax !== undefined && (
                  <div className="bg-background px-2 py-1.5 rounded text-xs text-muted-foreground">
                    Charge tax: <span className="font-medium">{productChargeTax ? 'Yes' : 'No'}</span> (Inherited from product)
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>

      {/* Inventory */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Inventory</CardTitle>
            <div className="flex items-center gap-2">
              <Label htmlFor="trackInventory" className="text-sm font-normal cursor-pointer">
                Inventory tracked
              </Label>
              <Switch
                id="trackInventory"
                checked={formData.trackInventory}
                onCheckedChange={(checked) => handleInputChange('trackInventory', checked)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="pb-4">
          {formData.trackInventory ? (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/30">
                  <tr className="border-b">
                    <th className="text-left p-2 text-xs font-medium">Locations</th>
                    <th className="text-center p-2 text-xs font-medium w-[90px]">Unavailable</th>
                    <th className="text-center p-2 text-xs font-medium w-[90px]">Committed</th>
                    <th className="text-center p-2 text-xs font-medium w-[90px]">Available</th>
                    <th className="text-center p-2 text-xs font-medium w-[90px]">On hand</th>
                  </tr>
                </thead>
                <tbody>
                  {variant?.inventory && variant.inventory.length > 0 ? (
                    variant.inventory.map((inv: any) => {
                      const locationId = inv?.location?.id;
                      const locationName = inv?.location?.name || 'Unknown';
                      const currentData = inventoryData[locationId] || {
                        onhand: inv?.onhand ?? inv?.quantity ?? 0,
                        available: inv?.available ?? inv?.quantity ?? 0,
                      };
                      const unavailable = currentData.onhand - currentData.available;
                      const committed = 0;

                      return (
                        <tr key={locationId} className="border-b last:border-b-0">
                          <td className="p-2 text-xs">{locationName}</td>
                          <td className="p-2 text-center text-xs text-muted-foreground">{unavailable}</td>
                          <td className="p-2 text-center text-xs text-muted-foreground">{committed}</td>
                          <td className="p-2 text-center">
                            <Input
                              type="number"
                              value={currentData.available}
                              onChange={(e) => handleInventoryChange(locationId, 'available', e.target.value)}
                              className="w-16 h-7 text-xs text-center mx-auto"
                              min="0"
                            />
                          </td>
                          <td className="p-2 text-center">
                            <Input
                              type="number"
                              value={currentData.onhand}
                              onChange={(e) => handleInventoryChange(locationId, 'onhand', e.target.value)}
                              className="w-16 h-7 text-xs text-center mx-auto"
                              min="0"
                            />
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="p-6 text-center text-xs text-muted-foreground">
                        No inventory locations found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Inventory tracking is disabled for this variant
            </p>
          )}
        </CardContent>
      </Card>

      {/* SKU & Barcode - Collapsible */}
      <Card>
        <CardContent className="p-0">
          <Collapsible open={showSkuDetails} onOpenChange={setShowSkuDetails}>
            <CollapsibleTrigger className="w-full border rounded-md px-3 py-2.5 hover:bg-muted/30 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ChevronRight className={`h-4 w-4 transition-transform ${showSkuDetails ? 'rotate-90' : ''}`} />
                  <span className="text-sm font-medium">SKU</span>
                  <span className="text-sm font-medium">Barcode</span>
                </div>
                <div className="flex items-center gap-2">
                  {formData.sku && <Badge variant="secondary" className="text-xs">{formData.sku}</Badge>}
                  {formData.barcode && <Badge variant="secondary" className="text-xs">{formData.barcode}</Badge>}
                </div>
              </div>
            </CollapsibleTrigger>

            <CollapsibleContent>
              <div className="border border-t-0 rounded-b-md px-3 py-3 space-y-3 bg-muted/10">
                <div className="space-y-1.5">
                  <Label htmlFor="sku" className="text-xs">SKU (Stock Keeping Unit)</Label>
                  <Input
                    id="sku"
                    value={formData.sku}
                    onChange={(e) => handleInputChange('sku', e.target.value)}
                    placeholder="SKU"
                    className="h-8 text-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="barcode" className="text-xs">Barcode (ISBN, UPC, GTIN, etc.)</Label>
                  <Input
                    id="barcode"
                    value={formData.barcode}
                    onChange={(e) => handleInputChange('barcode', e.target.value)}
                    placeholder="Barcode"
                    className="h-8 text-xs"
                  />
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>
    </div>
  );
}
