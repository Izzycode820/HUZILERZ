import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Label } from '@/components/shadcn-ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select';
import { Separator } from '@/components/shadcn-ui/separator';
import { usePaymentCalculations } from './usePaymentCalculations';
import { formatCurrency } from '@/utils/currency';
import type { PaymentSectionProps } from './types';

const PAYMENT_METHODS = [
  { value: 'cash_on_delivery', label: 'Cash on Delivery' },
  { value: 'mobile_money', label: 'Mobile Money' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Credit/Debit Card' },
] as const;

export function PaymentSection({
  items,
  paymentMethod,
  onPaymentMethodChange,
}: PaymentSectionProps) {
  const { subtotal, taxAmount, total } = usePaymentCalculations(items);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Payment</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Payment Method Dropdown */}
        <div className="space-y-2">
          <Label htmlFor="payment-method">Payment method</Label>
          <Select value={paymentMethod} onValueChange={onPaymentMethodChange}>
            <SelectTrigger id="payment-method">
              <SelectValue placeholder="Select payment method" />
            </SelectTrigger>
            <SelectContent>
              {PAYMENT_METHODS.map((method) => (
                <SelectItem key={method.value} value={method.value}>
                  {method.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* Payment Summary */}
        <div className="space-y-3">
          {/* Subtotal */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              Subtotal
              {items.length > 0 && (
                <span className="ml-2">
                  {items.length} {items.length === 1 ? 'item' : 'items'}
                </span>
              )}
            </span>
            <span className="font-medium">FCFA {formatCurrency(subtotal)}</span>
          </div>

          {/* Tax (shown but 0 for now) */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Tax</span>
            <span className="text-muted-foreground">FCFA {formatCurrency(taxAmount)}</span>
          </div>

          <Separator />

          {/* Total */}
          <div className="flex items-center justify-between">
            <span className="font-semibold">Total</span>
            <span className="font-bold text-lg">FCFA {formatCurrency(total)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
