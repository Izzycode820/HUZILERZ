'use client';

import React from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/shadcn-ui/input';
import { DiscountCard } from './DiscountCard';
import { DiscountsFilterChips } from './DiscountsFilterChips';
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

interface FilterChip {
    value: string;
    label: string;
    count?: number;
}

interface MobileDiscountsListProps {
    discounts: Discount[];
    workspaceId: string;
    // Search
    searchTerm: string;
    onSearchChange: (value: string) => void;
    // Filter chips
    chips: FilterChip[];
    activeChip: string;
    onChipChange: (value: string) => void;
    // Selection
    selectedDiscounts: string[];
    onSelectDiscount: (discountId: string) => void;
    onLongPressDiscount: (discountId: string) => void;
    onClearSelection: () => void;
    // Loading
    isLoading?: boolean;
}

export function MobileDiscountsList({
    discounts,
    workspaceId,
    searchTerm,
    onSearchChange,
    chips,
    activeChip,
    onChipChange,
    selectedDiscounts,
    onSelectDiscount,
    onLongPressDiscount,
    onClearSelection,
    isLoading,
}: MobileDiscountsListProps) {
    const isSelectionMode = selectedDiscounts.length > 0;

    return (
        <div className="flex flex-col gap-4 pb-32">
            {/* Search Bar */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                <Input
                    placeholder="Search discounts..."
                    value={searchTerm}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-10 h-12 rounded-xl border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
                />
            </div>

            {/* Filter Chips */}
            <DiscountsFilterChips
                chips={chips}
                activeChip={activeChip}
                onChipChange={onChipChange}
            />

            {/* Discounts List */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-white" />
                </div>
            ) : discounts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <p className="text-zinc-500 dark:text-zinc-400">No discounts found</p>
                    <p className="text-sm text-zinc-400 dark:text-zinc-500 mt-1">
                        Try adjusting your filters
                    </p>
                </div>
            ) : (
                <div className="flex flex-col gap-2">
                    {discounts.map((discount) => (
                        <DiscountCard
                            key={discount.id}
                            discount={discount}
                            workspaceId={workspaceId}
                            isSelected={selectedDiscounts.includes(discount.id)}
                            isSelectionMode={isSelectionMode}
                            onSelect={onSelectDiscount}
                            onLongPress={onLongPressDiscount}
                        />
                    ))}
                </div>
            )}

            {/* Selection indicator */}
            {selectedDiscounts.length > 0 && (
                <div className="fixed bottom-20 left-0 right-0 z-40 flex justify-center px-4 md:hidden pointer-events-none">
                    <div className="flex items-center gap-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-full px-4 py-3 shadow-2xl pointer-events-auto">
                        <button
                            onClick={onClearSelection}
                            className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                        >
                            ✕
                        </button>
                        <span className="text-sm font-medium px-2">
                            {selectedDiscounts.length} selected
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
