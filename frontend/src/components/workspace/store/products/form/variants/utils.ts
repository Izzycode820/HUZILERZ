/**
 * Utility functions for variant generation and management
 * Updated to use generated GraphQL types
 */

import type { ProductOption, VariantFormState } from './types';

/**
 * Generate hierarchical nested variants from product options
 * Creates parent-child relationships instead of combinations
 *
 * With 2 options:
 * - Option1Value1 (parent) → Option2Value1, Option2Value2 (children)
 *
 * With 3 options (SPECIAL: skip middle level):
 * - Option1Value1 (parent) → Option2Value1/Option3Value1, Option2Value1/Option3Value2 (combined children)
 */
export function generateVariantCombinations(
  options: ProductOption[],
  basePrice?: number
): VariantFormState[] {
  if (options.length === 0) return [];

  // Filter out empty values and options
  const validOptions = options
    .filter(opt => opt.optionValues.length > 0)
    .map(opt => ({
      ...opt,
      optionValues: opt.optionValues.filter(v => v.trim() !== "")
    }))
    .filter(opt => opt.optionValues.length > 0);

  if (validOptions.length === 0) return [];

  const variants: VariantFormState[] = [];
  let variantIdCounter = 0;

  // Special handling for 3 options - skip middle level
  if (validOptions.length === 3) {
    validOptions[0].optionValues.forEach((value1) => {
      const parentId = `variant-${variantIdCounter++}`;
      const children: VariantFormState[] = [];

      // Generate combined children (Op2/Op3)
      validOptions[1].optionValues.forEach((value2) => {
        validOptions[2].optionValues.forEach((value3) => {
          const childId = `variant-${variantIdCounter++}`;
          children.push({
            id: childId,
            option1: value1,
            option2: value2,
            option3: value3,
            price: basePrice,
            costPrice: undefined,
            compareAtPrice: undefined,
            isActive: true,
            position: children.length,
            inventoryQuantity: 0,
            parentId: parentId,
            children: [],
            isExpanded: true,
            level: 1 // Direct children of Op1
          });
        });
      });

      // Create parent (Op1)
      variants.push({
        id: parentId,
        option1: value1,
        price: basePrice,
        costPrice: undefined,
        compareAtPrice: undefined,
        isActive: true,
        position: variants.length,
        inventoryQuantity: 0,
        parentId: undefined,
        children: children,
        isExpanded: true,
        level: 0
      });
    });

    return variants;
  }

  // Standard hierarchical build for 1 or 2 options
  function buildHierarchy(
    optionIndex: number,
    parentVariant: VariantFormState | null,
    parentId: string | undefined,
    inheritedValues: { option1?: string; option2?: string; option3?: string }
  ) {
    if (optionIndex >= validOptions.length) return;

    const currentOption = validOptions[optionIndex];

    currentOption.optionValues.forEach((value) => {
      const variantId = `variant-${variantIdCounter++}`;
      const level = optionIndex;

      // Build option values based on level
      const optionValues = { ...inheritedValues };
      if (level === 0) optionValues.option1 = value;
      if (level === 1) optionValues.option2 = value;
      if (level === 2) optionValues.option3 = value;

      const variant: VariantFormState = {
        id: variantId,
        ...optionValues,
        price: basePrice,
        costPrice: undefined,
        compareAtPrice: undefined,
        isActive: true,
        position: variants.length,
        inventoryQuantity: 0,
        parentId: parentId,
        children: [],
        isExpanded: true,
        level: level
      };

      // Add to parent's children or to root variants array
      if (parentVariant) {
        parentVariant.children = parentVariant.children || [];
        parentVariant.children.push(variant);
      } else {
        variants.push(variant);
      }

      // Recursively build children for next option level
      buildHierarchy(optionIndex + 1, variant, variantId, optionValues);
    });
  }

  // Start building from option 1
  buildHierarchy(0, null, undefined, {});

  return variants;
}

/**
 * Get human-readable variant name
 */
export function getVariantDisplayName(variant: VariantFormState | { option1?: string; option2?: string; option3?: string }): string {
  const parts = [
    variant.option1,
    variant.option2,
    variant.option3
  ].filter(Boolean);

  return parts.length > 0 ? parts.join(" / ") : "Default";
}

/**
 * Check if a variant is a leaf node (has no children)
 */
export function isLeafVariant(variant: VariantFormState): boolean {
  return !variant.children || variant.children.length === 0;
}

/**
 * Get the display value for a variant based on its level
 * For 3 options: level 1 children show "Op2 / Op3" combined format
 */
