import { CreditCard } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Separator } from '@/components/shadcn-ui/separator';
import { formatCurrency } from '@/utils/currency';

interface PaymentCardProps {
  paymentStatus: string;
  paymentMethod: string;
  subtotal: string;
  shippingCost: string;
  taxAmount: string;
  discountAmount: string;
  totalAmount: string;
  currency: string;
  itemCount: number;
}

export function PaymentCard({
  paymentStatus,
  paymentMethod,
  subtotal,
  shippingCost,
  taxAmount,
  discountAmount,
  totalAmount,
  currency,
  itemCount,
}: PaymentCardProps) {
  return (
    <Card>
      <CardHeader className="bg-green-50 dark:bg-green-900/10 border-b">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded">
            <CreditCard className="h-4 w-4 text-green-700 dark:text-green-400" />
          </div>
          <CardTitle className="text-base capitalize">
            {paymentStatus?.toLowerCase()}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-4 space-y-3">
        {/* Subtotal */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Subtotal
            <span className="ml-2">{itemCount} {itemCount === 1 ? 'item' : 'items'}</span>
          </span>
          <span className="font-medium">{currency} {formatCurrency(subtotal)}</span>
        </div>

        {/* Shipping */}
        {parseFloat(shippingCost) > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Shipping</span>
            <span className="font-medium">{currency} {formatCurrency(shippingCost)}</span>
          </div>
        )}

        {/* Tax */}
        {parseFloat(taxAmount) > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Tax</span>
            <span className="font-medium">{currency} {formatCurrency(taxAmount)}</span>
          </div>
        )}

        {/* Discount */}
        {parseFloat(discountAmount) > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Discount</span>
            <span className="font-medium text-red-600">
              -{currency} {formatCurrency(discountAmount)}
            </span>
          </div>
        )}

        <Separator />

        {/* Total */}
        <div className="flex items-center justify-between">
          <span className="font-semibold">Total</span>
          <span className="font-bold text-lg">{currency} {formatCurrency(totalAmount)}</span>
        </div>

        <Separator />

        {/* Payment Method */}
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium capitalize">
            {paymentStatus?.toLowerCase()}
          </span>
          <span className="font-medium">{currency} {formatCurrency(totalAmount)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
