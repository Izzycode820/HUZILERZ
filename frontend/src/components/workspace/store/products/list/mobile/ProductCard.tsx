'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/shadcn-ui/badge';
import { ProductRowActions } from '../ProductRowActions';

interface Product {
    id: string;
    name: string;
    status: 'published' | 'archived';
    price: number;
    inventory: number;
    category: string;
    type: string;
    vendor: string;
    featuredMedia?: {
        thumbnailUrl?: string;
        url?: string;
    };
}

interface ProductCardProps {
    product: Product;
    workspaceId: string;
    isSelected: boolean;
    isSelectionMode: boolean; // NEW: Are we in multi-select mode?
    onSelect: (productId: string) => void;
    onLongPress: (productId: string) => void;
    onEdit?: (productId: string) => void;
    onView?: (productId: string) => void;
    onDuplicate?: (productId: string) => void;
    onDelete?: (productId: string) => void;
    onCategoryUpdate?: () => void;
}

export function ProductCard({
    product,
    workspaceId,
    isSelected,
    isSelectionMode,
    onSelect,
    onLongPress,
    onEdit,
    onView,
    onDuplicate,
    onDelete,
    onCategoryUpdate,
}: ProductCardProps) {
    const longPressTimer = React.useRef<NodeJS.Timeout | null>(null);
    const [isPressed, setIsPressed] = React.useState(false);

    const handleTouchStart = () => {
        setIsPressed(true);
        longPressTimer.current = setTimeout(() => {
            onLongPress(product.id);
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
        // If in selection mode, toggle selection instead of navigating
        if (isSelectionMode) {
            e.preventDefault();
            onSelect(product.id);
        }
    };

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('fr-CM', {
            style: 'currency',
            currency: 'XAF',
            minimumFractionDigits: 0,
        }).format(price);
    };

    const getStatusBadge = (status: string) => {
        if (status === 'published') {
            return (
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-xs">
                    Active
                </Badge>
            );
        }
        return (
            <Badge variant="outline" className="bg-zinc-50 text-zinc-600 border-zinc-200 text-xs">
                Archived
            </Badge>
        );
    };

    const thumbnailUrl = product.featuredMedia?.thumbnailUrl || product.featuredMedia?.url;

    return (
        <Link
            href={`/workspace/${workspaceId}/store/products/${product.id}`}
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
                        alt={product.name}
                        className="w-12 h-12 rounded-lg object-cover border border-zinc-200 dark:border-zinc-700"
                    />
                ) : (
                    <div className="w-12 h-12 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700">
                        <span className="text-xs text-zinc-400">📦</span>
                    </div>
                )}
            </div>

            {/* Product Info */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="font-medium text-sm truncate text-zinc-900 dark:text-zinc-100">
                        {product.name}
                    </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                    {getStatusBadge(product.status)}
                    <span className="text-xs text-zinc-500">
                        {product.category}
                    </span>
                </div>
            </div>

            {/* Right Side: Price + Stock + Actions */}
            <div className="flex-shrink-0 flex items-center gap-2">
                <div className="text-right">
                    <div className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                        {formatPrice(product.price)}
                    </div>
                    <div className={cn(
                        "text-xs",
                        product.inventory > 0 ? "text-zinc-500" : "text-red-500"
                    )}>
                        {product.inventory > 0 ? `${product.inventory} in stock` : 'Out of stock'}
                    </div>
                </div>
                {/* Row Actions - Hidden in selection mode */}
                {!isSelectionMode && (
                    <div onClick={(e) => e.preventDefault()}>
                        <ProductRowActions
                            product={product}
                            onEdit={onEdit}
                            onView={onView}
                            onDuplicate={onDuplicate}
                            onDelete={onDelete}
                            onCategoryUpdate={onCategoryUpdate}
                        />
                    </div>
                )}
            </div>
        </Link>
    );
}
