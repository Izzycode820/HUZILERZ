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

export interface BuyXGetYFormData {
  code: string;
  name?: string;
  method: Types.WorkspaceStoreDiscountMethodChoices;
  customerBuysType: Types.WorkspaceStoreDiscountCustomerBuysTypeChoices;
  customerBuysQuantity?: number;
  customerBuysValue?: number;
  customerBuysProductIds?: string[];
  customerGetsQuantity?: number;
  customerGetsProductIds?: string[];
  bxgyDiscountType: Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices;
  bxgyValue?: number;
  maxUsesPerOrder?: number;
  startsAt: string;
  endsAt?: string;
  minimumRequirementType: Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices; // Note: Typically BxGy doesn't use this, but keeping if shared
  minimumPurchaseAmount?: number;
  minimumQuantityItems?: number;
  limitTotalUses: boolean;
  usageLimit?: number;
  limitOnePerCustomer: boolean;
  canCombineWithProductDiscounts: boolean;
  canCombineWithOrderDiscounts: boolean;
  appliesToAllCustomers: boolean;
  // Note: We might map "Buys Collections" to generic categoryIds if backend supports it
  categoryIds?: string[];
}

interface BuyXGetYFormProps {
  onSubmit: (data: BuyXGetYFormData) => void;
  onDiscard: () => void;
  isLoading?: boolean;
}

