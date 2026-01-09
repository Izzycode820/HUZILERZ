'use client';

import React from 'react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/shadcn-ui/badge';
import { formatCurrency } from '@/utils/currency';
import type { GetCustomersQuery } from '@/services/graphql/admin-store/queries/customers/__generated__/GetCustomers.generated';

type CustomerNode = NonNullable<
    NonNullable<
        NonNullable<GetCustomersQuery['customers']>['edges'][number]
    >['node']
>;

interface CustomerCardProps {
    customer: CustomerNode;
    workspaceId: string;
    isSelected: boolean;
    isSelectionMode: boolean;
    onSelect: (customerId: string) => void;
    onLongPress: (customerId: string) => void;
}

export function CustomerCard({
    customer,
    workspaceId,
    isSelected,
    isSelectionMode,
    onSelect,
    onLongPress,
}: CustomerCardProps) {
    const longPressTimer = React.useRef<NodeJS.Timeout | null>(null);
    const [isPressed, setIsPressed] = React.useState(false);

    const handleTouchStart = () => {
        setIsPressed(true);
        longPressTimer.current = setTimeout(() => {
            onLongPress(customer.id);
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
            onSelect(customer.id);
        }
    };

    // Generate initials for avatar
    const getInitials = (name: string) => {
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    return (
        <Link
            href={`/workspace/${workspaceId}/store/customers/${customer.id}`}
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
            {/* Avatar Circle */}
            <div className="flex-shrink-0 w-11 h-11 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-sm font-semibold text-zinc-600 dark:text-zinc-300">
                {getInitials(customer.name)}
            </div>

            {/* Customer Info */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="font-medium text-sm truncate text-zinc-900 dark:text-zinc-100">
                        {customer.name}
                    </span>
                    <Badge variant="secondary" className="text-xs capitalize px-1.5 py-0">
                        {customer.customerType}
                    </Badge>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-zinc-500 truncate">
                        {customer.phone}
                    </span>
                    {customer.city && (
                        <span className="text-xs text-zinc-400">
                            • {customer.city}
                        </span>
                    )}
                </div>
            </div>

            {/* Right Side: Orders + Spent */}
            <div className="flex-shrink-0 text-right">
                <div className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                    {customer.totalOrders} orders
                </div>
                <div className="text-xs text-zinc-500">
                    FCFA {formatCurrency(customer.totalSpent)}
                </div>
            </div>
        </Link>
    );
}
