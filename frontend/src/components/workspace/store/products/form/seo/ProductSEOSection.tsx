/**
 * ProductSEOSection Component
 *
 * Features:
 * - Collapsed preview showing search engine listing
 * - Auto-populates from product name and description
 * - Expands to show editable fields
 * - Character count validation
 * - Real-time slug generation
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Button } from '@/components/shadcn-ui/button';
import { Edit2 } from 'lucide-react';
import { SEO_LIMITS } from './types';
import {
  generateSlug,
  generateMetaTitle,
  generateMetaDescription,
  getCharacterCount,
  getUrlBreadcrumbs,
} from './utils';

interface ProductSEOSectionProps {
  // Auto-populated from main form
  productName: string;
  productDescription: string;
  productPrice?: number;

  // Controlled SEO values
  metaTitle: string;
  metaDescription: string;
  slug: string;

  // Change handlers
  onMetaTitleChange: (value: string) => void;
  onMetaDescriptionChange: (value: string) => void;
  onSlugChange: (value: string) => void;
}

export function ProductSEOSection({
  productName,
  productDescription,
  productPrice,
  metaTitle,
  metaDescription,
  slug,
  onMetaTitleChange,
  onMetaDescriptionChange,
  onSlugChange,
}: ProductSEOSectionProps) {
  const [isEditing, setIsEditing] = useState(false);

  // Auto-generate slug from product name when name changes (only if slug is empty)
  useEffect(() => {
    if (productName && !slug) {
      onSlugChange(generateSlug(productName));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productName]); // Only when productName changes, not onSlugChange

  // Display values (use utility functions for proper truncation)
  const displayTitle = generateMetaTitle(productName, metaTitle);
  const displayDescription = generateMetaDescription(productDescription, metaDescription);
  const displaySlug = slug || generateSlug(productName) || 'product-slug';

  // Character counts
  const titleCount = getCharacterCount(metaTitle || productName, SEO_LIMITS.TITLE);
  const descCount = getCharacterCount(metaDescription || productDescription, SEO_LIMITS.DESCRIPTION);

  const handleSlugChange = (value: string) => {
    // Auto-format slug as user types
    const formatted = generateSlug(value);
    onSlugChange(formatted);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Search engine listing</CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsEditing(!isEditing)}
          >
            <Edit2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Preview Card */}
        <div className="border rounded-lg p-4 bg-muted/30 space-y-2">
          <p className="text-sm text-muted-foreground">My Store</p>
          <p className="text-xs text-muted-foreground">
            {getUrlBreadcrumbs(displaySlug)}
          </p>
          <h3 className="text-blue-600 font-medium text-lg hover:underline cursor-pointer">
            {displayTitle}
          </h3>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {displayDescription}
          </p>
          {productPrice !== undefined && productPrice > 0 && (
            <p className="text-sm font-medium">
              FCFA {productPrice.toLocaleString()} XAF
            </p>
          )}
        </div>

        {/* Editable Fields (shown when editing) */}
        {isEditing && (
          <div className="space-y-4 pt-4 border-t">
            {/* Page Title */}
            <div className="space-y-2">
              <Label htmlFor="meta-title">Page title</Label>
              <Input
                id="meta-title"
                placeholder={productName || "Enter product name first"}
                value={metaTitle}
                onChange={(e) => onMetaTitleChange(e.target.value)}
                maxLength={SEO_LIMITS.TITLE}
              />
              <p className={`text-xs ${titleCount.isExceeding ? 'text-destructive' : 'text-muted-foreground'}`}>
                {titleCount.message}
              </p>
            </div>

            {/* Meta Description */}
            <div className="space-y-2">
              <Label htmlFor="meta-description">Meta description</Label>
              <Textarea
                id="meta-description"
                placeholder={productDescription || "Enter product description first"}
                value={metaDescription}
                onChange={(e) => onMetaDescriptionChange(e.target.value)}
                maxLength={SEO_LIMITS.DESCRIPTION}
                rows={3}
              />
              <p className={`text-xs ${descCount.isExceeding ? 'text-destructive' : 'text-muted-foreground'}`}>
                {descCount.message}
              </p>
            </div>

            {/* URL Handle */}
            <div className="space-y-2">
              <Label htmlFor="url-handle">URL handle</Label>
              <Input
                id="url-handle"
                placeholder="product-slug"
                value={slug}
                onChange={(e) => handleSlugChange(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                https://mystore.com/products/{displaySlug}
              </p>
            </div>
          </div>
        )}

        {/* Info text when not editing */}
        {!isEditing && (
          <p className="text-xs text-muted-foreground">
            Add a title and description to see how this product might appear in a search engine listing.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
