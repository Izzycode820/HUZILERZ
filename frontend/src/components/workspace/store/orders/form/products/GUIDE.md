# Products Section - Build Guide

## Objective
Build products section for order creation form with search modal and product list management.

---

## File Structure
```
orders/form/products/
├── ProductsSection.tsx          # Main component
├── ProductSearchModal.tsx       # Search & add modal
├── ProductItem.tsx              # Individual product card
├── useProductsState.ts          # State management hook
├── types.ts                     # Type definitions
└── index.ts                     # Clean exports
```

---

## 1. types.ts

```typescript
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
```

---

## 2. useProductsState.ts

**Purpose:** Manage product items array state

```typescript
import { useState, useCallback } from 'react';
import type { OrderItem, ProductSearchResult } from './types';

export function useProductsState() {
  const [items, setItems] = useState<OrderItem[]>([]);

  // Add product from search modal
  const addProduct = useCallback((product: ProductSearchResult) => {
    const newItem: OrderItem = {
      product_id: product.id,
      product_name: product.name,
      product_image: product.mediaUploads?.[0]?.thumbnail || null,
      variant_id: null, // TODO: variant support later
      quantity: 1,
      unit_price: product.price.toString(),
      subtotal: product.price.toString(),
    };

    setItems(prev => [...prev, newItem]);
  }, []);

  // Update quantity
  const updateQuantity = useCallback((productId: string, quantity: number) => {
    setItems(prev =>
      prev.map(item =>
        item.product_id === productId
          ? {
              ...item,
              quantity,
              subtotal: (parseFloat(item.unit_price) * quantity).toFixed(2),
            }
          : item
      )
    );
  }, []);

  // Remove item
  const removeItem = useCallback((productId: string) => {
    setItems(prev => prev.filter(item => item.product_id !== productId));
  }, []);

  return {
    items,
    addProduct,
    updateQuantity,
    removeItem,
  };
}
```

---

## 3. ProductSearchModal.tsx

**UI Flow:**
1. Click "Search products" → input appears with autofocus
2. Type → query runs (debounced 300ms)
3. Results show with image, name, price, stock
4. Click "Add" → calls `onAddProduct`, modal closes

**shadcn components:**
- Dialog (modal)
- Command (search with keyboard nav)
- Input (search field)
- Button

**GraphQL:**
- Use generated hook from `SearchProductsForOrder.generated.ts`
- Import: `import { useSearchProductsForOrderQuery } from '@/services/graphql/admin-store/queries/products/__generated__/SearchProductsForOrder.generated'`

**Key behaviors:**
- Debounce search input (300ms)
- Show loading state while querying
- Empty state: "No products found"
- Disable "Add" if product already in list

---

## 4. ProductItem.tsx

**Display:**
- Product image (48x48)
- Name
- Quantity input (number, min=1)
- Unit price (read-only, formatted: `FCFA {price}`)
- Subtotal (calculated: quantity × unit_price)
- Remove button (X icon)

**shadcn components:**
- Card
- Input (number type)
- Button (ghost variant for remove)

**Behaviors:**
- On quantity change → call `onQuantityChange(product_id, newQuantity)`
- On remove → call `onRemove(product_id)`
- Calculate subtotal in real-time

---

## 5. ProductsSection.tsx

**Layout:**
```
┌─ Card ─────────────────────────────┐
│ Products                            │
├─────────────────────────────────────┤
│ [Search products input/button]      │
│                                      │
│ [ProductItem]                        │
│ [ProductItem]                        │
│ [ProductItem]                        │
│                                      │
│ Empty state: "No products added"    │
└─────────────────────────────────────┘
```

**Props:**
```typescript
interface Props {
  items: OrderItem[];
  onItemsChange: (items: OrderItem[]) => void;
}
```

**Behavior:**
- Button click → opens ProductSearchModal
- Pass `items` to modal to disable already-added products
- On product add → append to items array
- Map items to ProductItem components

---

## 6. GraphQL Query File

**Path:** `frontend/src/services/graphql/admin-store/queries/products/SearchProductsForOrder.graphql`

```graphql
query SearchProductsForOrder($search: String, $first: Int) {
  products(name_Icontains: $search, first: $first, status: ACTIVE) {
    edges {
      node {
        id
        name
        price
        inventoryQuantity
        sku
        mediaUploads {
          id
          thumbnail
          thumbnailWebp
        }
      }
    }
  }
}
```

**After creating:** Run `npm run codegen` to generate types

---

## Integration with Parent Form

**Parent form state:**
```typescript
const { items, addProduct, updateQuantity, removeItem } = useProductsState();

// Pass to ProductsSection
<ProductsSection
  items={items}
  onItemsChange={setItems} // Or use individual handlers
/>

// On form submit
const orderPayload = {
  customer_id: customerId,
  items: items.map(item => ({
    product_id: item.product_id,
    variant_id: item.variant_id,
    quantity: item.quantity,
    unit_price: item.unit_price,
  })),
  // ... other fields
};
```

---

## Key Points

1. **NO mutations until final submit** - all UI state only
2. **Use codegen types** - import from `__generated__/` files
3. **Controlled components** - parent owns state
4. **Currency format** - Always show "FCFA" for Cameroon context
5. **Real-time calculations** - Subtotal updates on quantity change
6. **Debounced search** - 300ms delay, use `useDebouncedValue` hook if available

---

## Testing Checklist

- [ ] Search modal opens on button click
- [ ] Search query debounces properly
- [ ] Products display with image, name, price
- [ ] Add button adds product to list
- [ ] Duplicate products disabled in modal
- [ ] Quantity input updates subtotal
- [ ] Remove button works
- [ ] Empty state shows when no products
