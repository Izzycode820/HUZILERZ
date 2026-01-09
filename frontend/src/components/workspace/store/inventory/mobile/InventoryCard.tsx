'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/shadcn-ui/badge';
import type { GetInventoryQuery } from '@/services/graphql/admin-store/queries/inventory/__generated__/GetInventory.generated';

type InventoryNode = NonNullable<
    NonNullable<NonNullable<GetInventoryQuery['inventory']>['edges'][0]>['node']
>;

interface InventoryCardProps {
    item: InventoryNode;
    workspaceId: string;
    isSelected: boolean;
    isSelectionMode: boolean;
    onSelect: (itemId: string) => void;
    onLongPress: (itemId: string) => void;
}

export function InventoryCard({
    item,
    workspaceId,
    isSelected,
    isSelectionMode,
    onSelect,
    onLongPress,
}: InventoryCardProps) {
    const longPressTimer = React.useRef<NodeJS.Timeout | null>(null);
    const [isPressed, setIsPressed] = React.useState(false);

    const handleTouchStart = () => {
        setIsPressed(true);
        longPressTimer.current = setTimeout(() => {
            onLongPress(item.id);
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
            onSelect(item.id);
        }
    };

    // Build variant URL
    const variantId = item.variant?.id || '';
    const productId = item.variant?.product?.id || '';
    const variantUrl = productId && variantId
        ? `/workspace/${workspaceId}/store/products/${productId}/variants/${variantId}`
        : `/workspace/${workspaceId}/store/inventory`;

    // Thumbnail
    const thumbnailUrl = item.productImage?.thumbnailUrl || item.productImage?.url;

    // Get stock status color for the circle
    const getStockCircleStyle = (stockStatus: string | null, available: number) => {
        if (stockStatus === 'out_of_stock' || available === 0) {
            return 'bg-red-100 text-red-700 border-red-300';
        }
        if (stockStatus === 'low_stock' || available < 10) {
            return 'bg-yellow-100 text-yellow-700 border-yellow-300';
        }
        return 'bg-green-100 text-green-700 border-green-300';
    };

    return (
        <Link
            href={variantUrl}
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
            {/* Product Thumbnail */}
            <div className="flex-shrink-0">
                {thumbnailUrl ? (
                    <img
                        src={thumbnailUrl}
                        alt={item.productName || ''}
                        className="w-12 h-12 rounded-lg object-cover border border-zinc-200 dark:border-zinc-700"
                    />
                ) : (
                    <div className="w-12 h-12 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700">
                        <span className="text-xs text-zinc-400">📦</span>
                    </div>
                )}
            </div>

            {/* Product + Variant Info */}
            <div className="flex-1 min-w-0">
                {/* Product Name */}
                <span className="font-medium text-sm truncate text-zinc-900 dark:text-zinc-100 block">
                    {item.productName}
                </span>

                {/* Variant Options as Badges (like desktop) */}
                <div className="flex flex-wrap gap-1 mt-1">
                    {item.variant?.option1 && (
                        <Badge variant="secondary" className="text-xs px-1.5 py-0">
                            {item.variant.option1}
                        </Badge>
                    )}
                    {item.variant?.option2 && (
                        <Badge variant="secondary" className="text-xs px-1.5 py-0">
                            {item.variant.option2}
                        </Badge>
                    )}
                    {item.variant?.option3 && (
                        <Badge variant="secondary" className="text-xs px-1.5 py-0">
                            {item.variant.option3}
                        </Badge>
                    )}
                    {!item.variant?.option1 && !item.variant?.option2 && !item.variant?.option3 && (
                        <span className="text-xs text-zinc-500">Default</span>
                    )}
                </div>

                {/* Location (small text) */}
                {item.location?.name && (
                    <div className="text-xs text-zinc-400 mt-0.5">
                         {item.location.name}
                    </div>
                )}
            </div>

            {/* Available Stock Circle */}
            <div className="flex-shrink-0">
                <div className={cn(
                    "w-11 h-11 rounded-full border-2 flex items-center justify-center font-semibold text-sm",
                    getStockCircleStyle(item.stockStatus, item.available || 0)
                )}>
                    {item.available}
                </div>
            </div>
        </Link>
    );
}
