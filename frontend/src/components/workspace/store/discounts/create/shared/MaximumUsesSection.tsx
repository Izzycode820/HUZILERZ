'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Label } from '@/components/shadcn-ui/label';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import { Input } from '@/components/shadcn-ui/input';

interface MaximumUsesSectionProps {
  limitTotalUses: boolean;
  usageLimit?: number;
  limitOnePerCustomer: boolean;
  onLimitTotalUsesChange: (checked: boolean) => void;
  onUsageLimitChange: (limit: number | undefined) => void;
  onLimitOnePerCustomerChange: (checked: boolean) => void;
}

export function MaximumUsesSection({
  limitTotalUses,
  usageLimit,
  limitOnePerCustomer,
  onLimitTotalUsesChange,
  onUsageLimitChange,
  onLimitOnePerCustomerChange,
}: MaximumUsesSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Maximum discount uses</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="limit-total"
              checked={limitTotalUses}
              onCheckedChange={(checked) => onLimitTotalUsesChange(checked as boolean)}
            />
            <Label htmlFor="limit-total" className="font-normal cursor-pointer">
              Limit number of times this discount can be used in total
            </Label>
          </div>
          {limitTotalUses && (
            <div className="ml-6">
              <Input
                type="number"
                value={usageLimit || ''}
                onChange={(e) => onUsageLimitChange(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="0"
              />
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="limit-per-customer"
            checked={limitOnePerCustomer}
            onCheckedChange={(checked) => onLimitOnePerCustomerChange(checked as boolean)}
          />
          <Label htmlFor="limit-per-customer" className="font-normal cursor-pointer">
            Limit to one use per customer
          </Label>
        </div>
      </CardContent>
    </Card>
  );
}
