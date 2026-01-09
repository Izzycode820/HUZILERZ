/**
 * Filter state types
 * Matches GraphQL API parameters for product filtering
 */

export interface FilterState {
    search: string;
    categorySlug: string | null;
    minPrice: number | null;
    maxPrice: number | null;
    inStock: boolean | null;
    brand: string | null;
    sortBy: SortOption;
}

export type SortOption =
    | 'featured'
    | 'price-asc'
    | 'price-desc'
    | 'newest'
    | 'name-asc'
    | 'name-desc';

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
    { value: 'featured', label: 'Featured' },
    { value: 'price-asc', label: 'Price: Low to High' },
    { value: 'price-desc', label: 'Price: High to Low' },
    { value: 'newest', label: 'Newest' },
    { value: 'name-asc', label: 'Name: A-Z' },
    { value: 'name-desc', label: 'Name: Z-A' },
];

export const DEFAULT_FILTERS: FilterState = {
    search: '',
    categorySlug: null,
    minPrice: null,
    maxPrice: null,
    inStock: null,
    brand: null,
    sortBy: 'featured',
};
