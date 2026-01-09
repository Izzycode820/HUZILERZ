import type { Config } from "@measured/puck";
import React from 'react';

// Section Imports
import NavBar from "./src/components/sections/NavBar";
import HeroSection from "./src/components/sections/HeroSection";
import TwoColumnCollections from "./src/components/sections/TwoColumnCollections/TwoColumnCollections";
import SaleBannerSection from "./src/components/sections/SaleBannerSection";
import FeaturedProducts from "./src/components/sections/FeaturedProducts/FeaturedProducts";
import Footer from "./src/components/sections/Footer";
import CollectionSlider from "./src/components/sections/CollectionSlider/CollectionSlider";

// No custom field imports needed - registered via fieldTypes override in editor

// Types for section props
type DataContract = {
  type: string;
  resolver: string;
};

type NavLink = {
  label: string;
  href: string;
};

type NavBarProps = {
  storeName: string;
  logoUrl?: string;
  links: NavLink[];
  alignment?: 'left' | 'center' | 'right';
  showSearch?: boolean;
  showCart?: boolean;
  dataContract?: DataContract;
  storeSlug?: string; // Added to match resolveData injection
  categories?: Array<{
    id: string;
    name: string;
    slug: string;
  }>;
};

type HeroSectionProps = {
  headline: string;
  description: string;
  ctaText: string;
  ctaLink?: string;
  mediaType?: 'image' | 'video';
  mediaUrl: string;
  videoUrl?: string;
  overlayOpacity?: number;
  textAlignment?: 'left' | 'center' | 'right';
};

type SaleBannerSectionProps = {
  headline: string;
  description: string;
  offerText: string;
  ctaText: string;
  ctaLink?: string;
  backgroundImage: string;
  overlayOpacity?: number;
};

type CollectionSliderProps = {
  title: string;
  limit?: number;
  viewMoreText?: string;
  dataContract?: DataContract;
  categories?: Array<{
    id: string;
    name: string;
    slug: string;
    image?: string | null;
  }>;
};

type FeaturedProductsProps = {
  title: string;
  categorySlug: string;
  limit?: number;
  viewMoreText?: string;
  dataContract?: DataContract;
  storeSlug?: string; // Added to match resolveData injection
  products?: {
    id: string;
    name: string;
    slug: string;
    price: string;
    compareAtPrice?: string | null;
    mediaUploads?: Array<{
      optimizedWebp?: string | null;
      thumbnailWebp?: string | null;
    }>;
  }[];
};

type TwoColumnCollectionsProps = {
  title?: string;
  collection1Slug?: string;
  collection2Slug?: string;
  dataContract?: DataContract;
  categories?: {
    id: string;
    name: string;
    slug: string;
    image?: string | null;
    products?: Array<any>;
  }[];
};

type FooterLink = {
  label: string;
  href: string;
};

type FooterColumn = {
  title: string;
  links: FooterLink[];
};

type SocialLink = {
  platform: string;
  url: string;
  icon: string;
};

type FooterProps = {
  storeName: string;
  description?: string;
  columns?: FooterColumn[];
  socialLinks?: SocialLink[];
  copyrightText?: string;
  showPaymentMethods?: boolean;
};

// Define a map of all component props
type PropsMap = {
  NavBar: NavBarProps;
  HeroSection: HeroSectionProps;
  CollectionSlider: CollectionSliderProps;
  SaleBannerSection: SaleBannerSectionProps;
  FeaturedProducts: FeaturedProductsProps;
  NewArrivals: FeaturedProductsProps; // Reuses FeaturedProductsProps
  TwoColumnCollections: TwoColumnCollectionsProps;
  Footer: FooterProps;
};

// Custom Type Definitions for Extended Functionality
type BaseComponentConfig = Config["components"][string];

type CustomField = {
  type: string;
  label?: string;
  min?: number;
  max?: number;
  unit?: string;
  options?: { label: string; value: any }[];
  arrayFields?: Record<string, CustomField>;
  [key: string]: any;
};

