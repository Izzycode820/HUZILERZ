/**
 * Workspace Domain Routes
 * All admin workspace routes - Single source of truth
 * Pattern: /workspace/[workspace_id]/[workspace_type]/[section]
 */

// Base workspace routes
export const WORKSPACE_ROUTES = {
  ROOT: '/workspace',
  CREATE: '/workspace/create',

  // Generic workspace dashboard
  DASHBOARD: (workspaceId: string) => `/workspace/${workspaceId}`,
} as const

// ============================================================================
// STORE WORKSPACE ROUTES (Shopify-inspired structure)
// ============================================================================
export const STORE_ROUTES = {
  // Dashboard (Home)
  HOME: (workspaceId: string) => `/workspace/${workspaceId}/store`,

  // Products (Shopify-exact structure)
  PRODUCTS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/store/products`,
    NEW: (workspaceId: string) => `/workspace/${workspaceId}/store/products/new`,
    EDIT: (workspaceId: string, productId: string) => `/workspace/${workspaceId}/store/products/${productId}`,
    INVENTORY: (workspaceId: string) => `/workspace/${workspaceId}/store/products/inventory`,
    COLLECTIONS: (workspaceId: string) => `/workspace/${workspaceId}/store/products/categories`,
    TRANSFERS: (workspaceId: string) => `/workspace/${workspaceId}/store/products/transfers`,
    GIFT_CARDS: (workspaceId: string) => `/workspace/${workspaceId}/store/products/gift-cards`,
  },

  // Orders
  ORDERS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/store/orders`,
    VIEW: (workspaceId: string, orderId: string) =>
      `/workspace/${workspaceId}/store/orders/${orderId}`,
    DRAFTS: (workspaceId: string) => `/workspace/${workspaceId}/store/orders/drafts`,
  },

  // Customers (Shopify-exact: no sub-menu)
  CUSTOMERS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/store/customers`,
    VIEW: (workspaceId: string, customerId: string) =>
      `/workspace/${workspaceId}/store/customers/${customerId}`,
  },

  // Content (Shopify-exact: blog posts, pages, files)
  // CONTENT: {
  //   BLOG_POSTS: (workspaceId: string) => `/workspace/${workspaceId}/store/content/blog-posts`,
  //   PAGES: (workspaceId: string) => `/workspace/${workspaceId}/store/content/pages`,
  //   FILES: (workspaceId: string) => `/workspace/${workspaceId}/store/content/files`,
  // },

  // Analytics (Shopify-exact: no sub-menu in sidebar)
  ANALYTICS: {
    OVERVIEW: (workspaceId: string) => `/workspace/${workspaceId}/store/analytics`,
    REPORTS: (workspaceId: string) => `/workspace/${workspaceId}/store/analytics/reports`,
  },

  // Marketing (Shopify-exact: campaigns, automations)
  // MARKETING: {
  //   OVERVIEW: (workspaceId: string) => `/workspace/${workspaceId}/store/themes`,
  //   CAMPAIGNS: (workspaceId: string) => `/workspace/${workspaceId}/store/marketing/campaigns`,
  //   AUTOMATIONS: (workspaceId: string) => `/workspace/${workspaceId}/store/marketing/automations`,
  // },

  // Discounts (Shopify-exact: no sub-menu)
  DISCOUNTS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/store/discounts`,
    NEW: (workspaceId: string) => `/workspace/${workspaceId}/store/discounts/new`,
  },

  // Sales Channels (Shopify-exact: Online Store, Shop, Point of Sale)
  CHANNELS: {
    ONLINE_STORE: (workspaceId: string) => `/workspace/${workspaceId}/store/themes`,
    THEMES: (workspaceId: string) => `/workspace/${workspaceId}/store/themes`,
    PAGES: (workspaceId: string) => `/workspace/${workspaceId}/store/pages`,
    PREFERENCES: (workspaceId: string) => `/workspace/${workspaceId}/store/themes/preferences`,
    // SHOP: (workspaceId: string) => `/workspace/${workspaceId}/store/channels/shop`,
    // POINT_OF_SALE: (workspaceId: string) => `/workspace/${workspaceId}/store/channels/pos`,
  },

  // Apps
  APPS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/store/apps`,
  },

  // Settings
  SETTINGS: {
    GENERAL: (workspaceId: string) => `/workspace/${workspaceId}/store/settings/domains`,
    PAYMENTS: (workspaceId: string) => `/workspace/${workspaceId}/store/settings/payments`,
    SHIPPING: (workspaceId: string) => `/workspace/${workspaceId}/store/settings/shipping`,
    TAXES: (workspaceId: string) => `/workspace/${workspaceId}/store/settings/taxes`,
    CHECKOUT: (workspaceId: string) => `/workspace/${workspaceId}/store/settings/checkout`,
  },
} as const

// ============================================================================
// SERVICES WORKSPACE ROUTES
// ============================================================================
export const SERVICES_ROUTES = {
  HOME: (workspaceId: string) => `/workspace/${workspaceId}/services`,

  SERVICES: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/services/services`,
    NEW: (workspaceId: string) => `/workspace/${workspaceId}/services/services/new`,
  },

  BOOKINGS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/services/bookings`,
    CALENDAR: (workspaceId: string) => `/workspace/${workspaceId}/services/bookings/calendar`,
  },

  CLIENTS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/services/clients`,
  },

  SETTINGS: {
    GENERAL: (workspaceId: string) => `/workspace/${workspaceId}/services/settings`,
  },
} as const

// ============================================================================
// BLOG WORKSPACE ROUTES
// ============================================================================
export const BLOG_ROUTES = {
  HOME: (workspaceId: string) => `/workspace/${workspaceId}/blog`,

  POSTS: {
    LIST: (workspaceId: string) => `/workspace/${workspaceId}/blog/posts`,
    NEW: (workspaceId: string) => `/workspace/${workspaceId}/blog/posts/new`,
    EDIT: (workspaceId: string, postId: string) =>
      `/workspace/${workspaceId}/blog/posts/${postId}`,
  },

  CONTENT: {
    MEDIA: (workspaceId: string) => `/workspace/${workspaceId}/blog/content/media`,
  },

  MONETIZATION: {
    OVERVIEW: (workspaceId: string) => `/workspace/${workspaceId}/blog/monetization`,
  },

  SETTINGS: {
    GENERAL: (workspaceId: string) => `/workspace/${workspaceId}/blog/settings`,
  },
} as const

// ============================================================================
// RESTAURANT WORKSPACE ROUTES (Future)
// ============================================================================
export const RESTAURANT_ROUTES = {
  HOME: (workspaceId: string) => `/workspace/${workspaceId}/restaurant`,
  // TODO: Add restaurant routes
} as const
