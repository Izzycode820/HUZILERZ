'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

interface Category {
    id: string;
    name: string;
    isVisible: boolean;
    isFeatured: boolean;
    productCount: number;
    featuredMedia?: {
        id: string;
        url?: string | null;
        thumbnailUrl?: string | null;
    };
}

interface CategoryCardProps {
    category: Category;
    workspaceId: string;
    isSelected: boolean;
    isSelectionMode: boolean;
    onSelect: (categoryId: string) => void;
    onLongPress: (categoryId: string) => void;
}

export function CategoryCard({
    category,
    workspaceId,
    isSelected,
    isSelectionMode,
    onSelect,
    onLongPress,
}: CategoryCardProps) {
    const longPressTimer = React.useRef<NodeJS.Timeout | null>(null);
    const [isPressed, setIsPressed] = React.useState(false);

    const handleTouchStart = () => {
        setIsPressed(true);
        longPressTimer.current = setTimeout(() => {
            onLongPress(category.id);
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
            onSelect(category.id);
        }
    };

    const thumbnailUrl = category.featuredMedia?.thumbnailUrl || category.featuredMedia?.url;

    return (
        <Link
            href={`/workspace/${workspaceId}/store/categories/${category.id}`}
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
            {/* Category Image */}
            <div className="flex-shrink-0">
                {thumbnailUrl ? (
                    <img
                        src={thumbnailUrl}
                        alt={category.name}
                        className="w-14 h-14 rounded-lg object-cover border border-zinc-200 dark:border-zinc-700"
                    />
                ) : (
                    <div className="w-14 h-14 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700">
                        <span className="text-lg">📁</span>
                    </div>
                )}
            </div>

            {/* Category Name */}
            <div className="flex-1 min-w-0">
                <span className="font-medium text-sm text-zinc-900 dark:text-zinc-100 block truncate">
                    {category.name}
                </span>
                {!category.isVisible && (
                    <span className="text-xs text-zinc-400">Hidden</span>
                )}
            </div>

            {/* Product Count */}
            <div className="flex-shrink-0 text-right">
                <div className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                    {category.productCount}
                </div>
                <div className="text-xs text-zinc-500">
                    products
                </div>
            </div>
        </Link>
    );
}
