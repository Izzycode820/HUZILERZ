'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Label } from '@/components/shadcn-ui/label';
import { Input } from '@/components/shadcn-ui/input';
import { Button } from '@/components/shadcn-ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/shadcn-ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select';
import { Search, X } from 'lucide-react';
import { MinimumRequirementsSection } from '../shared/MinimumRequirementsSection';
import { MaximumUsesSection } from '../shared/MaximumUsesSection';
import { CombinationsSection } from '../shared/CombinationsSection';
import { ActiveDatesSection } from '../shared/ActiveDatesSection';
import { ProductSearchModal } from '../../../shared/products/ProductSearchModal';
import { CollectionSearchModal } from '../../../shared/collections/CollectionSearchModal';
import * as Types from '@/types/workspace/store/graphql-base';

export interface AmountOffProductFormData {
  code: string;
  name?: string;
  method: Types.WorkspaceStoreDiscountMethodChoices;
  discountValueType: Types.WorkspaceStoreDiscountDiscountValueTypeChoices;
  value?: number;
  appliesToAllProducts: boolean;
  productIds?: string[];
  categoryIds?: string[];
  startsAt: string;
  endsAt?: string;
  minimumRequirementType: Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices;
  minimumPurchaseAmount?: number;
  minimumQuantityItems?: number;
  limitTotalUses: boolean;
  usageLimit?: number;
  limitOnePerCustomer: boolean;
  canCombineWithProductDiscounts: boolean;
  canCombineWithOrderDiscounts: boolean;
  appliesToAllCustomers: boolean;
}

interface AmountOffProductFormProps {
  onSubmit: (data: AmountOffProductFormData) => void;
  onDiscard: () => void;
  isLoading?: boolean;
}

