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
        image: '/images/categories/new-arrivals.jpg',
        description: 'The latest trends for the season.'
    },
    {
        id: 'cat_2',
        name: 'Women',
        slug: 'women',
        image: '/images/categories/women.jpg',
    },
    {
        id: 'cat_3',
        name: 'Men',
        slug: 'men',
        image: '/images/categories/men.jpg',
    },
    {
        id: 'cat_4',
        name: 'Accessories',
        slug: 'accessories',
        image: '/images/categories/accessories.jpg',
    },
    {
        id: 'cat_5',
        name: 'Sale',
        slug: 'sale',
        image: '/images/categories/sale.jpg',
    }
];
