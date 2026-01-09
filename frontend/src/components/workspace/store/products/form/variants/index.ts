/**
 * Variants Module Exports
 * Clean public API for the variants UI
 */

export { ProductVariantsSection } from './ProductVariantsSection';
export { OptionsForm } from './OptionsForm';
export { OptionCard } from './OptionCard';
export { VariantsTable } from './VariantsTable';
export { VariantEditModal } from './VariantEditModal';

export type {
  ProductOption,
  VariantFormState,
  ProductVariantOptionInput,
  VariantInput,
  ProductVariantType
} from './types';

export {
  generateVariantCombinations,
  getVariantDisplayName,
  groupVariantsByOption,
  generateSKU,
  hasOptionsChanged,
  isLeafVariant,
  getVariantLevelValue,
  validateOptionNames,
  flattenVariantsForMutation,
  extractOptionsFromVariants
} from './utils';
