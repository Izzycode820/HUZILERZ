/**
 * Theme Configuration for Sneakers Theme
 * Defines theme metadata, capabilities, and registered pages
 * Used by backend to understand theme features and tier
 */

export const themeConfig = {
  // Theme Metadata
  name: "Sneakers Theme",
  slug: "sneakers",
  version: "1.0.0",
  tier: "free", // free | paid | exclusive

  // Compatible workspace types
  compatibleWorkspaceTypes: ["store"],

  // Theme Capabilities (Free Tier)
  capabilities: {
    hasPaymentCheckout: false,        // Free: WhatsApp only
    hasWhatsAppCheckout: true,        // All tiers: true
    supportsVariants: true,           // Theme-specific feature
    showsRegionalInventory: false,    // Exclusive only
    hasDiscountBanners: false,        // Paid/Exclusive
    hasAdvancedFilters: false,        // Exclusive only
  },

  // Registered Pages
  pages: {
    // Puck-Editable Pages
    home: {
      editable: true,
      puckDataFile: "puck.data.json",
      route: "/",
      description: "Home page with customizable sections",
    },

    // Functional Pages (Not Puck-editable)
    products: {
      editable: false,
      route: "/products",
      description: "All products listing page",
    },

    collections: {
      editable: false,
      route: "/collections/[slug]",
      description: "Collection-filtered products page",
    },

    productDetail: {
      editable: false,
      route: "/products/[slug]",
      description: "Single product detail page",
    },

    cart: {
      editable: false,
      route: "/cart",
      description: "Shopping cart page",
    },

    checkout: {
      editable: false,
      route: "/checkout",
      description: "WhatsApp checkout page",
    },
  },

  // Puck Sections Registry
  sections: {
    HeroSection: {
      name: "Hero Banner",
      category: "content",
      locked: false,
    },
    CollectionSection_A: {
      name: "Collection Display A",
      category: "commerce",
      locked: true, // Only collection slug is editable
      description: "Horizontal grid with 6 products",
    },
    CollectionSection_B: {
      name: "Collection Display B",
      category: "commerce",
      locked: true,
      description: "Horizontal scrolling carousel",
    },
    SaleBannerSection: {
      name: "Sale Banner",
      category: "content",
      locked: false,
    },
    CategoriesSection: {
      name: "Categories Browser",
      category: "commerce",
      locked: false,
      description: "Sidebar categories with product grid",
    },
  },

  // Demo Configuration
  demo: {
    storeSlug: "sneakers-demo",
    collections: ["sneakers-demo", "new-arrivals-demo"],
  },

  // Feature Flags
  features: {
    customerAccounts: false,      // Future feature
    wishlist: false,              // Future feature
    productReviews: false,        // Future feature
    analytics: false,             // Future feature
  },
};

export type ThemeConfig = typeof themeConfig;
export default themeConfig;
