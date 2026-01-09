export interface ProductImage {
    id: string;
    url: string;
    alt: string;
    is_thumbnail?: boolean;
}

export interface ProductVariant {
    id: string;
    name: string; // e.g. "Small / Red"
    sku: string;
    price: number;
    stock: number;
    options: Record<string, string>; // { Size: "S", Color: "Red" }
}

export interface Product {
    id: string;
    title: string;
    slug: string;
    description: string;
    price: number;
    compare_at_price?: number;
    vendor: string;
    category_id: string;
    tags: string[];
    images: ProductImage[];
    variants: ProductVariant[];
    rating?: number;
    review_count?: number;
    created_at: string;
}

export const products: Product[] = [
    {
        id: 'prod_1',
        title: 'Essential Cotton T-Shirt',
        slug: 'essential-cotton-t-shirt',
        description: 'A premium heavy-weight cotton t-shirt designed for everyday comfort and durability. Features a relaxed fit and ribbed crew neck.',
        price: 35.00,
        compare_at_price: 45.00,
        vendor: 'Studio',
        category_id: 'cat_2',
        tags: ['basic', 'cotton', 'top'],
        rating: 4.8,
        review_count: 124,
        images: [
            { id: 'img_1', url: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&q=80&w=800', alt: 'White cotton t-shirt front view', is_thumbnail: true },
            { id: 'img_2', url: 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?auto=format&fit=crop&q=80&w=800', alt: 'Black cotton t-shirt front view' }
        ],
        variants: [
            { id: 'var_1', name: 'S / White', sku: 'TS-WHT-S', price: 35.00, stock: 10, options: { Size: 'S', Color: 'White' } },
            { id: 'var_2', name: 'M / White', sku: 'TS-WHT-M', price: 35.00, stock: 15, options: { Size: 'M', Color: 'White' } }
        ],
        created_at: '2025-01-01T10:00:00Z'
    },
    {
        id: 'prod_2',
        title: 'Oversized Denim Jacket',
        slug: 'oversized-denim-jacket',
        description: 'Vintage-inspired oversized denim jacket with distressed details and ample pockets.',
        price: 120.00,
        vendor: 'Urban',
        category_id: 'cat_3',
        tags: ['outerwear', 'denim', 'vintage'],
        rating: 4.6,
        review_count: 56,
        images: [
            { id: 'img_3', url: 'https://images.unsplash.com/photo-1551537482-f2075a1d41f2?auto=format&fit=crop&q=80&w=800', alt: 'Denim jacket', is_thumbnail: true }
        ],
        variants: [],
        created_at: '2025-01-02T10:00:00Z'
    },
    {
        id: 'prod_3',
        title: 'Minimalist Leather Tote',
        slug: 'minimalist-leather-tote',
        description: 'Crafted from genuine full-grain leather, this tote carries all your essentials in style.',
        price: 195.00,
        vendor: 'Artisan',
        category_id: 'cat_4',
        tags: ['bag', 'leather', 'accessory'],
        rating: 5.0,
        review_count: 32,
        images: [
            { id: 'img_4', url: 'https://images.unsplash.com/photo-1591561954557-26941169b49e?auto=format&fit=crop&q=80&w=800', alt: 'Leather tote bag', is_thumbnail: true }
        ],
        variants: [],
        created_at: '2025-01-03T10:00:00Z'
    },
    {
        id: 'prod_4',
        title: 'Pleated Trousers',
        slug: 'pleated-trousers',
        description: 'Elegant pleated trousers that work for both office and casual settings. High-waisted fit.',
        price: 85.00,
        vendor: 'Studio',
        category_id: 'cat_2',
        tags: ['bottoms', 'formal', 'trousers'],
        rating: 4.2,
        review_count: 18,
        images: [
            { id: 'img_5', url: 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&q=80&w=800', alt: 'Pleated trousers', is_thumbnail: true }
        ],
        variants: [],
        created_at: '2025-01-04T10:00:00Z'
    },
    {
        id: 'prod_5',
        title: 'Chunky Knit Sweater',
        slug: 'chunky-knit-sweater',
        description: 'Stay warm in this ultra-soft chunky knit sweater. Perfect for layering.',
        price: 75.00,
        compare_at_price: 90.00,
        vendor: 'Cozy',
        category_id: 'cat_2',
        tags: ['knitwear', 'winter', 'sweater'],
        rating: 4.9,
        review_count: 210,
        images: [
            { id: 'img_6', url: 'https://images.unsplash.com/photo-1576871337622-98d48d1cf531?auto=format&fit=crop&q=80&w=800', alt: 'Knit sweater', is_thumbnail: true }
        ],
        variants: [],
        created_at: '2025-01-05T10:00:00Z'
    },
    {
        id: 'prod_6',
        title: 'Classic Sneakers',
        slug: 'classic-sneakers',
        description: 'Timeless low-top sneakers in premium white leather.',
        price: 110.00,
        vendor: 'Kicks',
        category_id: 'cat_3',
        tags: ['footwear', 'shoes', 'sneakers'],
        rating: 4.7,
        review_count: 89,
        images: [
            { id: 'img_7', url: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&q=80&w=800', alt: 'White sneakers', is_thumbnail: true }
        ],
        variants: [],
        created_at: '2025-01-06T10:00:00Z'
    }
];