export function BuyXGetYForm({ onSubmit, onDiscard, isLoading }: BuyXGetYFormProps) {
  const [formData, setFormData] = useState<BuyXGetYFormData>({
    code: '',
    method: Types.WorkspaceStoreDiscountMethodChoices.DiscountCode,
    customerBuysType: Types.WorkspaceStoreDiscountCustomerBuysTypeChoices.MinimumQuantity,
    bxgyDiscountType: Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices.Percentage,
    startsAt: new Date().toISOString(),
    minimumRequirementType: Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices.None,
    limitTotalUses: false,
    limitOnePerCustomer: false,
    canCombineWithProductDiscounts: false,
    canCombineWithOrderDiscounts: false,
    appliesToAllCustomers: true,
    customerBuysProductIds: [],
    customerGetsProductIds: [],
    categoryIds: [],
  });

  // UI States for Selection Logic
  const [buysResourceType, setBuysResourceType] = useState<'product' | 'collection'>('product');
  const [getsResourceType, setGetsResourceType] = useState<'product' | 'collection'>('product');

  // Modal States
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [isCollectionModalOpen, setIsCollectionModalOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<'buys' | 'gets' | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Selected Items State
  const [selectedBuysProducts, setSelectedBuysProducts] = useState<any[]>([]);
  const [selectedBuysCollections, setSelectedBuysCollections] = useState<any[]>([]);
  const [selectedGetsProducts, setSelectedGetsProducts] = useState<any[]>([]);
  const [selectedGetsCollections, setSelectedGetsCollections] = useState<any[]>([]);

  // Sync state with formData
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      customerBuysProductIds: selectedBuysProducts.map(p => p.id),
      customerGetsProductIds: selectedGetsProducts.map(p => p.id),
      // Mapping Buys Collections to categoryIds as primary context for now
      categoryIds: selectedBuysCollections.map(c => c.id),
    }));
  }, [selectedBuysProducts, selectedGetsProducts, selectedBuysCollections]);

  const handleSubmit = () => {
    onSubmit(formData);
  };

  const handleSearchChange = (value: string, section: 'buys' | 'gets') => {
    setSearchTerm(value);
    setActiveSection(section);

    // Determine which modal to open based on section's resource type
    const resourceType = section === 'buys' ? buysResourceType : getsResourceType;

    if (value.length > 0) {
      if (resourceType === 'product') {
        setIsProductModalOpen(true);
      } else {
        setIsCollectionModalOpen(true);
      }
    }
  };

  const handleBrowseClick = (section: 'buys' | 'gets') => {
    setActiveSection(section);
    setSearchTerm(''); // Clear search when browsing
    const resourceType = section === 'buys' ? buysResourceType : getsResourceType;
    if (resourceType === 'product') {
      setIsProductModalOpen(true);
    } else {
      setIsCollectionModalOpen(true);
    }
  };

  const removeItem = (id: string, section: 'buys' | 'gets', type: 'product' | 'collection') => {
    if (section === 'buys') {
      if (type === 'product') {
        setSelectedBuysProducts(prev => prev.filter(p => p.id !== id));
      } else {
        setSelectedBuysCollections(prev => prev.filter(c => c.id !== id));
      }
    } else {
      if (type === 'product') {
        setSelectedGetsProducts(prev => prev.filter(p => p.id !== id));
      } else {
        setSelectedGetsCollections(prev => prev.filter(c => c.id !== id));
      }
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
                  placeholder="e.g., BUY2GET1"
                  required
                />
              </div>
            </CardContent>
          </Card>

          {/* Customer Buys */}
          <Card>
            <CardHeader>
              <CardTitle>Customer buys</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="buys-type">Requirement type</Label>
                  <Select
                    value={formData.customerBuysType}
                    onValueChange={(value) =>
                      setFormData({
                        ...formData,
                        customerBuysType: value as Types.WorkspaceStoreDiscountCustomerBuysTypeChoices,
                      })
                    }
                  >
                    <SelectTrigger id="buys-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={Types.WorkspaceStoreDiscountCustomerBuysTypeChoices.MinimumQuantity}>
                        Minimum quantity of items
                      </SelectItem>
                      <SelectItem value={Types.WorkspaceStoreDiscountCustomerBuysTypeChoices.MinimumPurchaseAmount}>
                        Minimum purchase amount
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="buys-value">
                    {formData.customerBuysType === Types.WorkspaceStoreDiscountCustomerBuysTypeChoices.MinimumQuantity
                      ? 'Quantity'
                      : 'Amount'}
                  </Label>
                  <div className="relative">
                    <Input
                      id="buys-value"
                      type="number"
                      value={
                        formData.customerBuysType === Types.WorkspaceStoreDiscountCustomerBuysTypeChoices.MinimumQuantity
                          ? formData.customerBuysQuantity || ''
                          : formData.customerBuysValue || ''
                      }
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        if (formData.customerBuysType === Types.WorkspaceStoreDiscountCustomerBuysTypeChoices.MinimumQuantity) {
                          setFormData({ ...formData, customerBuysQuantity: val, customerBuysValue: undefined });
                        } else {
                          setFormData({ ...formData, customerBuysValue: val, customerBuysQuantity: undefined });
                        }
                      }}
                      placeholder="0"
                      required
                    />
                    {formData.customerBuysType === Types.WorkspaceStoreDiscountCustomerBuysTypeChoices.MinimumPurchaseAmount && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm pointer-events-none">
                        FCFA
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t space-y-4">
                <div className="space-y-2">
                  <Label>Any items from</Label>
                  <Select
                    value={buysResourceType}
                    onValueChange={(value: 'product' | 'collection') => setBuysResourceType(value)}
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

                {/* Buys Search & Browse */}
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder={`Search ${buysResourceType}s...`}
                      value={activeSection === 'buys' ? searchTerm : ''}
                      onChange={(e) => handleSearchChange(e.target.value, 'buys')}
                      className="pl-9"
                    />
                  </div>
                  <Button
                    variant="outline"
                    type="button"
                    onClick={() => handleBrowseClick('buys')}
                  >
                    Browse
                  </Button>
                </div>

                {/* Buys Selected Items List */}
                <div className="space-y-2">
                  {buysResourceType === 'product' && selectedBuysProducts.length > 0 && (
                    <div className="border rounded-md divide-y">
                      {selectedBuysProducts.map(product => (
                        <div key={product.id} className="flex items-center justify-between p-3 text-sm">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-muted rounded overflow-hidden flex-shrink-0">
                              {product.mediaGallery?.[0]?.thumbnailUrl && (
                                <img src={product.mediaGallery[0].thumbnailUrl} alt="" className="w-full h-full object-cover" />
                              )}
                            </div>
                            <span className="font-medium">{product.name}</span>
                          </div>
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => removeItem(product.id, 'buys', 'product')}>
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                  {buysResourceType === 'collection' && selectedBuysCollections.length > 0 && (
                    <div className="border rounded-md divide-y">
                      {selectedBuysCollections.map(collection => (
                        <div key={collection.id} className="flex items-center justify-between p-3 text-sm">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-muted rounded overflow-hidden flex-shrink-0">
                              {collection.featuredMedia?.thumbnailUrl && (
                                <img src={collection.featuredMedia.thumbnailUrl} alt="" className="w-full h-full object-cover" />
                              )}
                            </div>
                            <span className="font-medium">{collection.name}</span>
                          </div>
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => removeItem(collection.id, 'buys', 'collection')}>
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

          {/* Customer Gets */}
          <Card>
            <CardHeader>
              <CardTitle>Customer gets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="gets-quantity">Quantity</Label>
                  <Input
                    id="gets-quantity"
                    type="number"
                    value={formData.customerGetsQuantity || ''}
                    onChange={(e) => setFormData({ ...formData, customerGetsQuantity: Number(e.target.value) })}
                    placeholder="0"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label>Any items from</Label>
                  <Select
                    value={getsResourceType}
                    onValueChange={(value: 'product' | 'collection') => setGetsResourceType(value)}
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

                {/* Gets Search & Browse */}
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder={`Search ${getsResourceType}s...`}
                      value={activeSection === 'gets' ? searchTerm : ''}
                      onChange={(e) => handleSearchChange(e.target.value, 'gets')}
                      className="pl-9"
                    />
                  </div>
                  <Button
                    variant="outline"
                    type="button"
                    onClick={() => handleBrowseClick('gets')}
                  >
                    Browse
                  </Button>
                </div>

                {/* Gets Selected Items List */}
                <div className="space-y-2">
                  {getsResourceType === 'product' && selectedGetsProducts.length > 0 && (
                    <div className="border rounded-md divide-y">
                      {selectedGetsProducts.map(product => (
                        <div key={product.id} className="flex items-center justify-between p-3 text-sm">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-muted rounded overflow-hidden flex-shrink-0">
                              {product.mediaGallery?.[0]?.thumbnailUrl && (
                                <img src={product.mediaGallery[0].thumbnailUrl} alt="" className="w-full h-full object-cover" />
                              )}
                            </div>
                            <span className="font-medium">{product.name}</span>
                          </div>
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => removeItem(product.id, 'gets', 'product')}>
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                  {getsResourceType === 'collection' && selectedGetsCollections.length > 0 && (
                    <div className="border rounded-md divide-y">
                      {selectedGetsCollections.map(collection => (
                        <div key={collection.id} className="flex items-center justify-between p-3 text-sm">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-muted rounded overflow-hidden flex-shrink-0">
                              {collection.featuredMedia?.thumbnailUrl && (
                                <img src={collection.featuredMedia.thumbnailUrl} alt="" className="w-full h-full object-cover" />
                              )}
                            </div>
                            <span className="font-medium">{collection.name}</span>
                          </div>
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => removeItem(collection.id, 'gets', 'collection')}>
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 border-t pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="discount-type">At a discounted value</Label>
                    <Select
                      value={formData.bxgyDiscountType}
                      onValueChange={(value) =>
                        setFormData({
                          ...formData,
                          bxgyDiscountType: value as Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices,
                        })
                      }
                    >
                      <SelectTrigger id="discount-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices.Percentage}>
                          Percentage
                        </SelectItem>
                        <SelectItem value={Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices.AmountOffEach}>
                          Amount off each
                        </SelectItem>
                        <SelectItem value={Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices.Free}>Free</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.bxgyDiscountType !== Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices.Free && (
                    <div className="space-y-2">
                      <Label htmlFor="bxgy-value">
                        {formData.bxgyDiscountType === Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices.Percentage
                          ? 'Value'
                          : 'Amount'}
                      </Label>
                      <div className="relative">
                        <Input
                          id="bxgy-value"
                          type="number"
                          value={formData.bxgyValue || ''}
                          onChange={(e) => setFormData({ ...formData, bxgyValue: Number(e.target.value) })}
                          placeholder="0"
                          required
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm pointer-events-none">
                          {formData.bxgyDiscountType === Types.WorkspaceStoreDiscountBxgyDiscountTypeChoices.Percentage ? '%' : 'FCFA'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="max-uses">Set a maximum number of uses per order (optional)</Label>
                  <Input
                    id="max-uses"
                    type="number"
                    value={formData.maxUsesPerOrder || ''}
                    onChange={(e) => setFormData({ ...formData, maxUsesPerOrder: Number(e.target.value) || undefined })}
                    placeholder="0"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

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
        selectedProductIds={
          activeSection === 'buys'
            ? formData.customerBuysProductIds || []
            : formData.customerGetsProductIds || []
        }
        onAddProducts={(products: any[]) => {
          if (activeSection === 'buys') {
            const newProducts = products.filter(p => !selectedBuysProducts.some(sp => sp.id === p.id));
            setSelectedBuysProducts([...selectedBuysProducts, ...newProducts]);
          } else if (activeSection === 'gets') {
            const newProducts = products.filter(p => !selectedGetsProducts.some(sp => sp.id === p.id));
            setSelectedGetsProducts([...selectedGetsProducts, ...newProducts]);
          }
          setSearchTerm('');
        }}
      />

      <CollectionSearchModal
        open={isCollectionModalOpen}
        onOpenChange={setIsCollectionModalOpen}
        selectedCollectionIds={
          activeSection === 'buys'
            ? selectedBuysCollections.map(c => c.id)
            : selectedGetsCollections.map(c => c.id)
        }
        onAddCollections={(collections: any[]) => {
          if (activeSection === 'buys') {
            const newCollections = collections.filter(c => !selectedBuysCollections.some(sc => sc.id === c.id));
            setSelectedBuysCollections([...selectedBuysCollections, ...newCollections]);
          } else if (activeSection === 'gets') {
            const newCollections = collections.filter(c => !selectedGetsCollections.some(sc => sc.id === c.id));
            setSelectedGetsCollections([...selectedGetsCollections, ...newCollections]);
          }
          setSearchTerm('');
        }}
      />
    </div>
  );
}
