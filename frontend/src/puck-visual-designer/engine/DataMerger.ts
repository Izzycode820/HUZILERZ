'use client';

import type { ThemeConfigResponse } from '@/types/theme/theme.manifest';

// Manifest system interfaces
interface StoreData {
  store_info: {
    id: string;
    name: string;
    description?: string;
    logo?: string;
    contact?: Record<string, any>;
  };
  products: any[];
  settings: Record<string, any>;
  customizations: Record<string, any>;
}

interface MergedData {
  store: StoreData;
  styling: any;
  content: Record<string, any>;
  products: any[];
  features: Record<string, any>;
  // Manifest system data
  themeId: string;
  themeName: string;
  themeVersion: string;
  manifest?: any;
  puckConfig: any;
  puckData: any;
}

export class DataMerger {
  /**
   * Merge theme manifest configuration with store data and customizations
   * Updated for manifest system compatibility
   */
  static merge(themeConfig: ThemeConfigResponse, storeData: StoreData): MergedData {
    try {
      // Add null checks for required properties
      if (!themeConfig || !storeData) {
        throw new Error('Theme config and store data are required');
      }

      // Extract styling from theme manifest and puck config
      const themeStyling = themeConfig.puck_config?.styling || {};
      const storeCustomizations = storeData.customizations || {};
      const storeStyling = storeCustomizations.styling || {};

      const mergedStyling = this.mergeStyling(themeStyling, storeStyling);
      const processedProducts = this.processProducts(storeData.products || [], themeConfig);
      const mergedFeatures = this.mergeFeatures(themeConfig.puck_config?.features || {}, storeData.settings || {});
      const contentData = this.generateContentData(themeConfig, storeData);

      return {
        store: storeData,
        styling: mergedStyling,
        content: contentData,
        products: processedProducts,
        features: mergedFeatures,
        // Manifest system data
        themeId: themeConfig.template_id,
        themeName: themeConfig.template_name,
        themeVersion: themeConfig.version,
        manifest: themeConfig.manifest,
        puckConfig: themeConfig.puck_config,
        puckData: themeConfig.puck_data
      };
    } catch (error) {
      console.error('Error merging theme data:', error);
      throw new Error('Failed to merge theme configuration with store data');
    }
  }

  /**
   * Merge template styling with store customizations
   */
  private static mergeStyling(templateStyling: any, storeStyling: any): any {
    const merged = { ...templateStyling };

    // Merge default theme colors
    if (storeStyling.colors) {
      merged.default_theme = {
        ...merged.default_theme,
        ...storeStyling.colors
      };
    }

    // Merge typography
    if (storeStyling.typography) {
      merged.typography = {
        ...merged.typography,
        ...storeStyling.typography
      };
    }

    // Merge spacing
    if (storeStyling.spacing) {
      merged.spacing = {
        ...merged.spacing,
        ...storeStyling.spacing
      };
    }

    return merged;
  }

  /**
   * Process products for template consumption
   */
  private static processProducts(products: any[], themeConfig: ThemeConfigResponse): any[] {
    return products.map(product => ({
      ...product,
      // Add template-specific processing
      formatted_price: this.formatPrice(product.price, themeConfig.puck_config?.localization?.currency),
      image_urls: this.processProductImages(product.images || []),
      variants: this.processProductVariants(product.variants || []),
      availability: this.determineAvailability(product),
      seo_data: this.generateProductSEO(product)
    }));
  }

  /**
   * Format price according to template localization
   */
  private static formatPrice(price: number, currencyConfig?: any): string {
    if (!currencyConfig) {
      return `FCFA ${price.toLocaleString()}`;
    }

    const { symbol, position } = currencyConfig;
    const formattedNumber = price.toLocaleString();

    return position === 'before' 
      ? `${symbol} ${formattedNumber}`
      : `${formattedNumber} ${symbol}`;
  }

  /**
   * Process product images for template consumption
   */
  private static processProductImages(images: any[]): string[] {
    return images.map(image => {
      if (typeof image === 'string') {
        return image;
      }
      return image.url || image.src || '';
    }).filter(Boolean);
  }

  /**
   * Process product variants
   */
  private static processProductVariants(variants: any[]): any[] {
    return variants.map(variant => ({
      ...variant,
      formatted_price: this.formatPrice(variant.price || 0),
      is_available: variant.stock_quantity > 0
    }));
  }

