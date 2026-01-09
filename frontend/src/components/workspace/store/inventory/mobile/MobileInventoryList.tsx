'use client';

import React from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/shadcn-ui/input';
import { InventoryCard } from './InventoryCard';
import { InventoryFilterChips } from './InventoryFilterChips';
import type { GetInventoryQuery } from '@/services/graphql/admin-store/queries/inventory/__generated__/GetInventory.generated';

type InventoryNode = NonNullable<
    NonNullable<NonNullable<GetInventoryQuery['inventory']>['edges'][0]>['node']
>;

interface FilterChip {
    value: string;
    label: string;
    count?: number;
}

interface MobileInventoryListProps {
    inventory: InventoryNode[];
    workspaceId: string;
    // Search
    searchTerm: string;
    onSearchChange: (value: string) => void;
    // Filter chips
    chips: FilterChip[];
    activeChip: string;
    onChipChange: (value: string) => void;
    // Selection
    selectedItems: string[];
    onSelectItem: (itemId: string) => void;
    onLongPressItem: (itemId: string) => void;
    onClearSelection: () => void;
    // Loading
    isLoading?: boolean;
}

export function MobileInventoryList({
    inventory,
    workspaceId,
    searchTerm,
    onSearchChange,
    chips,
    activeChip,
    onChipChange,
    selectedItems,
    onSelectItem,
    onLongPressItem,
    onClearSelection,
    isLoading,
}: MobileInventoryListProps) {
    const isSelectionMode = selectedItems.length > 0;

    return (
        <div className="flex flex-col gap-4 pb-32">
            {/* Search Bar */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                <Input
                    placeholder="Search inventory..."
                    value={searchTerm}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-10 h-12 rounded-xl border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
                />
            </div>

            {/* Filter Chips */}
            <InventoryFilterChips
                chips={chips}
                activeChip={activeChip}
                onChipChange={onChipChange}
            />

            {/* Inventory List */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-white" />
                </div>
            ) : inventory.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <p className="text-zinc-500 dark:text-zinc-400">No inventory found</p>
                    <p className="text-sm text-zinc-400 dark:text-zinc-500 mt-1">
                        Inventory is created when you add products with variants
                    </p>
                </div>
            ) : (
                <div className="flex flex-col gap-2">
                    {inventory.map((item) => (
                        <InventoryCard
                            key={item.id}
                            item={item}
                            workspaceId={workspaceId}
                            isSelected={selectedItems.includes(item.id)}
                            isSelectionMode={isSelectionMode}
                            onSelect={onSelectItem}
                            onLongPress={onLongPressItem}
                        />
                    ))}
                </div>
            )}

            {/* Selection indicator (no action bar for inventory since it's view-only for now) */}
            {selectedItems.length > 0 && (
                <div className="fixed bottom-20 left-0 right-0 z-40 flex justify-center px-4 md:hidden pointer-events-none">
                    <div className="flex items-center gap-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-full px-4 py-3 shadow-2xl pointer-events-auto">
                        <button
                            onClick={onClearSelection}
                            className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                        >
                            ✕
                        </button>
                        <span className="text-sm font-medium px-2">
                            {selectedItems.length} selected
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
