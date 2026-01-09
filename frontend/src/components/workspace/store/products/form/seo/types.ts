/**
 * Types for Product SEO Section
 * Re-exports from generated GraphQL types
 */

import type { SeoInput } from '@/types/workspace/store/graphql-base';

// Re-export generated type
export type { SeoInput };

/**
 * UI State for SEO form
 * Tracks both the SEO values and whether the section is expanded
 */
export interface SEOFormState {
  metaTitle: string;
  metaDescription: string;
  slug: string;
  isEditing: boolean; // Track if edit mode is active
}

/**
 * Character limits for SEO fields (Google recommendations)
 */
export const SEO_LIMITS = {
  TITLE: 70,
  DESCRIPTION: 160,
} as const;