  /**
   * Determine product availability
   */
  private static determineAvailability(product: any): any {
    const hasStock = product.stock_quantity > 0;
    const isActive = product.status === 'active' || product.status === 'published';
    
    return {
      in_stock: hasStock,
      is_active: isActive,
      is_available: hasStock && isActive,
      stock_level: this.getStockLevel(product.stock_quantity),
      estimated_restock: product.estimated_restock || null
    };
  }

  /**
   * Get stock level indicator
   */
  private static getStockLevel(quantity: number): 'out_of_stock' | 'low' | 'medium' | 'high' {
    if (quantity === 0) return 'out_of_stock';
    if (quantity <= 5) return 'low';
    if (quantity <= 20) return 'medium';
    return 'high';
  }

  /**
   * Generate SEO data for products
   */
  private static generateProductSEO(product: any): any {
    return {
      title: product.seo_title || product.name,
      description: product.seo_description || product.description?.substring(0, 160),
      keywords: product.seo_keywords || this.generateKeywords(product),
      canonical_url: `/product/${product.slug || product.id}`,
      og_image: product.images?.[0]?.url || product.image_url
    };
  }

  /**
   * Generate keywords from product data
   */
  private static generateKeywords(product: any): string[] {
    const keywords = [];
    
    if (product.name) {
      keywords.push(...product.name.toLowerCase().split(' '));
    }
    
    if (product.category) {
      keywords.push(product.category.toLowerCase());
    }
    
    if (product.tags) {
      keywords.push(...product.tags.map((tag: string) => tag.toLowerCase()));
    }
    
    return [...new Set(keywords)].filter(keyword => keyword.length > 2);
  }

  /**
   * Merge template features with store settings
   */
  private static mergeFeatures(templateFeatures: Record<string, any>, storeSettings: Record<string, any>): Record<string, any> {
    const merged = { ...templateFeatures };

    // Override features with store-specific settings
    Object.keys(merged).forEach(featureKey => {
      if (storeSettings[featureKey]) {
        merged[featureKey] = {
          ...merged[featureKey],
          ...storeSettings[featureKey]
        };
      }
    });

    return merged;
  }

  /**
   * Generate content data for template pages
   */
  private static generateContentData(themeConfig: ThemeConfigResponse, storeData: StoreData): Record<string, any> {
    const baseContent = {
      store_name: storeData.store_info.name,
      store_description: storeData.store_info.description,
      store_logo: storeData.store_info.logo,
      contact_info: storeData.store_info.contact || {},

      // Navigation content
      navigation: {
        home_text: 'Home',
        products_text: 'Products',
        cart_text: 'Cart',
        checkout_text: 'Checkout'
      },

      // Common page content
      common: {
        add_to_cart_text: 'Add to Cart',
        buy_now_text: 'Buy Now',
        continue_shopping_text: 'Continue Shopping',
        view_cart_text: 'View Cart',
        checkout_text: 'Checkout',
        back_text: 'Back',
        next_text: 'Next',
        loading_text: 'Loading...',
        error_text: 'Something went wrong',
        retry_text: 'Try Again'
      }
    };

    // Merge with store customizations
    const customContent = storeData.customizations?.content || {};

    return this.deepMerge(baseContent, customContent);
  }

  /**
   * Deep merge objects
   */
  private static deepMerge(target: any, source: any): any {
    const result = { ...target };
    
    for (const key in source) {
      if (source.hasOwnProperty(key)) {
        if (this.isObject(source[key]) && this.isObject(result[key])) {
          result[key] = this.deepMerge(result[key], source[key]);
        } else {
          result[key] = source[key];
        }
      }
    }
    
    return result;
  }

  /**
   * Check if value is an object
   */
  private static isObject(obj: any): boolean {
    return obj !== null && typeof obj === 'object' && !Array.isArray(obj);
  }

  /**
   * Validate merged data structure
   */
  static validate(mergedData: MergedData): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Validate required theme fields
    if (!mergedData.themeId) {
      errors.push('Theme ID is required');
    }

    if (!mergedData.themeName) {
      errors.push('Theme name is required');
    }

    // Validate store data
    if (!mergedData.store || !mergedData.store.store_info) {
      errors.push('Store information is required');
    }

    if (!mergedData.store.store_info.name) {
      errors.push('Store name is required');
    }

    // Validate styling
    if (!mergedData.styling) {
      errors.push('Styling configuration is required');
    }

    // Validate Puck configuration
    if (!mergedData.puckConfig) {
      errors.push('Puck configuration is required');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

export default DataMerger;