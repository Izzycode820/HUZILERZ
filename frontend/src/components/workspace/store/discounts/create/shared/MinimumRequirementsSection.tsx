'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Label } from '@/components/shadcn-ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/shadcn-ui/radio-group';
import { Input } from '@/components/shadcn-ui/input';
import * as Types from '@/types/workspace/store/graphql-base';

interface MinimumRequirementsSectionProps {
  minimumRequirementType: Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices;
  minimumPurchaseAmount?: number;
  minimumQuantityItems?: number;
  onRequirementTypeChange: (type: Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices) => void;
  onPurchaseAmountChange: (amount: number | undefined) => void;
  onQuantityChange: (quantity: number | undefined) => void;
}

export function MinimumRequirementsSection({
  minimumRequirementType,
  minimumPurchaseAmount,
  minimumQuantityItems,
  onRequirementTypeChange,
  onPurchaseAmountChange,
  onQuantityChange,
}: MinimumRequirementsSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Minimum purchase requirements</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <RadioGroup
          value={minimumRequirementType}
          onValueChange={(value) =>
            onRequirementTypeChange(value as Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices)
          }
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem
              value={Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices.None}
              id="min-none"
            />
            <Label htmlFor="min-none" className="font-normal cursor-pointer">
              No minimum requirements
            </Label>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem
                value={Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices.MinimumAmount}
                id="min-amount"
              />
              <Label htmlFor="min-amount" className="font-normal cursor-pointer">
                Minimum purchase amount (FCFA)
              </Label>
            </div>
            {minimumRequirementType === Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices.MinimumAmount && (
              <div className="ml-6">
                <Input
                  type="number"
                  value={minimumPurchaseAmount || ''}
                  onChange={(e) => onPurchaseAmountChange(e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="0.00"
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem
                value={Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices.MinimumQuantity}
                id="min-quantity"
              />
              <Label htmlFor="min-quantity" className="font-normal cursor-pointer">
                Minimum quantity of items
              </Label>
            </div>
            {minimumRequirementType === Types.WorkspaceStoreDiscountMinimumRequirementTypeChoices.MinimumQuantity && (
              <div className="ml-6">
                <Input
                  type="number"
                  value={minimumQuantityItems || ''}
                  onChange={(e) => onQuantityChange(e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="0"
                />
              </div>
            )}
          </div>
        </RadioGroup>
      </CardContent>
    </Card>
  );
}
