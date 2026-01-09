export interface Category {
    id: string;
    name: string;
    slug: string;
    image?: string;
    description?: string;
    parent_id?: string;
}

export const categories: Category[] = [
    {
        id: 'cat_1',
        name: 'New Arrivals',
        slug: 'new-arrivals',
        image: 'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&q=80&w=800',
        description: 'The latest trends for the season.'
    },
    {
        id: 'cat_2',
        name: 'Women',
        slug: 'women',
        image: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&q=80&w=800',
    },
    {
        id: 'cat_3',
        name: 'Men',
        slug: 'men',
        image: 'https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?auto=format&fit=crop&q=80&w=800',
    },
    {
        id: 'cat_4',
        name: 'Accessories',
        slug: 'accessories',
        image: 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&q=80&w=800',
    },
    {
        id: 'cat_5',
        name: 'Sale',
        slug: 'sale',
        image: 'https://images.unsplash.com/photo-1607083206968-13611e3d76db?auto=format&fit=crop&q=80&w=800',
    }
];
