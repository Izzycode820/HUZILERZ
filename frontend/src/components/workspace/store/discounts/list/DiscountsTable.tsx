'use client';

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table';
import { Badge } from '@/components/shadcn-ui/badge';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import { DiscountRowActions } from './DiscountRowActions';
import * as Types from '@/types/workspace/store/graphql-base';

interface Discount {
  id: string;
  code: string;
  name: string;
  method: Types.WorkspaceStoreDiscountMethodChoices;
  discountType: Types.WorkspaceStoreDiscountDiscountTypeChoices;
  status: Types.WorkspaceStoreDiscountStatusChoices;
  discountValueType: Types.WorkspaceStoreDiscountDiscountValueTypeChoices | null;
  value: any | null;
  customerBuysQuantity: number | null;
  customerBuysValue: any | null;
  customerGetsQuantity: number | null;
  minimumPurchaseAmount: any | null;
  minimumQuantityItems: number | null;
  limitOnePerCustomer: boolean;
  usageCount: number;
  canCombineWithProductDiscounts: boolean;
  canCombineWithOrderDiscounts: boolean;
  isActive: boolean | null;
  isExpired: boolean | null;
}

interface DiscountsTableProps {
  discounts: Discount[];
  onDiscountSelect?: (selectedIds: string[]) => void;
  onEdit?: (discountId: string) => void;
  onDelete?: (discountId: string) => void;
}

export function DiscountsTable({
  discounts,
  onDiscountSelect,
  onEdit,
  onDelete,
}: DiscountsTableProps) {
  const [selectedDiscounts, setSelectedDiscounts] = useState<string[]>([]);

  const handleSelectAll = (checked: boolean) => {
    const newSelected = checked ? discounts.map((d) => d.id) : [];
    setSelectedDiscounts(newSelected);
    onDiscountSelect?.(newSelected);
  };

  const handleSelectDiscount = (discountId: string, checked: boolean) => {
    const newSelected = checked
      ? [...selectedDiscounts, discountId]
      : selectedDiscounts.filter((id) => id !== discountId);
    setSelectedDiscounts(newSelected);
    onDiscountSelect?.(newSelected);
  };

  const getStatusBadge = (discount: Discount) => {
    if (discount.isExpired) {
      return (
        <Badge variant="outline" className="bg-gray-100 text-gray-800 border-gray-200">
          Expired
        </Badge>
      );
    }
    if (!discount.isActive) {
      return (
        <Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-200">
          Scheduled
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">
        Active
      </Badge>
    );
  };

  const getMethodBadge = (method: Types.WorkspaceStoreDiscountMethodChoices) => {
    return (
      <span className="text-sm">
        {method === Types.WorkspaceStoreDiscountMethodChoices.DiscountCode ? 'Code' : 'Automatic'}
      </span>
    );
  };

  const getTypeBadge = (discountType: Types.WorkspaceStoreDiscountDiscountTypeChoices) => {
    const typeLabels = {
      [Types.WorkspaceStoreDiscountDiscountTypeChoices.AmountOffProduct]: 'Amount off products',
      [Types.WorkspaceStoreDiscountDiscountTypeChoices.BuyXGetY]: 'Buy X get Y',
      [Types.WorkspaceStoreDiscountDiscountTypeChoices.AmountOffOrder]: 'Amount off order',
      [Types.WorkspaceStoreDiscountDiscountTypeChoices.FreeShipping]: 'Free shipping',
    };
    return <span className="text-sm">{typeLabels[discountType] || discountType}</span>;
  };

  const getCombinationIcons = (discount: Discount) => {
    const combinations = [];
    if (discount.canCombineWithProductDiscounts) {
      combinations.push('Products');
    }
    if (discount.canCombineWithOrderDiscounts) {
      combinations.push('Orders');
    }
    return combinations.length > 0 ? (
      <span className="text-sm">{combinations.join(' • ')}</span>
    ) : (
      <span className="text-muted-foreground">-</span>
    );
  };

  const getDiscountDescription = (discount: Discount) => {
    const parts = [];

    // Discount value
    if (discount.discountType === Types.WorkspaceStoreDiscountDiscountTypeChoices.AmountOffProduct) {
      if (discount.discountValueType === Types.WorkspaceStoreDiscountDiscountValueTypeChoices.Percentage) {
        parts.push(`${discount.value}% off`);
      } else if (discount.discountValueType === Types.WorkspaceStoreDiscountDiscountValueTypeChoices.FixedAmount) {
        parts.push(`FCFA${parseFloat(discount.value).toLocaleString()} off`);
      }
    } else if (discount.discountType === Types.WorkspaceStoreDiscountDiscountTypeChoices.BuyXGetY) {
      if (discount.customerBuysQuantity && discount.customerGetsQuantity) {
        parts.push(`Buy ${discount.customerBuysQuantity}, get ${discount.customerGetsQuantity}`);
      }
    }

    // Minimum requirements
    if (discount.minimumPurchaseAmount) {
      parts.push(`Minimum purchase of FCFA${parseFloat(discount.minimumPurchaseAmount).toLocaleString()}`);
    } else if (discount.minimumQuantityItems) {
      parts.push(`Minimum ${discount.minimumQuantityItems} items`);
    }

    // Usage limit
    if (discount.limitOnePerCustomer) {
      parts.push('One use per customer');
    }

    return parts.join(' • ');
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={selectedDiscounts.length === discounts.length && discounts.length > 0}
                onCheckedChange={handleSelectAll}
                aria-label="Select all"
              />
            </TableHead>
            <TableHead>Title</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Method</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Combinations</TableHead>
            <TableHead>Used</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {discounts.map((discount) => (
            <TableRow key={discount.id}>
              <TableCell>
                <Checkbox
                  checked={selectedDiscounts.includes(discount.id)}
                  onCheckedChange={(checked) => handleSelectDiscount(discount.id, checked as boolean)}
                  aria-label={`Select ${discount.code}`}
                />
              </TableCell>
              <TableCell className="font-medium">
                <div className="flex flex-col gap-1">
                  <div className="font-medium">{discount.code}</div>
                  <div className="text-xs text-muted-foreground">{getDiscountDescription(discount)}</div>
                </div>
              </TableCell>
              <TableCell>{getStatusBadge(discount)}</TableCell>
              <TableCell>{getMethodBadge(discount.method)}</TableCell>
              <TableCell>{getTypeBadge(discount.discountType)}</TableCell>
              <TableCell>{getCombinationIcons(discount)}</TableCell>
              <TableCell>
                <span className="text-sm">{discount.usageCount}</span>
              </TableCell>
              <TableCell>
                <DiscountRowActions discount={discount} onEdit={onEdit} onDelete={onDelete} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
