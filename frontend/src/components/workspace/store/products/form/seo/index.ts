/**
 * SEO Module Exports
 * Clean public API for the SEO section
 */

export { ProductSEOSection } from './ProductSEOSection';

export type { SeoInput, SEOFormState } from './types';
export { SEO_LIMITS } from './types';

export {
  generateSlug,
  truncateText,
  generateMetaTitle,
  generateMetaDescription,
  getCharacterCount,
  formatPreviewUrl,
  getUrlBreadcrumbs,
} from './utils';
