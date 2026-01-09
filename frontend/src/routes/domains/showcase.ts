/**
 * Showcase Domain Routes
 * Theme store and template showcase routes
 */

// Showcase routes
export const SHOWCASE_ROUTES = {
  ROOT: '/showcase',
  THEME_DETAIL: (themeId: string) => `/showcase/theme/${themeId}`,
  CATEGORY: (category: string) => `/showcase/category/${category}`,
  SEARCH: (query: string) => `/showcase/search?q=${encodeURIComponent(query)}`,
} as const