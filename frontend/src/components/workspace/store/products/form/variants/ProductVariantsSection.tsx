/**
 * ProductVariantsSection Component
 * Main entry point for product variants UI
 *
 * Features:
 * - Toggle-based enable/disable (consistent with inventory/shipping)
 * - Add up to 3 options (like Shopify)
 * - Auto-generate variant combinations
 * - Inline editing of variants
 * - Bulk operations
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Switch } from '@/components/shadcn-ui/switch';
import { Label } from '@/components/shadcn-ui/label';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { AlertTriangle } from 'lucide-react';
import { OptionsForm } from './OptionsForm';
import { VariantsTable } from './VariantsTable';
import type { ProductOption, VariantFormState } from './types';
import { generateVariantCombinations, validateOptionNames } from './utils';

interface ProductVariantsSectionProps {
  // Controlled component - parent manages state
  hasVariants: boolean;
  options: ProductOption[];
  variants: VariantFormState[];
  basePrice?: number;
  onHasVariantsChange: (hasVariants: boolean) => void;
  onOptionsChange: (options: ProductOption[]) => void;
  onVariantsChange: (variants: VariantFormState[]) => void;
}

export function ProductVariantsSection({
  hasVariants,
  options,
  variants,
  basePrice,
  onHasVariantsChange,
  onOptionsChange,
  onVariantsChange
}: ProductVariantsSectionProps) {
  const [validationError, setValidationError] = useState<string | null>(null);

  // Validate option names for duplicates
  useEffect(() => {
    const validation = validateOptionNames(options);
    if (!validation.isValid) {
      setValidationError(
        `Duplicate option name${validation.duplicates.length > 1 ? 's' : ''}: "${validation.duplicates.join('", "')}". Variants with duplicate options will be deleted if you save.`
      );
    } else {
      setValidationError(null);
    }
  }, [options]);

  // Auto-generate variants when options change (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      // Check if we have valid options with values
      const hasValidOptions = options.some(
        opt => opt.optionName.trim() !== "" && opt.optionValues.some(v => v.trim() !== "")
      );

      if (hasValidOptions) {
        const generated = generateVariantCombinations(options, basePrice);
        onVariantsChange(generated);
      } else if (options.length === 0) {
        // Clear variants if no options
        onVariantsChange([]);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options, basePrice]);

  const handleToggleVariants = (enabled: boolean) => {
    onHasVariantsChange(enabled);

    if (enabled && options.length === 0) {
      // Add first empty option when enabling
      onOptionsChange([
        {
          optionName: "",
          optionValues: [""]
        }
      ]);
    } else if (!enabled) {
      // Clear variants when disabling
      onOptionsChange([]);
      onVariantsChange([]);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Variants</CardTitle>
          <div className="flex items-center gap-2">
            <Label htmlFor="has-variants" className="text-sm font-normal cursor-pointer">
              This product has variants
            </Label>
            <Switch
              id="has-variants"
              checked={hasVariants}
              onCheckedChange={handleToggleVariants}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pb-4">
        {hasVariants ? (
          <>
            {/* Options Form */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Options</h3>
              <OptionsForm
                options={options}
                setOptions={onOptionsChange}
              />
            </div>

            {/* Validation Error */}
            {validationError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{validationError}</AlertDescription>
              </Alert>
            )}

            {/* Variants Table - Auto-appears when variants exist */}
            {variants.length > 0 && (
              <div>
                <VariantsTable
                  options={options}
                  variants={variants}
                  setVariants={onVariantsChange}
                />
              </div>
            )}
          </>
        ) : (
          <div className="bg-muted/30 px-3 py-2 rounded-md border">
            <p className="text-xs text-muted-foreground">
              Enable variants if this product comes in multiple options (e.g., size, color, material).
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
