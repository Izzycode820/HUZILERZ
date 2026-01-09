/**
 * Utility functions for Category SEO management
 */

import { SEO_LIMITS } from './types'

/**
 * Generate URL-friendly slug from text
 * Converts "My Category Name" to "my-category-name"
 */
export function generateSlug(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special chars
    .replace(/\s+/g, '-')      // Replace spaces with hyphens
    .replace(/--+/g, '-')      // Replace multiple hyphens with single
    .replace(/^-+|-+$/g, '')   // Remove leading/trailing hyphens
}

/**
 * Truncate text to max length
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trim()
}

/**
 * Strip HTML tags from rich text content
 * Converts "<p>Hello <strong>World</strong></p>" to "Hello World"
 */
export function stripHtmlTags(html: string): string {
  return html
    .replace(/<[^>]*>/g, '') // Remove HTML tags
    .replace(/\s+/g, ' ')    // Normalize whitespace
    .trim()
}

/**
 * Auto-generate meta title from category name
 * Falls back to category name if not set
 */
export function generateMetaTitle(
  categoryName: string,
  customTitle?: string
): string {
  if (customTitle && customTitle.trim()) {
    return truncateText(customTitle, SEO_LIMITS.TITLE)
  }
  return truncateText(categoryName, SEO_LIMITS.TITLE)
}

/**
 * Auto-generate meta description from category description
 * Falls back to category description if not set
 * Strips HTML tags since description uses rich text editor
 */
export function generateMetaDescription(
  categoryDescription: string,
  customDescription?: string
): string {
  if (customDescription && customDescription.trim()) {
    return truncateText(customDescription, SEO_LIMITS.DESCRIPTION)
  }

  // Strip HTML tags from rich text description
  const plainText = stripHtmlTags(categoryDescription)
  return truncateText(plainText, SEO_LIMITS.DESCRIPTION)
}

/**
 * Count characters with warning if exceeding limit
 */
export function getCharacterCount(text: string, limit: number): {
  count: number
  isExceeding: boolean
  message: string
} {
  const count = text.length
  const isExceeding = count > limit

  return {
    count,
    isExceeding,
    message: `${count} of ${limit} characters used`
  }
}

/**
 * Format full URL for preview
 */
export function formatPreviewUrl(
  baseUrl: string,
  slug: string
): string {
  return `${baseUrl}/collections/${slug}`
}

/**
 * Get URL breadcrumbs for preview
 */
export function getUrlBreadcrumbs(slug: string): string {
  return `collections › ${slug}`
}
