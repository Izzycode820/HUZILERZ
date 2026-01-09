/**
 * Types for Product Organization Section
 * Re-exports from generated GraphQL types
 */

import type { OrganizationInput } from '@/types/workspace/store/graphql-base';
import type { CategoryPickerQuery } from '@/services/graphql/admin-store/queries/categories/__generated__/CategoryPicker.generated';

// Re-export generated type
export type { OrganizationInput };

/**
 * UI State for Organization form
 */
export interface OrganizationFormState {
  productType: string;
  vendor: string;
  categoryId: string;
  tags: string[];
}

/**
 * Category option for dropdown (extracted from CategoryPickerQuery)
 */
export type CategoryOption = NonNullable<
  NonNullable<
    NonNullable<CategoryPickerQuery['categories']>['edges'][number]
  >['node']
>;
