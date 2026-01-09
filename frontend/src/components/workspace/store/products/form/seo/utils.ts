/**
 * Utility functions for SEO management
 */

import { SEO_LIMITS } from './types';

/**
 * Generate URL-friendly slug from text
 * Converts "My Product Name" to "my-product-name"
 */
export function generateSlug(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special chars
    .replace(/\s+/g, '-')      // Replace spaces with hyphens
    .replace(/--+/g, '-')      // Replace multiple hyphens with single
    .replace(/^-+|-+$/g, '');  // Remove leading/trailing hyphens
}

/**
 * Truncate text to max length
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim();
}

/**
 * Auto-generate meta title from product name
 * Falls back to product name if not set
 */
export function generateMetaTitle(
  productName: string,
  customTitle?: string
): string {
  if (customTitle && customTitle.trim()) {
    return truncateText(customTitle, SEO_LIMITS.TITLE);
  }
  return truncateText(productName, SEO_LIMITS.TITLE);
}

/**
 * Auto-generate meta description from product description
 * Falls back to product description if not set
 */
export function generateMetaDescription(
  productDescription: string,
  customDescription?: string
): string {
  if (customDescription && customDescription.trim()) {
    return truncateText(customDescription, SEO_LIMITS.DESCRIPTION);
  }
  return truncateText(productDescription, SEO_LIMITS.DESCRIPTION);
}

/**
 * Count characters with warning if exceeding limit
 */
export function getCharacterCount(text: string, limit: number): {
  count: number;
  isExceeding: boolean;
  message: string;
} {
  const count = text.length;
  const isExceeding = count > limit;

  return {
    count,
    isExceeding,
    message: `${count} of ${limit} characters used`
  };
}

/**
 * Format full URL for preview
 */
export function formatPreviewUrl(
  baseUrl: string,
  slug: string
): string {
  return `${baseUrl}/products/${slug}`;
}

/**
 * Get URL breadcrumbs for preview
 */
export function getUrlBreadcrumbs(slug: string): string {
  return `products › ${slug}`;
}
