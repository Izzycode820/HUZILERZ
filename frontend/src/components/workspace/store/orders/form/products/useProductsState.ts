import { useState, useCallback } from 'react';
import type { OrderItem, ProductSearchResult } from './types';

export function useProductsState() {
  const [items, setItems] = useState<OrderItem[]>([]);

  // Add product from search modal
  const addProduct = useCallback((product: ProductSearchResult) => {
    const newItem: OrderItem = {
      product_id: product.id,
      product_name: product.name,
      product_image: product.mediaGallery?.[0]?.thumbnailUrl || null,
      variant_id: null, // TODO: variant support later
      quantity: 1,
      unit_price: product.price.toString(),
      subtotal: product.price.toString(),
    };

    setItems(prev => [...prev, newItem]);
  }, []);

  // Update quantity
  const updateQuantity = useCallback((productId: string, quantity: number) => {
    if (quantity < 1) return; // Prevent zero or negative quantities

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
    setItems,
  };
}
