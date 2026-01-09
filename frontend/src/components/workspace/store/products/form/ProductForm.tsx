'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/shadcn-ui/button'
import { Card } from '@/components/shadcn-ui/card'
import { ProductTitleSection } from './ProductTitleSection'
import { ProductMediaSection } from './media'
import { ProductPricingSection } from './ProductPricingSection'
import type { MediaItem } from './media'
import { ProductInventorySection } from './ProductInventorySection'
import { ProductShippingSection } from './ProductShippingSection'
import { ProductSidebar } from './ProductSidebar'
import { ProductVariantsSection, ProductOption, VariantFormState } from './variants'
import { ProductSEOSection } from './seo'
import { ProductOrganizationSection, CategoryOption } from './organization'
import { Save, Eye } from 'lucide-react'
import type { ProductCreateInput } from '@/types/workspace/store/graphql-base'
import { useUnsavedChanges } from '@/hooks/workspace/store/useUnsavedChanges'
import { cn } from '@/lib/utils'

// Extended form data with UI-only fields (weight unit)
export interface ProductFormData extends Omit<ProductCreateInput, 'price' | 'compareAtPrice' | 'costPrice' | 'weight' | 'tags' | 'images' | 'existingImageIds' | 'options' | 'variants' | 'seo' | 'featuredMediaId' | 'mediaGalleryIds'> {
  price: number
  compareAtPrice?: number
  costPrice?: number
  chargeTax: boolean
  paymentCharges: boolean
  chargesAmount?: number
  sku: string
  barcode?: string
  vendor: string
  trackInventory: boolean
  onhand: number
  available: number
  condition: string
  locationId?: string
  allowBackorders: boolean
  requiresShipping: boolean
  packageId?: string
  weight?: number
  weightUnit: string
  tags: string[]
  mediaItems: MediaItem[] // UI-only field for managing media
  featuredMediaId?: string // First image ID for backend
  mediaGalleryIds?: string[] // Rest of image IDs for backend
  status: 'draft' | 'published'
  // Variants
  hasVariants: boolean
  options: ProductOption[]
  variants: VariantFormState[]
  // SEO
  metaTitle: string
  metaDescription: string
  slug: string
  // Organization (replacing old category/type)
  productType: string
  categoryId: string
}

export interface ProductFormProps {
  initialData?: Partial<ProductFormData>
  onSubmit?: (data: ProductFormData) => void | Promise<void>
  onSaveDraft?: (data: ProductFormData) => void | Promise<void>
  onPreview?: () => void
  onDiscard?: () => void
  isEditing?: boolean
  isLoading?: boolean
  existingImages?: Array<{ id: string; url: string; width: number; height: number }>
  onRemoveExistingImage?: (uploadId: string) => void
  categories?: CategoryOption[] // Add categories prop
  enableUnsavedChanges?: boolean // Enable unsaved changes protection
  onUnsavedChangesMount?: (confirmNavigation: (onConfirm: () => void) => void) => void // Pass confirmNavigation to parent
}

