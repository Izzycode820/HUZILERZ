import type { OrderItem } from '../products/types';

export interface PaymentSummary {
  subtotal: string;      // Sum of all item subtotals
  taxAmount: string;     // 0.00 for now (MVP)
  discountAmount: string; // 0.00 for now (admin doesn't set)
  shippingCost: string;  // 0.00 for now (admin doesn't set)
  total: string;         // subtotal + tax + shipping - discount
}

export interface PaymentSectionProps {
  items: OrderItem[];  // From products section
  paymentMethod: string;
  onPaymentMethodChange: (method: string) => void;
}
