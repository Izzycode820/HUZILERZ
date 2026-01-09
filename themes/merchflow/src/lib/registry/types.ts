export type CategoryId =
    | "clothing" | "clothing-tops" | "clothing-warm" | "clothing-bottoms" | "clothing-headwear" | "clothing-footwear" | "clothing-kids"
    | "electronics" | "electronics-phone" | "electronics-computer" | "electronics-audio" | "electronics-wearables"
    | "home" | "home-drinkware" | "home-bedding" | "home-bathroom" | "home-kitchen" | "home-decor"
    | "wall-art" | "wall-art-prints" | "wall-art-textiles"
    | "accessories" | "accessories-bags" | "accessories-travel" | "accessories-small" | "accessories-masks"
    | "stationery" | "stationery-paper" | "stationery-mailing" | "stationery-office"
    | "pets";

export interface Category {
    id: CategoryId;
    label: string;
    parentId?: CategoryId;
    description?: string;
    image?: string; // Leading image for the category card
}

export interface ProductFeature {
    icon: string; // Lucide icon name
    title: string;
    description: string;
}

export interface SizeSpec {
    label: string; // S, M, L, XL, 11oz, etc.
    dims: {
        [key: string]: string; // "width": "20in", "length": "28in"
    };
}

// Re-using the logic from our canvas plan but strictly for the registry
export interface PrintArea {
    id: string; // front, back, sleeve_left, sleeve_right, wrap
    label: string;
    aspectRatio: number; // width / height
    baseImage: string; // URL to the photo/vector
    maskImage?: string; // URL to a masking layer
    overlayImage?: string; // URL to a texture/shadow layer represents the sandwich top

    // Editor coordinates (0-100%)
    editor: {
        top: number;
        left: number;
        width: number;
        height: number;
    };
}

export interface CatalogProduct {
    id: string;
    categoryId: CategoryId;
    name: string;
    brand: string;
    description: string;

    // Pricing & Meta
    basePrice: number;
    premiumPrice: number;
    rating?: number;
    reviewCount?: number;
    isNew?: boolean;
    isBestSeller?: boolean;

    // Configuration
    colors: { name: string; hex: string; image?: string }[];
    sizes: SizeSpec[];

    // Rich Details
    features: ProductFeature[];
    careInstructions: string[]; // "Do not bleach", "Machine wash cold"

    // Technicals for the Canvas
    printAreas: PrintArea[];
}
