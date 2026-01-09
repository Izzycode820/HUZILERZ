import { X } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import type { ProductItemProps } from './types';

// Currency formatting utility
function formatCurrency(amount: string | number): string {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(numAmount);
}

export function ProductItem({ item, onQuantityChange, onRemove }: ProductItemProps) {
  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 1) {
      onQuantityChange(item.product_id, value);
    }
  };

  return (
    <div className="flex items-center gap-3 py-3 border-b last:border-b-0">
      {/* Product Image */}
      <div className="flex-shrink-0 w-12 h-12 bg-muted rounded overflow-hidden">
        {item.product_image ? (
          <img
            src={item.product_image}
            alt={item.product_name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-xs text-muted-foreground">
            No image
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">{item.product_name}</p>
        <p className="text-sm text-blue-600">FCFA {formatCurrency(item.unit_price)}</p>
      </div>

      {/* Quantity Input */}
      <div className="w-20">
        <Input
          type="number"
          min="1"
          value={item.quantity}
          onChange={handleQuantityChange}
          className="text-center h-9"
        />
      </div>

      {/* Total */}
      <div className="w-32 text-right">
        <p className="font-medium text-sm">FCFA {formatCurrency(item.subtotal)}</p>
      </div>

      {/* Remove Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onRemove(item.product_id)}
        className="flex-shrink-0 h-8 w-8"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
