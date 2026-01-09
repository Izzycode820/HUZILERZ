'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Label } from '@/components/shadcn-ui/label';
import { Checkbox } from '@/components/shadcn-ui/checkbox';

interface CombinationsSectionProps {
  canCombineWithProductDiscounts: boolean;
  canCombineWithOrderDiscounts: boolean;
  onProductDiscountsChange: (checked: boolean) => void;
  onOrderDiscountsChange: (checked: boolean) => void;
}

export function CombinationsSection({
  canCombineWithProductDiscounts,
  canCombineWithOrderDiscounts,
  onProductDiscountsChange,
  onOrderDiscountsChange,
}: CombinationsSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Combinations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="combine-product"
            checked={canCombineWithProductDiscounts}
            onCheckedChange={(checked) => onProductDiscountsChange(checked as boolean)}
          />
          <Label htmlFor="combine-product" className="font-normal cursor-pointer">
            Product discounts
          </Label>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="combine-order"
            checked={canCombineWithOrderDiscounts}
            onCheckedChange={(checked) => onOrderDiscountsChange(checked as boolean)}
          />
          <Label htmlFor="combine-order" className="font-normal cursor-pointer">
            Order discounts
          </Label>
        </div>
      </CardContent>
    </Card>
  );
}
