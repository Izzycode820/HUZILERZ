/**
 * Types for Category SEO Section
 */

/**
 * UI State for Category SEO form
 * Tracks both the SEO values and whether the section is expanded
 */
export interface CategorySEOFormState {
  metaTitle: string
  metaDescription: string
  slug: string
  isEditing: boolean // Track if edit mode is active
}

/**
 * Character limits for SEO fields (Google recommendations)
 */
export const SEO_LIMITS = {
  TITLE: 70,
  DESCRIPTION: 160,
} as const
