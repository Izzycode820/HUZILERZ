import type { SearchProductsForOrderQuery } from '@/services/graphql/admin-store/queries/products/__generated__/SearchProductsForOrder.generated';

// Extract product from codegen query
export type ProductSearchResult = NonNullable<
  NonNullable<
    NonNullable<SearchProductsForOrderQuery['products']>['edges'][number]
  >['node']
>;

// Order item state (what we store in UI)
export interface OrderItem {
  product_id: string;
  product_name: string;
  product_image: string | null;
  variant_id?: string | null;
  quantity: number;
  unit_price: string; // Decimal as string
  subtotal: string;   // quantity * unit_price
}

// Props interfaces
export interface ProductsSectionProps {
  items: OrderItem[];
  onItemsChange: (items: OrderItem[]) => void;
}

// Note: ProductSearchModalProps is now in shared/products/types.ts
// We use the shared ProductSearchModal component

export interface ProductItemProps {
  item: OrderItem;
  onQuantityChange: (productId: string, quantity: number) => void;
  onRemove: (productId: string) => void;
}
