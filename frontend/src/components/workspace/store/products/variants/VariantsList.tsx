'use client';

/**
 * Variants List (Left Panel)
 *
 * Shopify-style variant selector:
 * - Product header with image and status
 * - Search input
 * - Clickable variant list
 */

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Button } from '@/components/shadcn-ui/button';
import { Badge } from '@/components/shadcn-ui/badge';
import { Search, ArrowLeft, Package } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VariantsListProps {
  product: {
    id: string;
    name: string;
    status: string;
    featuredMedia?: {
      thumbnailUrl?: string | null;
      url?: string | null;
    } | null;
  };
  variants: any[];
  selectedVariantId: string | null;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onSelectVariant: (variantId: string) => void;
  onBack: () => void;
  optionNames: string[];
}

export function VariantsList({
  product,
  variants,
  selectedVariantId,
  searchTerm,
  onSearchChange,
  onSelectVariant,
  onBack,
  optionNames,
}: VariantsListProps) {
  return (
    <Card className="h-fit sticky top-4">
      <CardHeader className="space-y-4">
        {/* Back Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="w-fit -ml-2"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Inventory
        </Button>

        {/* Product Header */}
        <div className="flex items-start gap-3">
          {/* Product Image */}
          <div className="flex-shrink-0 w-14 h-14 bg-muted rounded-lg overflow-hidden border">
            {product.featuredMedia?.thumbnailUrl || product.featuredMedia?.url ? (
              <img
                src={product.featuredMedia.thumbnailUrl || product.featuredMedia.url || ''}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Package className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
          </div>

          {/* Product Info */}
          <div className="flex-1 min-w-0">
            <h2 className="font-semibold text-base truncate">{product.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <Badge
                variant={product.status === 'published' ? 'default' : 'secondary'}
                className="text-xs"
              >
                {product.status === 'published' ? 'Active' : product.status}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {variants.length} variant{variants.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search variants"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9"
          />
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Variant Count */}
        <p className="text-sm text-muted-foreground mb-3">
          {variants.length} variant{variants.length !== 1 ? 's' : ''}
        </p>

        {/* Variants List */}
        <div className="space-y-1">
          {variants.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No variants found
            </div>
          ) : (
            variants.map((variant) => {
              const isSelected = variant?.id === selectedVariantId;
              const options = [
                variant?.option1,
                variant?.option2,
                variant?.option3,
              ].filter(Boolean);

              return (
                <button
                  key={variant?.id}
                  onClick={() => onSelectVariant(variant?.id)}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors',
                    isSelected
                      ? 'bg-primary/10 border-2 border-primary'
                      : 'hover:bg-muted border-2 border-transparent'
                  )}
                >
                  {/* Variant Image/Icon */}
                  <div className="flex-shrink-0 w-10 h-10 bg-muted rounded overflow-hidden border">
                    {variant?.featuredMedia?.thumbnailUrl || variant?.featuredMedia?.url ? (
                      <img
                        src={variant.featuredMedia.thumbnailUrl || variant.featuredMedia.url}
                        alt={options.join(' / ')}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="h-5 w-5 text-muted-foreground" />
                      </div>
                    )}
                  </div>

                  {/* Variant Options */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {options.join(' / ')}
                    </p>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}