// Strongly typed Component Config
type CustomComponentConfig<P> = Omit<BaseComponentConfig, "fields" | "render" | "defaultProps" | "resolveData"> & {
  dataContract?: DataContract;
  fields: Record<string, CustomField>;
  defaultProps?: P;
  render: (props: P & { id?: string }) => React.ReactElement; // Allow id in props
  resolveData?: (
    data: { props: P },
    params: { changed: Partial<Record<keyof P, boolean>> & { id?: string } }
  ) => Promise<{ props: P; readOnly?: Partial<Record<keyof P, boolean>> }>;
};

// Config that iterates over PropsMap using Mapped Types
type CustomConfig = Omit<Config, "components"> & {
  components: {
    [K in keyof PropsMap]: CustomComponentConfig<PropsMap[K]>;
  };
};

// Puck Configuration
export const config: CustomConfig = {
  // Root object for page-level settings
  root: {
    fields: {
      pageTitle: { type: "text", label: "Page Title" },
      pageDescription: { type: "textarea", label: "Page Description (SEO)" },
      backgroundColor: {
        type: "select",
        label: "Page Background",
        options: [
          { label: "White", value: "bg-white" },
          { label: "Gray", value: "bg-gray-50" },
          { label: "Dark", value: "bg-gray-900" },
        ],
      },
    },
    defaultProps: {
      pageTitle: "Sneakers Demo Store",
      pageDescription: "Premium footwear collection for style and comfort",
      backgroundColor: "bg-white",
    },
    render: (props: any) => (
      <div className={props.backgroundColor}>
        {props.children}
      </div>
    ),
  },

  // Categories for component organization
  categories: {
    layout: {
      title: "Layout",
      components: ["NavBar", "Footer"],
    },
    hero: {
      title: "Hero Sections",
      components: ["HeroSection", "SaleBannerSection"],
    },
    collections: {
      title: "Product Collections",
      components: ["CollectionSlider", "FeaturedProducts", "NewArrivals", "TwoColumnCollections"],
    },
  },

  components: {
    // NavBar
    NavBar: {
      label: "Navigation Bar",
      fields: {
        storeName: { type: "text", label: "Store Name" },
        logoUrl: { type: "imagePicker", label: "Logo Image" },
        links: {
          type: "array",
          label: "Navigation Links",
          arrayFields: {
            label: { type: "text", label: "Link Label" },
            href: { type: "text", label: "Link URL" },
          },
        },
        alignment: {
          type: "radio",
          label: "Link Alignment",
          options: [{ label: "Left", value: "left" }, { label: "Center", value: "center" }, { label: "Right", value: "right" }]
        },
        showSearch: { type: "radio", label: "Show Search", options: [{ label: "Yes", value: true }, { label: "No", value: false }] },
        showCart: { type: "radio", label: "Show Cart", options: [{ label: "Yes", value: true }, { label: "No", value: false }] },
        dataContract: { type: "custom", label: "Data Contract (Auto)", render: () => null },
      },
      defaultProps: {
        storeName: "👟 Sneakers Store",
        logoUrl: "",
        links: [
          { label: "Shop", href: "/products" },
          { label: "Collections", href: "/collections" },
          { label: "About", href: "/about" },
        ],
        alignment: "left",
        showSearch: true,
        showCart: true,
        dataContract: {
          type: "ALL_CATEGORIES",
          resolver: "allCategories",
        },
      },
      resolveData: async ({ props }, { changed }) => {
        const { getStoreSlug } = await import("./src/lib/utils/store-identifier");
        const storeSlug = getStoreSlug() || 'demo-store';
        return {
          props: { ...props, storeSlug },
          readOnly: { storeSlug: true },
        };
      },
      render: (props) => (
        <NavBar
          storeName={props.storeName}
          logoUrl={props.logoUrl}
          links={props.links}
          alignment={props.alignment}
          showSearch={props.showSearch}
          showCart={props.showCart}
          categories={props.categories}
        />
      ),
    },

    // Hero Section
    HeroSection: {
      label: "Hero Section",
      fields: {
        headline: { type: "textField", label: "Headline" },
        description: { type: "textField", label: "Description" },
        ctaText: { type: "text", label: "Button Text" },
        ctaLink: { type: "text", label: "Button Link" },
        mediaType: { type: "radio", label: "Media Type", options: [{ label: "Image", value: "image" }, { label: "Video", value: "video" }] },
        mediaUrl: { type: "imagePicker", label: "Image URL" },
        videoUrl: { type: "videoPicker", label: "Video URL" },
        overlayOpacity: { type: "slider", label: "Overlay Opacity", min: 0, max: 100, unit: "%" },
        textAlignment: { type: "radio", label: "Text Alignment", options: [{ label: "Left", value: "left" }, { label: "Center", value: "center" }, { label: "Right", value: "right" }] },
      },
      defaultProps: {
        headline: "PREMIUM <br/> FOOTWEAR",
        description: "Experience the ultimate comfort and style with our new collection.",
        ctaText: "Shop Now",
        ctaLink: "/products",
        mediaType: "image",
        mediaUrl: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=1920",
        videoUrl: "",
        overlayOpacity: 50,
        textAlignment: "center",
      },
      render: (props) => (
        <HeroSection {...props} />
      ),
    },

    // Collection Slider (Featured Collections)
    CollectionSlider: {
      label: "Featured Collections Slider",
      fields: {
        title: { type: "text", label: "Title" },
        limit: { type: "number", label: "Limit", min: 1, max: 10 },
        viewMoreText: { type: "text", label: "View More Text" },
        dataContract: { type: "custom", label: "Data Contract (Auto)", render: () => null },
      },
      defaultProps: {
        title: "Shop by Collection",
        limit: 3,
        viewMoreText: "See all collections →",
        dataContract: {
          type: "FEATURED_CATEGORIES",
          resolver: "featuredCategories",
        },
      },
      resolveData: async ({ props }, { changed }) => {
        // Resolve logic
        return { props: { ...props } };
      },
      render: (props) => (
        <CollectionSlider {...props} />
      ),
    },

    // Sale Banner Section
    SaleBannerSection: {
      label: "Sale Banner",
      fields: {
        headline: { type: "textField", label: "Headline" },
        description: { type: "textField", label: "Description" },
        offerText: { type: "textField", label: "Offer Text" },
        ctaText: { type: "text", label: "Button Text" },
        ctaLink: { type: "text", label: "Button Link" },
        backgroundImage: { type: "imagePicker", label: "Background Image" },
        overlayOpacity: { type: "slider", label: "Overlay Opacity", min: 0, max: 100, unit: "%" },
      },
      defaultProps: {
        headline: "BIG SALE!",
        description: "Get up to 50% off on selected items. Limited time only.",
        offerText: "3 FOR $169",
        ctaText: "Shop sale",
        ctaLink: "/collections/sale",
        backgroundImage: "https://images.unsplash.com/photo-1612902376491-7a8a99b424e8?w=1920",
        overlayOpacity: 70,
      },
      render: (props) => (
        <SaleBannerSection {...props} />
      ),
    },


    // Featured Products (Gradient Background)
    FeaturedProducts: {
      label: "Featured Products (Gradient)",
      fields: {
        title: { type: "text", label: "Title" },
        categorySlug: { type: "categorySelector", label: "Collection" },
        limit: { type: "number", label: "Limit", min: 1, max: 20 },
        viewMoreText: { type: "text", label: "View More Text" },
        dataContract: { type: "custom", label: "Data Contract (Auto)", render: () => null },
      },
      defaultProps: {
        title: "Featured Drops",
        categorySlug: "featured",
        limit: 10,
        viewMoreText: "View all",
        dataContract: {
          type: "CATEGORY_PRODUCTS",
          resolver: "categoryProducts",
        },
      },
      resolveData: async ({ props }, { changed }) => {
        const { getStoreSlug } = await import("./src/lib/utils/store-identifier");
        const storeSlug = getStoreSlug();
        return { props: { ...props, storeSlug } };
      },
      render: (props) => (
        <FeaturedProducts {...props} />
      ),
    },

    // New Arrivals (Same logic as Featured Products)
    NewArrivals: {
      label: "New Arrivals (Gradient)",
      fields: {
        title: { type: "text", label: "Title" },
        categorySlug: { type: "categorySelector", label: "Collection" },
        limit: { type: "number", label: "Limit", min: 1, max: 20 },
        viewMoreText: { type: "text", label: "View More Text" },
        dataContract: { type: "custom", label: "Data Contract (Auto)", render: () => null },
      },
      defaultProps: {
        title: "New Arrivals",
        categorySlug: "new-arrivals",
        limit: 10,
        viewMoreText: "View all",
        dataContract: {
          type: "CATEGORY_PRODUCTS",
          resolver: "categoryProducts",
        },
      },
      resolveData: async ({ props }, { changed }) => {
        const { getStoreSlug } = await import("./src/lib/utils/store-identifier");
        const storeSlug = getStoreSlug();
        return { props: { ...props, storeSlug } };
      },
      render: (props) => (
        <FeaturedProducts {...props} />
      ),
    },

    // Two Column Collections
    TwoColumnCollections: {
      label: "Secondary Collections (2-Col)",
      fields: {
        title: { type: "text", label: "Title (Optional)" },
        collection1Slug: { type: "categorySelector", label: "Left Collection" },
        collection2Slug: { type: "categorySelector", label: "Right Collection" },
        dataContract: { type: "custom", label: "Data Contract (Auto)", render: () => null },
      },
      defaultProps: {
        title: "More to Explore",
        collection1Slug: "",
        collection2Slug: "",
        dataContract: {
          type: "ALL_CATEGORIES",
          resolver: "allCategories",
        },
      },
      resolveData: async ({ props }, { changed }) => {
        // Resolve logic
        return { props: { ...props } };
      },
      render: (props) => (
        <TwoColumnCollections {...props} />
      ),
    },

    // Footer
    Footer: {
      label: "Footer",
      fields: {
        storeName: { type: "text", label: "Store Name" },
        description: { type: "textarea", label: "Store Description" },
        columns: {
          type: "array", label: "Footer Columns", arrayFields: { title: { type: "text", label: "Column Title" }, links: { type: "array", label: "Links", arrayFields: { label: { type: "text", label: "Link Label" }, href: { type: "text", label: "Link URL" } } } }
        },
        socialLinks: {
          type: "array", label: "Social Links", arrayFields: { platform: { type: "text", label: "Platform Name" }, url: { type: "text", label: "URL" }, icon: { type: "text", label: "Icon (emoji or text)" } }
        },
        copyrightText: { type: "text", label: "Copyright Text (Optional)" },
        showPaymentMethods: { type: "radio", label: "Show Payment Methods", options: [{ label: "Yes", value: true }, { label: "No", value: false }] },
      },
      defaultProps: {
        storeName: "SNEAKERS",
        description: "Premium footwear collection for style and comfort",
        columns: [
          {
            title: "SHOP",
            links: [
              { label: "All Products", href: "/products" },
              { label: "Collections", href: "/collections" },
              { label: "Sale", href: "/sale" },
            ],
          },
          {
            title: "COMPANY",
            links: [
              { label: "About Us", href: "/about" },
              { label: "Contact", href: "/contact" },
              { label: "Blog", href: "/blog" },
            ],
          },
          {
            title: "SUPPORT",
            links: [
              { label: "Shipping", href: "/shipping" },
              { label: "Returns", href: "/returns" },
              { label: "FAQ", href: "/faq" },
            ],
          },
        ],
        socialLinks: [
          { platform: "Instagram", url: "https://instagram.com", icon: "" },
          { platform: "Twitter", url: "https://twitter.com", icon: "" },
          { platform: "Facebook", url: "https://facebook.com", icon: "" },
        ],
        copyrightText: "",
        showPaymentMethods: true,
      },
      render: (props) => (
        <Footer {...props} />
      ),
    },
  },
};

export default config;
