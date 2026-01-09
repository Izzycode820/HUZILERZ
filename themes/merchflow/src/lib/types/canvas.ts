export type ProductView = {
    id: string; // e.g., 'front', 'back', 'left', 'right'
    name: string; // Display name

    // Design Mode Assets (Flat / Vector style)
    editorBaseImage: string;

    // Preview Mode Assets (Realistic / 3D style)
    previewBaseImage: string;
    previewOverlayImage?: string; // Optional shadow/texture layer
    previewMaskImage?: string; // Optional clipping mask

    // The Safe Print Area relative to the Base Image
    // Defined as percentages (0-100) to be responsive
    printArea: {
        top: number;
        left: number;
        width: number;
        height: number;
    };
};

export type ProductFeature = {
    icon: string; // Lucide icon name or image path
    title: string;
    description: string;
};

export type SizeSpec = {
    label: string; // S, M, L, XL
    width: string; // "20.00"
    length: string; // "29.00" 
    sleeve?: string; // Optional
};

export type ProductConfig = {
    id: string;
    name: string;
    category: string;
    brand?: string;
    description?: string;
    basePrice: number;
    premiumPrice?: number;
    rating?: number;
    reviewCount?: number;

    colors: { name: string; hex: string }[];
    sizes?: SizeSpec[]; // List of available sizes and their dims

    features?: ProductFeature[];
    careInstructions?: string[]; // List of instruction codes or text

    views: ProductView[];
};
