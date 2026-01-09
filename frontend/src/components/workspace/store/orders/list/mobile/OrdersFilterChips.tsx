'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface FilterChip {
    value: string;
    label: string;
    count?: number;
}

interface OrdersFilterChipsProps {
    chips: FilterChip[];
    activeChip: string;
    onChipChange: (value: string) => void;
}

const DEFAULT_CHIPS: FilterChip[] = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'paid', label: 'Paid' },
    { value: 'unfulfilled', label: 'Unfulfilled' },
    { value: 'fulfilled', label: 'Fulfilled' },
    { value: 'archived', label: 'Archived' },
];

export function OrdersFilterChips({
    chips = DEFAULT_CHIPS,
    activeChip,
    onChipChange,
}: OrdersFilterChipsProps) {
    return (
        <div
            className="flex gap-2 overflow-x-auto scrollbar-none pb-2 -mx-4 px-4"
            style={{
                scrollbarWidth: 'none',
                msOverflowStyle: 'none',
            }}
        >
            {chips.map((chip) => (
                <button
                    key={chip.value}
                    onClick={() => onChipChange(chip.value)}
                    className={cn(
                        "flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 active:scale-95",
                        activeChip === chip.value
                            ? "bg-zinc-900 dark:bg-white text-white dark:text-zinc-900"
                            : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                    )}
                >
                    {chip.label}
                    {chip.count !== undefined && (
                        <span className="ml-1.5 text-xs opacity-70">
                            {chip.count}
                        </span>
                    )}
                </button>
            ))}
        </div>
    );
}

export { DEFAULT_CHIPS };
