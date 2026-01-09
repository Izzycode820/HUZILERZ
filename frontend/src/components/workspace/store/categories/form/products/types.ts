/**
 * Category Products Section Types
 */

export interface CategoryProductsSectionProps {
  selectedProductIds: string[]
  onProductsChange: (productIds: string[]) => void
  errors?: {
    products?: string
  }
}

export type SortOption = 'best-selling' | 'newest' | 'price-asc' | 'price-desc' | 'name-asc'

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'best-selling', label: 'Sort: Best selling' },
  { value: 'newest', label: 'Sort: Newest' },
  { value: 'price-asc', label: 'Sort: Price (Low to High)' },
  { value: 'price-desc', label: 'Sort: Price (High to Low)' },
  { value: 'name-asc', label: 'Sort: Name (A-Z)' },
]