export function getVariantLevelValue(variant: VariantFormState): string {
  // Level 0: Show option1 value
  if (variant.level === 0) return variant.option1 || '';

  // Level 1: Check if this is a combined Op2/Op3 (has option3)
  if (variant.level === 1) {
    if (variant.option3) {
      // Combined format for 3-option structure
      const parts = [variant.option2, variant.option3].filter(Boolean);
      return parts.join(' / ');
    }
    // Regular 2-option structure
    return variant.option2 || '';
  }

  // Level 2: Show combined format (shouldn't happen with new 3-option structure)
  if (variant.level === 2) {
    const parts = [variant.option2, variant.option3].filter(Boolean);
    return parts.join(' / ');
  }

  return variant.option3 || '';
}

/**
 * Validate option names for duplicates
 */
export function validateOptionNames(options: ProductOption[]): {
  isValid: boolean;
  duplicates: string[]
} {
  const names = options
    .map(opt => opt.optionName.trim().toLowerCase())
    .filter(name => name !== '');

  const duplicates = names.filter((name, index) => names.indexOf(name) !== index);
  const uniqueDuplicates = Array.from(new Set(duplicates));

  return {
    isValid: uniqueDuplicates.length === 0,
    duplicates: uniqueDuplicates
  };
}

/**
 * Flatten hierarchical variants to flat array for mutation (Shopify-style)
 * Extracts ONLY leaf nodes (sellable variants) for backend
 *
 * @param hierarchicalVariants - Tree structure from UI state
 * @returns Flat array of leaf variants ready for GraphQL mutation
 */
export function flattenVariantsForMutation(hierarchicalVariants: VariantFormState[]): any[] {
  const leafVariants: any[] = [];

  function extractLeaves(variants: VariantFormState[]) {
    variants.forEach(variant => {
      // Only extract leaf nodes (variants with no children)
      if (isLeafVariant(variant)) {
        leafVariants.push({
          // Option values
          option1: variant.option1 || '',
          option2: variant.option2 || '',
          option3: variant.option3 || '',

          // Pricing (preserve user-entered values)
          price: variant.price,
          compare_at_price: variant.compareAtPrice,
          cost_price: variant.costPrice,

          // Status and position
          is_active: variant.isActive ?? true,
          position: variant.position ?? 0,

          // Inventory fields (from VariantEditModal)
          sku: (variant as any).sku || '',
          barcode: (variant as any).barcode || '',
          inventoryQuantity: variant.inventoryQuantity ?? 0,

          // Featured media ID (from upload-first system)
          featuredMediaId: variant.featuredMediaId || null,
        });
      }

      // Recursively extract from children
      if (variant.children && variant.children.length > 0) {
        extractLeaves(variant.children);
      }
    });
  }

  extractLeaves(hierarchicalVariants);
  return leafVariants;
}

/**
 * Extract unique option names and values from variants for mutation
 * Reconstructs options array from variant data
 *
 * @param variants - Array of variants
 * @returns Array of {optionName, optionValues} for mutation
 */
export function extractOptionsFromVariants(
  options: ProductOption[]
): Array<{ option_name: string; option_values: string[] }> {
  return options.map(opt => ({
    option_name: opt.optionName,
    option_values: opt.optionValues.filter(v => v.trim() !== '')
  }));
}

/**
 * Group variants by a specific option
 */
export function groupVariantsByOption(
  variants: VariantFormState[],
  groupBy: 'option1' | 'option2' | 'option3'
): Map<string, VariantFormState[]> {
  const grouped = new Map<string, VariantFormState[]>();

  variants.forEach(variant => {
    const key = variant[groupBy] || "No value";
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key)!.push(variant);
  });

  return grouped;
}

/**
 * Auto-generate SKU from variant options
 */
export function generateSKU(
  productName: string,
  variant: VariantFormState,
  index: number
): string {
  const parts = [
    productName.substring(0, 3).toUpperCase(),
    variant.option1?.substring(0, 3).toUpperCase(),
    variant.option2?.substring(0, 3).toUpperCase(),
    variant.option3?.substring(0, 3).toUpperCase(),
  ].filter(Boolean);

  return parts.length > 1 ? parts.join("-") : `SKU-${index + 1}`;
}

/**
 * Validate if options have changed (to regenerate variants)
 */
export function hasOptionsChanged(
  oldOptions: ProductOption[],
  newOptions: ProductOption[]
): boolean {
  if (oldOptions.length !== newOptions.length) return true;

  return oldOptions.some((oldOpt, index) => {
    const newOpt = newOptions[index];
    if (oldOpt.optionName !== newOpt.optionName) return true;
    if (oldOpt.optionValues.length !== newOpt.optionValues.length) return true;
    return oldOpt.optionValues.some((val, i) => val !== newOpt.optionValues[i]);
  });
}
