import { useMemo } from 'react';
import type { OrderItem } from '../products/types';
import type { PaymentSummary } from './types';

export function usePaymentCalculations(items: OrderItem[]): PaymentSummary {
  return useMemo(() => {
    // Calculate subtotal (sum of all item subtotals)
    const subtotal = items.reduce((sum, item) => {
      return sum + parseFloat(item.subtotal);
    }, 0);

    // MVP: No tax, discount, or shipping on admin side
    const taxAmount = 0;
    const discountAmount = 0;
    const shippingCost = 0;

    // Calculate total
    const total = subtotal + taxAmount + shippingCost - discountAmount;

    return {
      subtotal: subtotal.toFixed(2),
      taxAmount: taxAmount.toFixed(2),
      discountAmount: discountAmount.toFixed(2),
      shippingCost: shippingCost.toFixed(2),
      total: total.toFixed(2),
    };
  }, [items]);
}
