'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/shadcn-ui/badge';
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
    usageCount: number;
    isActive: boolean | null;
    isExpired: boolean | null;
}

interface DiscountCardProps {
    discount: Discount;
    workspaceId: string;
    isSelected: boolean;
    isSelectionMode: boolean;
    onSelect: (discountId: string) => void;
    onLongPress: (discountId: string) => void;
}

export function DiscountCard({
    discount,
    workspaceId,
    isSelected,
    isSelectionMode,
    onSelect,
    onLongPress,
}: DiscountCardProps) {
    const longPressTimer = React.useRef<NodeJS.Timeout | null>(null);
    const [isPressed, setIsPressed] = React.useState(false);

    const handleTouchStart = () => {
        setIsPressed(true);
        longPressTimer.current = setTimeout(() => {
            onLongPress(discount.id);
        }, 500);
    };

    const handleTouchEnd = () => {
        setIsPressed(false);
        if (longPressTimer.current) {
            clearTimeout(longPressTimer.current);
            longPressTimer.current = null;
        }
    };

    const handleClick = (e: React.MouseEvent) => {
        if (isSelectionMode) {
            e.preventDefault();
            onSelect(discount.id);
        }
    };

    // Get status badge
    const getStatusBadge = () => {
        if (discount.isExpired) {
            return (
                <Badge variant="outline" className="bg-zinc-100 text-zinc-600 border-zinc-200 text-xs">
                    Expired
                </Badge>
            );
        }
        if (!discount.isActive) {
            return (
                <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200 text-xs">
                    Scheduled
                </Badge>
            );
        }
        return (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-xs">
                Active
            </Badge>
        );
    };

    // Get discount value description
    const getDiscountValue = () => {
        if (discount.discountValueType === Types.WorkspaceStoreDiscountDiscountValueTypeChoices.Percentage) {
            return `${discount.value}% off`;
        }
        if (discount.discountValueType === Types.WorkspaceStoreDiscountDiscountValueTypeChoices.FixedAmount) {
            return `FCFA ${parseFloat(discount.value).toLocaleString()} off`;
        }
        return discount.discountType.replace(/_/g, ' ');
    };

    // Get method label
    const getMethodLabel = () => {
        return discount.method === Types.WorkspaceStoreDiscountMethodChoices.DiscountCode
            ? '🏷️ Code'
            : '⚡ Auto';
    };

    return (
        <Link
            href={`/workspace/${workspaceId}/store/discounts/${discount.id}`}
            onClick={handleClick}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            onTouchCancel={handleTouchEnd}
            onMouseDown={handleTouchStart}
            onMouseUp={handleTouchEnd}
            onMouseLeave={handleTouchEnd}
            className={cn(
                "flex items-center gap-3 p-3 rounded-xl transition-all duration-200 active:scale-[0.99]",
                isSelected
                    ? "bg-primary/10 border-2 border-primary ring-1 ring-primary/20"
                    : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800",
                isPressed && !isSelected && "bg-zinc-50 dark:bg-zinc-800/50"
            )}
        >
            {/* Discount Icon */}
            <div className="flex-shrink-0 w-11 h-11 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-lg">
                %
            </div>

            {/* Discount Info */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                        {discount.code}
                    </span>
                    {getStatusBadge()}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-zinc-600 dark:text-zinc-400">
                        {getDiscountValue()}
                    </span>
                    <span className="text-xs text-zinc-400">
                        • {getMethodLabel()}
                    </span>
                </div>
            </div>

            {/* Right Side: Usage Count */}
            <div className="flex-shrink-0 text-right">
                <div className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                    {discount.usageCount}
                </div>
                <div className="text-xs text-zinc-500">
                    used
                </div>
            </div>
        </Link>
    );
}
