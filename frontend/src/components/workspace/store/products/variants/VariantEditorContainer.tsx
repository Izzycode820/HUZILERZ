'use client';

/**
 * Variant Editor Container (Smart Component)
 *
 * Shopify-style variant editing interface
 * - Left panel: Product info + searchable variant list
 * - Right panel: Selected variant editor with inventory
 */

import React, { useState, useMemo, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client/react';
import { GetProductDocument } from '@/services/graphql/admin-store/queries/products/__generated__/GetProduct.generated';
import { UpdateVariantDocument } from '@/services/graphql/admin-store/mutations/variants/__generated__/UpdateVariant.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';
import { VariantsList } from './VariantsList';
import { VariantEditorForm } from './VariantEditorForm';
import { Card } from '@/components/shadcn-ui/card';
import { Loader2 } from 'lucide-react';

export default function VariantEditorContainer() {
  const router = useRouter();
  const params = useParams();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const productId = params.id as string;
  const variantIdParam = params.variant_id as string;

  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(variantIdParam || null);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch product with all variants
  const { data, loading, error, refetch } = useQuery(GetProductDocument, {
    variables: { id: productId },
    skip: !currentWorkspace || !productId,
  });

  // Auto-select first variant if none selected
  useEffect(() => {
    if (!selectedVariantId && data?.product?.variants?.length && data.product.variants.length > 0) {
      const firstVariantId = data.product.variants[0]?.id;
      if (firstVariantId) {
        setSelectedVariantId(firstVariantId);
      }
    }
  }, [data, selectedVariantId]);

  // Update variant mutation
  const [updateVariant] = useMutation(UpdateVariantDocument);

  // Extract data
  const product = data?.product;
  const variants = product?.variants || [];

  // Filter variants based on search
  const filteredVariants = useMemo(() => {
    if (!searchTerm.trim()) return variants;

    const term = searchTerm.toLowerCase();
    return variants.filter(variant => {
      const searchableText = [
        variant?.option1,
        variant?.option2,
        variant?.option3,
        variant?.sku,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return searchableText.includes(term);
    });
  }, [variants, searchTerm]);

  // Get selected variant
  const selectedVariant = useMemo(() => {
    return variants.find(v => v?.id === selectedVariantId) || null;
  }, [variants, selectedVariantId]);

  // Extract unique option names from product
  const optionNames = useMemo(() => {
    if (!product?.options || product.options.length === 0) return [];
    return product.options as string[];
  }, [product?.options]);

  // Handle variant selection
  const handleSelectVariant = (variantId: string) => {
    setSelectedVariantId(variantId);
    // Update URL without navigation
    window.history.replaceState(
      null,
      '',
      `/workspace/${currentWorkspace?.id}/store/products/${productId}/variants/${variantId}`
    );
  };

  // Handle variant update
  const handleUpdateVariant = async (updateData: any) => {
    if (!selectedVariantId) return;

    setIsSaving(true);
    try {
      const { data: updateData_ } = await updateVariant({
        variables: {
          variantId: selectedVariantId,
          updateData,
        },
      });

      if (updateData_?.updateVariant?.success) {
        toast.success('Variant updated successfully');
        refetch(); // Refresh data
      } else {
        toast.error(updateData_?.updateVariant?.error || 'Failed to update variant');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to update variant');
      console.error('Update variant error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Handle back navigation
  const handleBack = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/inventory`);
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading variants...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !product) {
    return (
      <Card className="p-6">
        <div className="text-center text-destructive">
          <p>Failed to load product</p>
          {error && <p className="text-sm text-muted-foreground">{error.message}</p>}
        </div>
      </Card>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6">
        {/* Left Panel: Variants List */}
        <VariantsList
          product={{
            id: product.id || '',
            name: product.name,
            status: product.status,
            featuredMedia: product.featuredMedia,
          }}
          variants={filteredVariants}
          selectedVariantId={selectedVariantId}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onSelectVariant={handleSelectVariant}
          onBack={handleBack}
          optionNames={optionNames}
        />

        {/* Right Panel: Variant Editor */}
        {selectedVariant ? (
          <VariantEditorForm
            variant={selectedVariant}
            optionNames={optionNames}
            productChargeTax={product.chargeTax}
            onUpdate={handleUpdateVariant}
            isSaving={isSaving}
          />
        ) : (
          <Card className="p-6">
            <div className="text-center text-muted-foreground">
              <p>Select a variant to edit</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
