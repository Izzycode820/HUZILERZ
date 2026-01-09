'use client';

import React from 'react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import { OrderStatusBadge } from '../OrderStatusBadge';
import { formatCurrency } from '@/utils/currency';
import type { GetOrdersQuery } from '@/services/graphql/admin-store/queries/orders/__generated__/getOrders.generated';

type OrderNode = NonNullable<
    NonNullable<
        NonNullable<GetOrdersQuery['orders']>['edges'][number]
    >['node']
>;

interface OrderCardProps {
    order: OrderNode;
    workspaceId: string;
    isSelected: boolean;
    isSelectionMode: boolean; // NEW: Are we in multi-select mode?
    onSelect: (orderId: string) => void;
    onLongPress: (orderId: string) => void;
}

export function OrderCard({
    order,
    workspaceId,
    isSelected,
    isSelectionMode,
    onSelect,
    onLongPress,
}: OrderCardProps) {
    const longPressTimer = React.useRef<NodeJS.Timeout | null>(null);
    const [isPressed, setIsPressed] = React.useState(false);

    const handleTouchStart = () => {
        setIsPressed(true);
        longPressTimer.current = setTimeout(() => {
            onLongPress(order.id);
        }, 500); // 500ms for long press
    };

    const handleTouchEnd = () => {
        setIsPressed(false);
        if (longPressTimer.current) {
            clearTimeout(longPressTimer.current);
            longPressTimer.current = null;
        }
    };

    const handleClick = (e: React.MouseEvent) => {
        // If in selection mode, toggle selection instead of navigating
        if (isSelectionMode) {
            e.preventDefault();
            onSelect(order.id);
        }
    };

    const getChannelIcon = (orderSource: string) => {
        switch (orderSource?.toLowerCase()) {
            case 'whatsapp':
                return '💬';
            case 'web':
                return '🌐';
            case 'admin':
                return '👤';
            default:
                return '📦';
        }
    };

    return (
        <Link
            href={`/workspace/${workspaceId}/store/orders/${order.id}`}
            onClick={handleClick}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            onTouchCancel={handleTouchEnd}
            onMouseDown={handleTouchStart}
            onMouseUp={handleTouchEnd}
            onMouseLeave={handleTouchEnd}
            className={cn(
                "block rounded-xl p-4 transition-all duration-200 active:scale-[0.98]",
                isSelected
                    ? "bg-primary/10 border-2 border-primary ring-2 ring-primary/20"
                    : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800",
                isPressed && !isSelected && "bg-zinc-50 dark:bg-zinc-800/50"
            )}
        >
            {/* Header: Order # + Time + Channel */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">
                        #{order.orderNumber}
                    </span>
                    <span className="text-xs text-zinc-400">
                        {getChannelIcon(order.orderSource)}
                    </span>
                </div>
                <span className="text-xs text-zinc-500">
                    {formatDistanceToNow(new Date(order.createdAt), { addSuffix: true })}
                </span>
            </div>

            {/* Customer + Amount */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex flex-col">
                    <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                        {order.customerName || 'No customer'}
                    </span>
                    {order.customerPhone && (
                        <span className="text-xs text-zinc-500">
                            {order.customerPhone}
                        </span>
                    )}
                </div>
                <div className="text-right">
                    <span className="font-semibold text-sm">
                        {order.currency} {formatCurrency(order.totalAmount)}
                    </span>
                    <div className="text-xs text-zinc-500">
                        {order.itemCount} {order.itemCount === 1 ? 'item' : 'items'}
                    </div>
                </div>
            </div>

            {/* Status Badges */}
            <div className="flex items-center gap-2">
                <OrderStatusBadge status={order.paymentStatus} type="payment" />
                <OrderStatusBadge status={order.status} type="fulfillment" />
            </div>
        </Link>
    );
}
