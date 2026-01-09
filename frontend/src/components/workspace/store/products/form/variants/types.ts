/**
 * Types for Product Variants UI
 * Re-exports from generated GraphQL types with UI-specific extensions
 */

import type {
  ProductVariantOptionInput,
  VariantInput,
  ProductVariantType
} from '@/types/workspace/store/graphql-base';

// Re-export generated types
export type { ProductVariantOptionInput, VariantInput, ProductVariantType };

/**
 * UI-friendly type alias for ProductOption
 * Maps to ProductVariantOptionInput but with clearer naming for UI
 */
export interface ProductOption {
  optionName: string;        // "Color", "Size", "Storage"
  optionValues: string[];    // ["Blue", "Black", "White"]
  isCollapsed?: boolean;     // UI state: whether option form is collapsed
}

/**
 * Helper to convert UI ProductOption to GraphQL ProductVariantOptionInput
 */
export function toProductVariantOptionInput(option: ProductOption): ProductVariantOptionInput {
  return {
    optionName: option.optionName,
    optionValues: option.optionValues
  };
}

/**
 * Helper to convert GraphQL ProductVariantOptionInput to UI ProductOption
 */
export function fromProductVariantOptionInput(input: ProductVariantOptionInput): ProductOption {
  return {
    optionName: input.optionName,
    optionValues: input.optionValues.filter((v): v is string => v !== null && v !== undefined)
  };
}

import type { MediaItem } from '@/components/workspace/store/shared/files-and-media';

/**
 * UI State type for managing variant form
 * Extends VariantInput with local UI state and hierarchical structure
 */
export interface VariantFormState extends Omit<VariantInput, 'inventory' | 'images' | 'featuredMediaId'> {
  // Local UI-only fields
  inventoryQuantity?: number;
  mediaItem?: MediaItem;  // UI-only: manages variant image
  featuredMediaId?: string;  // Backend: upload ID for variant image

  // Keep all VariantInput fields
  option1?: string;
  option2?: string;
  option3?: string;
  price?: number;
  costPrice?: number;
  compareAtPrice?: number;
  isActive?: boolean;
  position?: number;

  // Hierarchical structure fields
  parentId?: string;  // ID of parent variant (for nesting)
  children?: VariantFormState[];  // Child variants
  isExpanded?: boolean;  // For UI collapse/expand
  level?: number;  // 0 = option1, 1 = option2, 2 = option3
  id?: string;  // Unique ID for this variant
}
