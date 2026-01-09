'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ProductForm, type ProductFormData } from '@/components/workspace/store/products/form/ProductForm';
import { Button } from '@/components/shadcn-ui/button';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useMutation, useQuery } from '@apollo/client/react';
import { CreateProductDocument } from '@/services/graphql/admin-store/mutations/products/__generated__/CreateProduct.generated';
import { CategoryPickerDocument } from '@/services/graphql/admin-store/queries/categories/__generated__/CategoryPicker.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';
import { flattenVariantsForMutation } from '@/components/workspace/store/products/form/variants/utils';

export default function AddProductPage() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);
  const [confirmNavigationFn, setConfirmNavigationFn] = React.useState<
    ((onConfirm: () => void) => void) | null
  >(null);

  // Fetch categories for dropdown
  const { data: categoriesData } = useQuery(CategoryPickerDocument);

  // Extract categories from edges
  const categories =
    categoriesData?.categories?.edges
      ?.map(edge => edge?.node)
      .filter((node): node is NonNullable<typeof node> => node !== null)
    || [];

  const [createProduct, { loading }] = useMutation(CreateProductDocument, {
    onCompleted: (data) => {
      if (data.createProduct?.success && data.createProduct?.product) {
        toast.success(`${data.createProduct.product.name} has been created successfully.`);
        // Navigate to products list
        router.push(`/workspace/${currentWorkspace?.id}/store/products`);
      } else {
        toast.error(data.createProduct?.error || "Failed to create product");
      }
    },
    onError: (error) => {
      toast.error(error.message || "An unexpected error occurred");
    },
  });

  const handleSubmit = async (data: ProductFormData) => {
    // Flatten hierarchical variants to extract only leaf nodes (actual sellable variants)
    const flattenedVariants = data.hasVariants ? flattenVariantsForMutation(data.variants) : [];

    await createProduct({
      variables: {
        productData: {
          name: data.name,
          description: data.description,
          price: data.price.toString(),
          costPrice: data.costPrice?.toString(),
          compareAtPrice: data.compareAtPrice?.toString(),
          chargeTax: data.chargeTax,
          paymentCharges: data.paymentCharges,
          chargesAmount: data.chargesAmount?.toString(),

          // Media (upload-first system)
          featuredMediaId: data.featuredMediaId,
          mediaIds: data.mediaGalleryIds,

          // Inventory
          inventory: {
            sku: data.sku,
            barcode: data.barcode || '',
            trackInventory: data.trackInventory,
            inventoryQuantity: data.onhand,
            available: data.available,
            condition: data.condition,
            locationId: data.locationId,
            allowBackorders: data.allowBackorders,
          },

          // Shipping
          shipping: {
            requiresShipping: data.requiresShipping,
            packageId: data.packageId,
            weight: data.weight?.toString(),
          },

          // Organization
          organization: {
            productType: data.productType,
            vendor: data.vendor,
            categoryId: data.categoryId || undefined,
            tags: JSON.stringify(data.tags || []),
          },

          // SEO
          seo: {
            metaTitle: data.metaTitle,
            metaDescription: data.metaDescription,
            slug: data.slug,
          },

          // Variants (if has variants)
          hasVariants: data.hasVariants,
          options: data.hasVariants ? data.options.map(opt => ({
            optionName: opt.optionName,
            optionValues: opt.optionValues,
          })) : undefined,
          variants: data.hasVariants ? flattenedVariants.map(variant => ({
            option1: variant.option1 || undefined,
            option2: variant.option2 || undefined,
            option3: variant.option3 || undefined,
            price: variant.price?.toString(),
            costPrice: variant.cost_price?.toString(),
            compareAtPrice: variant.compare_at_price?.toString(),
            isActive: variant.is_active ?? true,
            position: variant.position,
            // Variant featured media (upload-first system)
            featuredMediaId: variant.featuredMediaId,
            // Variant inventory
            inventory: {
              sku: variant.sku || '',
              barcode: variant.barcode || '',
              trackInventory: true,
              inventoryQuantity: variant.inventoryQuantity || 0,
              available: variant.inventoryQuantity || 0,
              condition: 'new',
            },
          })) : undefined,

          status: data.status.toLowerCase() as any,
        },
      },
    });
  };

  const handleSaveDraft = async (data: ProductFormData) => {
    // Save as draft by setting status to DRAFT
    await createProduct({
      variables: {
        productData: {
          name: data.name,
          description: data.description,
          price: data.price.toString(),
          status: 'draft',
          inventory: {
            sku: data.sku,
            trackInventory: data.trackInventory,
            inventoryQuantity: data.onhand,
          },
        },
      },
    });
  };

  const handlePreview = () => {
    toast.info("Save product first");
  };

  const handleDiscard = () => {
    // Navigate back to products list
    router.push(`/workspace/${currentWorkspace?.id}/store/products`);
  };

  const handleBackClick = () => {
    if (confirmNavigationFn) {
      confirmNavigationFn(() => {
        router.push(`/workspace/${currentWorkspace?.id}/store/products`);
      });
    } else {
      router.push(`/workspace/${currentWorkspace?.id}/store/products`);
    }
  };

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading workspace...</p>
      </div>
    );
  }

  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Header */}
        <div className="px-4 lg:px-6">
          <div className="flex items-center gap-4 mb-4">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={handleBackClick}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold">Add Product</h1>
          </div>
          <p className="text-muted-foreground">
            Create a new product for your store
          </p>
        </div>

        {/* Main Form */}
        <div className="px-4 lg:px-6">
          <ProductForm
            onSubmit={handleSubmit}
            onSaveDraft={handleSaveDraft}
            onPreview={handlePreview}
            onDiscard={handleDiscard}
            onUnsavedChangesMount={(fn) => setConfirmNavigationFn(() => fn)}
            isEditing={false}
            isLoading={loading}
            categories={categories}
          />
        </div>
      </div>
    </div>
  );
}