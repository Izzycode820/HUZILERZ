# Payment Section - Build Guide

## Objective
Build payment summary section that calculates and displays order totals in real-time based on selected products.

---

## File Structure
```
orders/form/payment/
├── PaymentSection.tsx           # Main component
├── usePaymentCalculations.ts    # Calculation logic hook
├── types.ts                     # Type definitions
└── index.ts                     # Clean exports
```

---

## 1. types.ts

```typescript
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
```

---

## 2. usePaymentCalculations.ts

**Purpose:** Calculate payment summary from items array

```typescript
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
```

---

## 3. PaymentSection.tsx

**Layout:**
```
┌─ Card ─────────────────────────┐
│ Payment                         │
├─────────────────────────────────┤
│ Payment method                  │
│ [Dropdown: COD/Mobile Money]    │
│                                 │
│ ─────────────────────────────── │
│ Subtotal      FCFA 155,598      │
│ Tax               FCFA 0        │
│ ─────────────────────────────── │
│ Total         FCFA 155,598      │
└─────────────────────────────────┘
```

**shadcn components:**
- Card
- Select (payment method dropdown)
- Label

**Props:**
```typescript
interface Props {
  items: OrderItem[];
  paymentMethod: string;
  onPaymentMethodChange: (method: string) => void;
}
```

**Payment methods (match backend):**
```typescript
const PAYMENT_METHODS = [
  { value: 'cash_on_delivery', label: 'Cash on Delivery' },
  { value: 'mobile_money', label: 'Mobile Money' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Credit/Debit Card' },
] as const;
```

**Behavior:**
- Auto-calculates when `items` change
- Format currency: `new Intl.NumberFormat('fr-FR').format(amount)` + " FCFA"
- Show 0 values for tax (grayed out or hidden)
- Bold total amount

---

## 4. Currency Formatting Utility

**Create:** `utils/currency.ts`

```typescript
export function formatCurrency(amount: string | number): string {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(numAmount);
}

// Usage: formatCurrency("155598") => "155 598"
// Display: "FCFA 155 598"
```

---

## Integration with Parent Form

```typescript
const [paymentMethod, setPaymentMethod] = useState('cash_on_delivery');

<PaymentSection
  items={items} // From products section
  paymentMethod={paymentMethod}
  onPaymentMethodChange={setPaymentMethod}
/>

// On form submit
const orderPayload = {
  customer_id: customerId,
  items: items.map(...),
  payment_method: paymentMethod,
  // These are calculated on backend, but we can pass from UI
  shipping_cost: "0.00",
  tax_amount: "0.00",
  discount_amount: "0.00",
};
```

---

## Key Points

1. **Pure calculation** - no API calls, just math
2. **Real-time updates** - recalculates when items array changes
3. **useMemo optimization** - prevents unnecessary recalculations
4. **Currency formatting** - Use Intl.NumberFormat for proper spacing
5. **MVP scope** - Tax/Discount/Shipping = 0 (backend calculates shipping for customer orders)

---

## Testing Checklist

- [ ] Subtotal updates when product added
- [ ] Subtotal updates when quantity changed
- [ ] Subtotal updates when product removed
- [ ] Total shows correct calculation
- [ ] Currency formatted with spaces (155 598)
- [ ] Payment method dropdown works
- [ ] Shows 0 when no products
