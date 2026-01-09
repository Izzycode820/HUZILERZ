/**
 * Store Domain Routes
 * All public store-related routes
 */

// Public store routes
export const STORE_ROUTES = {
  ROOT: '/store',
  BY_SLUG: (slug: string) => `/store/${slug}`,
  PRODUCT: (slug: string, productId: string) => `/store/${slug}/product/${productId}`,
  CART: (slug: string) => `/store/${slug}/cart`,
  CHECKOUT: (slug: string) => `/store/${slug}/checkout`,
} as const