export function AmountOffProductForm({ onSubmit, onDiscard, isLoading }: AmountOffProductFormProps) {
  const [formData, setFormData] = useState<AmountOffProductFormData>({
    code: '',
    method: Types.WorkspaceStoreDiscountMethodChoices.DiscountCode,
    discountValueType: Types.WorkspaceStoreDiscountDiscountValueTypeChoices.Percentage,
    appliesToAllProducts: false, // Default to specific logic as requested
    startsAt: new Date().toISOString(),
    minimumRequirementType: Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices.None,
    limitTotalUses: false,
    limitOnePerCustomer: false,
    canCombineWithProductDiscounts: false,
    canCombineWithOrderDiscounts: false,
    appliesToAllCustomers: true,
    productIds: [],
    categoryIds: [],
  });

  // UI States
  const [resourceType, setResourceType] = useState<'product' | 'collection'>('product');
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [isCollectionModalOpen, setIsCollectionModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Local state for display purposes (names, images)
  const [selectedProducts, setSelectedProducts] = useState<any[]>([]);
  const [selectedCollections, setSelectedCollections] = useState<any[]>([]);

  // Sync state with formData
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      productIds: selectedProducts.map(p => p.id),
      categoryIds: selectedCollections.map(c => c.id),
      // If we want to ensure mutual exclusivity based on 'appliesToAllProducts' flag or similar, handle here.
      // But for "Specific product OR collection", we usually just send what's populated.
    }));
  }, [selectedProducts, selectedCollections]);

  const handleSubmit = () => {
    onSubmit(formData);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    if (value.length > 0) {
      if (resourceType === 'product') {
        setIsProductModalOpen(true);
      } else {
        setIsCollectionModalOpen(true);
      }
    }
  };

  const removeItem = (id: string, type: 'product' | 'collection') => {
    if (type === 'product') {
      setSelectedProducts(prev => prev.filter(p => p.id !== id));
    } else {
      setSelectedCollections(prev => prev.filter(c => c.id !== id));
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main Form Column */}
        <div className="flex-1 max-w-3xl space-y-6">
          {/* Method & Code */}
          <Card>
            <CardHeader>
              <CardTitle>Method</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <RadioGroup
                value={formData.method}
                onValueChange={(value) =>
                  setFormData({ ...formData, method: value as Types.WorkspaceStoreDiscountMethodChoices })
                }
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value={Types.WorkspaceStoreDiscountMethodChoices.DiscountCode} id="method-code" />
                  <Label htmlFor="method-code" className="font-normal cursor-pointer">
                    Discount code
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value={Types.WorkspaceStoreDiscountMethodChoices.Automatic} id="method-auto" />
                  <Label htmlFor="method-auto" className="font-normal cursor-pointer">
                    Automatic discount
                  </Label>
                </div>
              </RadioGroup>

              <div className="space-y-2">
                <Label htmlFor="code">Discount code</Label>
                <Input
                  id="code"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  placeholder="e.g., SUMMER20"
                  required
                />
              </div>
            </CardContent>
          </Card>

          {/* Value & Applies To */}
          <Card>
            <CardHeader>
              <CardTitle>Value</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Side-by-side Value Inputs */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="value-type">Type</Label>
                  <Select
                    value={formData.discountValueType}
                    onValueChange={(value) =>
                      setFormData({
                        ...formData,
                        discountValueType: value as Types.WorkspaceStoreDiscountDiscountValueTypeChoices,
                      })
                    }
                  >
                    <SelectTrigger id="value-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={Types.WorkspaceStoreDiscountDiscountValueTypeChoices.Percentage}>
                        Percentage
                      </SelectItem>
                      <SelectItem value={Types.WorkspaceStoreDiscountDiscountValueTypeChoices.FixedAmount}>
                        Fixed amount
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="value">Value</Label>
                  <div className="relative">
                    <Input
                      id="value"
                      type="number"
                      value={formData.value || ''}
                      onChange={(e) => setFormData({ ...formData, value: Number(e.target.value) })}
                      placeholder="0"
                      required
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm pointer-events-none">
                      {formData.discountValueType === Types.WorkspaceStoreDiscountDiscountValueTypeChoices.Percentage ? '%' : 'FCFA'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t space-y-4">
                <div className="space-y-2">
                  <Label>Applies to</Label>
                  <Select
                    value={resourceType}
                    onValueChange={(value: 'product' | 'collection') => {
                      setResourceType(value);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="product">Specific products</SelectItem>
                      <SelectItem value="collection">Specific collections</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Search & Browse */}
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder={`Search ${resourceType}s...`}
                      value={searchTerm}
                      onChange={handleSearchChange}
                      className="pl-9"
                    />
                  </div>
                  <Button
                    variant="outline"
                    type="button"
                    onClick={() => resourceType === 'product' ? setIsProductModalOpen(true) : setIsCollectionModalOpen(true)}
                  >
                    Browse
                  </Button>
                </div>

                {/* Selected Items List */}
                <div className="space-y-2">
                  {resourceType === 'product' && selectedProducts.length > 0 && (
                    <div className="border rounded-md divide-y">
                      {selectedProducts.map(product => (
                        <div key={product.id} className="flex items-center justify-between p-3 text-sm">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-muted rounded overflow-hidden flex-shrink-0">
                              {product.mediaGallery?.[0]?.thumbnailUrl && (
                                <img src={product.mediaGallery[0].thumbnailUrl} alt="" className="w-full h-full object-cover" />
                              )}
                            </div>
                            <span className="font-medium">{product.name}</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                            onClick={() => removeItem(product.id, 'product')}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {resourceType === 'collection' && selectedCollections.length > 0 && (
                    <div className="border rounded-md divide-y">
                      {selectedCollections.map(collection => (
                        <div key={collection.id} className="flex items-center justify-between p-3 text-sm">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-muted rounded overflow-hidden flex-shrink-0">
                              {collection.featuredMedia?.thumbnailUrl && (
                                <img src={collection.featuredMedia.thumbnailUrl} alt="" className="w-full h-full object-cover" />
                              )}
                            </div>
                            <span className="font-medium">{collection.name}</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                            onClick={() => removeItem(collection.id, 'collection')}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Shared Sections */}
          <MinimumRequirementsSection
            minimumRequirementType={formData.minimumRequirementType}
            minimumPurchaseAmount={formData.minimumPurchaseAmount}
            minimumQuantityItems={formData.minimumQuantityItems}
            onRequirementTypeChange={(type) => setFormData({ ...formData, minimumRequirementType: type })}
            onPurchaseAmountChange={(amount) => setFormData({ ...formData, minimumPurchaseAmount: amount })}
            onQuantityChange={(quantity) => setFormData({ ...formData, minimumQuantityItems: quantity })}
          />
        </div>

        {/* Sidebar Column */}
        <div className="w-full lg:w-96 lg:flex-shrink-0 space-y-6">
          {/* Action Buttons (Sticky) */}
          <Card className="p-4 space-y-3 sticky top-6 z-10">
            <Button
              onClick={handleSubmit}
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : 'Save discount'}
            </Button>
            <Button
              variant="outline"
              onClick={onDiscard}
              className="w-full"
              disabled={isLoading}
            >
              Discard
            </Button>
          </Card>

          <MaximumUsesSection
            limitTotalUses={formData.limitTotalUses}
            usageLimit={formData.usageLimit}
            limitOnePerCustomer={formData.limitOnePerCustomer}
            onLimitTotalUsesChange={(checked) => setFormData({ ...formData, limitTotalUses: checked })}
            onUsageLimitChange={(limit) => setFormData({ ...formData, usageLimit: limit })}
            onLimitOnePerCustomerChange={(checked) => setFormData({ ...formData, limitOnePerCustomer: checked })}
          />

          <CombinationsSection
            canCombineWithProductDiscounts={formData.canCombineWithProductDiscounts}
            canCombineWithOrderDiscounts={formData.canCombineWithOrderDiscounts}
            onProductDiscountsChange={(checked) => setFormData({ ...formData, canCombineWithProductDiscounts: checked })}
            onOrderDiscountsChange={(checked) => setFormData({ ...formData, canCombineWithOrderDiscounts: checked })}
          />

          <ActiveDatesSection
            startsAt={formData.startsAt}
            endsAt={formData.endsAt}
            onStartsAtChange={(date) => setFormData({ ...formData, startsAt: date })}
            onEndsAtChange={(date) => setFormData({ ...formData, endsAt: date })}
          />
        </div>
      </div>

      {/* Modals */}
      <ProductSearchModal
        mode="order"
        open={isProductModalOpen}
        onOpenChange={setIsProductModalOpen}
        selectedProductIds={formData.productIds || []}
        onAddProducts={(products: any[]) => {
          const newProducts = products.filter(p => !selectedProducts.some(sp => sp.id === p.id));
          setSelectedProducts([...selectedProducts, ...newProducts]);
          setSearchTerm('');
        }}
      />

      <CollectionSearchModal
        open={isCollectionModalOpen}
        onOpenChange={setIsCollectionModalOpen}
        selectedCollectionIds={formData.categoryIds || []}
        onAddCollections={(collections: any[]) => {
          const newCollections = collections.filter(c => !selectedCollections.some(sc => sc.id === c.id));
          setSelectedCollections([...selectedCollections, ...newCollections]);
          setSearchTerm('');
        }}
      />
    </div>
  );
}