export function ProductForm({
  initialData,
  onSubmit,
  onSaveDraft,
  onPreview,
  onDiscard,
  isEditing = false,
  isLoading = false,
  existingImages = [],
  onRemoveExistingImage,
  categories = [],
  enableUnsavedChanges = true,
  onUnsavedChangesMount,
}: ProductFormProps) {
  const [formData, setFormData] = useState<ProductFormData>({
    name: '',
    description: '',
    mediaItems: [],
    price: 0,
    compareAtPrice: undefined,
    costPrice: undefined,
    chargeTax: false,
    paymentCharges: false,
    chargesAmount: undefined,
    sku: '',
    barcode: '',
    trackInventory: false,  // Default OFF for better UX
    onhand: 0,
    available: 0,
    condition: 'new',
    locationId: undefined,
    allowBackorders: false,
    requiresShipping: false,  // Default OFF for better UX
    packageId: undefined,
    weight: undefined,
    weightUnit: 'kg',
    status: 'draft',
    vendor: '',
    tags: [],
    hasVariants: false,
    options: [],
    variants: [],
    metaTitle: '',
    metaDescription: '',
    slug: '',
    productType: 'physical',  // Default to physical
    categoryId: '',
    ...initialData,
  })

  // Auto-disable inventory/shipping/variants when non-physical product type is selected
  useEffect(() => {
    if (formData.productType === 'digital' || formData.productType === 'service') {
      setFormData(prev => ({
        ...prev,
        trackInventory: false,
        requiresShipping: false,
        hasVariants: false,
        allowBackorders: false,
      }))
    }
  }, [formData.productType])


  // Unsaved changes protection (Shopify-style)
  const { isDirty, markAsDirty, markAsSaved, confirmNavigation } = useUnsavedChanges({
    onSave: async () => {
      await handleSubmit()
    },
    onDiscard: onDiscard,
    enabled: enableUnsavedChanges,
  })

  // Pass confirmNavigation to parent component on mount (only once)
  useEffect(() => {
    if (onUnsavedChangesMount) {
      onUnsavedChangesMount(confirmNavigation)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run on mount

  const updateFormData = (updates: Partial<ProductFormData>) => {
    setFormData(prev => ({ ...prev, ...updates }))
    markAsDirty() // Mark form as dirty when data changes
  }

  const handleSubmit = async () => {
    // Transform mediaItems to backend format
    // First image = featuredMedia, rest = mediaGallery
    const [firstItem, ...restItems] = formData.mediaItems

    const submitData: ProductFormData = {
      ...formData,
      // First image becomes featured media
      featuredMediaId: firstItem?.uploadId,
      // Rest become media gallery
      mediaGalleryIds: restItems.map(item => item.uploadId),
    }

    await onSubmit?.(submitData)
    markAsSaved() // Mark as saved after successful submit
  }

  const handleSaveDraft = async () => {
    await onSaveDraft?.(formData)
    markAsSaved() // Mark as saved after successful draft save
  }

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main Form Column */}
        <div className="flex-1 max-w-3xl space-y-6">
          <ProductTitleSection
            name={formData.name}
            description={formData.description || ''}
            onNameChange={(name) => updateFormData({ name })}
            onDescriptionChange={(description) => updateFormData({ description })}
          />

          <ProductMediaSection
            mediaItems={formData.mediaItems}
            onChange={(mediaItems) => updateFormData({ mediaItems })}
            existingImages={existingImages}
            onRemoveExisting={onRemoveExistingImage}
          />

          <ProductPricingSection
            price={formData.price}
            compareAtPrice={formData.compareAtPrice}
            costPrice={formData.costPrice}
            chargeTax={formData.chargeTax}
            paymentCharges={formData.paymentCharges}
            chargesAmount={formData.chargesAmount}
            onPriceChange={(price) => updateFormData({ price })}
            onCompareAtPriceChange={(compareAtPrice) => updateFormData({ compareAtPrice })}
            onCostPriceChange={(costPrice) => updateFormData({ costPrice })}
            onChargeTaxChange={(chargeTax) => updateFormData({ chargeTax })}
            onPaymentChargesChange={(paymentCharges) => updateFormData({ paymentCharges })}
            onChargesAmountChange={(chargesAmount) => updateFormData({ chargesAmount })}
          />

          <ProductInventorySection
            sku={formData.sku || ''}
            barcode={formData.barcode || ''}
            trackInventory={formData.trackInventory ?? true}
            onhand={formData.onhand ?? 0}
            available={formData.available ?? 0}
            condition={formData.condition ?? 'new'}
            locationId={formData.locationId}
            allowBackorders={formData.allowBackorders ?? false}
            onSkuChange={(sku) => updateFormData({ sku })}
            onBarcodeChange={(barcode) => updateFormData({ barcode })}
            onTrackInventoryChange={(trackInventory) => updateFormData({ trackInventory })}
            onOnhandChange={(onhand) => updateFormData({ onhand })}
            onAvailableChange={(available) => updateFormData({ available })}
            onConditionChange={(condition) => updateFormData({ condition })}
            onLocationIdChange={(locationId) => updateFormData({ locationId })}
            onAllowBackordersChange={(allowBackorders) => updateFormData({ allowBackorders })}
          />

          <ProductShippingSection
            requiresShipping={formData.requiresShipping}
            packageId={formData.packageId}
            weight={formData.weight}
            weightUnit={formData.weightUnit}
            onRequiresShippingChange={(requiresShipping) => updateFormData({ requiresShipping })}
            onPackageIdChange={(packageId) => updateFormData({ packageId })}
            onWeightChange={(weight) => updateFormData({ weight })}
            onWeightUnitChange={(weightUnit) => updateFormData({ weightUnit })}
          />

          <ProductVariantsSection
            hasVariants={formData.hasVariants}
            options={formData.options}
            variants={formData.variants}
            basePrice={formData.price}
            onHasVariantsChange={(hasVariants) => updateFormData({ hasVariants })}
            onOptionsChange={(options) => updateFormData({ options })}
            onVariantsChange={(variants) => updateFormData({ variants })}
          />

          <ProductSEOSection
            productName={formData.name}
            productDescription={formData.description || ''}
            productPrice={formData.price}
            metaTitle={formData.metaTitle}
            metaDescription={formData.metaDescription}
            slug={formData.slug}
            onMetaTitleChange={(metaTitle) => updateFormData({ metaTitle })}
            onMetaDescriptionChange={(metaDescription) => updateFormData({ metaDescription })}
            onSlugChange={(slug) => updateFormData({ slug })}
          />
        </div>

        {/* Sidebar Column */}
        <div className="w-full lg:w-96 lg:flex-shrink-0 space-y-6">
          <ProductSidebar
            status={formData.status}
            onStatusChange={(status) => updateFormData({ status })}
          />

          <ProductOrganizationSection
            productType={formData.productType}
            vendor={formData.vendor}
            categoryId={formData.categoryId}
            tags={formData.tags}
            categories={categories}
            onProductTypeChange={(productType) => updateFormData({ productType })}
            onVendorChange={(vendor) => updateFormData({ vendor })}
            onCategoryIdChange={(categoryId) => updateFormData({ categoryId })}
            onTagsChange={(tags) => updateFormData({ tags })}
          />

          {/* Action Buttons */}
          <Card className="p-4 space-y-3 sticky top-6">
            <div className="flex gap-2">
              <Button
                onClick={handleSaveDraft}
                variant="outline"
                className="flex-1"
                disabled={isLoading}
              >
                <Save className="mr-2 h-4 w-4" />
                Save draft
              </Button>
              <Button
                onClick={handleSubmit}
                className="flex-1"
                disabled={isLoading}
              >
                {isLoading ? 'Saving...' : (isEditing ? 'Update product' : 'Publish product')}
              </Button>
            </div>

            <Button
              onClick={onPreview}
              variant="outline"
              className="w-full"
              disabled={isLoading}
            >
              <Eye className="mr-2 h-4 w-4" />
              Preview
            </Button>
          </Card>
        </div>
      </div>
    </div>
  )
}