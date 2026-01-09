'use client';

import React from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/shadcn-ui/input';
import { CategoryCard } from './CategoryCard';

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

interface MobileCategoriesListProps {
    categories: Category[];
    workspaceId: string;
    // Search
    searchTerm: string;
    onSearchChange: (value: string) => void;
    // Selection
    selectedCategories: string[];
    onSelectCategory: (categoryId: string) => void;
    onLongPressCategory: (categoryId: string) => void;
    onClearSelection: () => void;
    // Loading
    isLoading?: boolean;
}

export function MobileCategoriesList({
    categories,
    workspaceId,
    searchTerm,
    onSearchChange,
    selectedCategories,
    onSelectCategory,
    onLongPressCategory,
    onClearSelection,
    isLoading,
}: MobileCategoriesListProps) {
    const isSelectionMode = selectedCategories.length > 0;

    return (
        <div className="flex flex-col gap-4 pb-32">
            {/* Search Bar */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                <Input
                    placeholder="Search categories..."
                    value={searchTerm}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-10 h-12 rounded-xl border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
                />
            </div>

            {/* Categories List */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-white" />
                </div>
            ) : categories.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <p className="text-zinc-500 dark:text-zinc-400">No categories found</p>
                    <p className="text-sm text-zinc-400 dark:text-zinc-500 mt-1">
                        Try adjusting your search
                    </p>
                </div>
            ) : (
                <div className="flex flex-col gap-2">
                    {categories.map((category) => (
                        <CategoryCard
                            key={category.id}
                            category={category}
                            workspaceId={workspaceId}
                            isSelected={selectedCategories.includes(category.id)}
                            isSelectionMode={isSelectionMode}
                            onSelect={onSelectCategory}
                            onLongPress={onLongPressCategory}
                        />
                    ))}
                </div>
            )}

            {/* Selection indicator */}
            {selectedCategories.length > 0 && (
                <div className="fixed bottom-20 left-0 right-0 z-40 flex justify-center px-4 md:hidden pointer-events-none">
                    <div className="flex items-center gap-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-full px-4 py-3 shadow-2xl pointer-events-auto">
                        <button
                            onClick={onClearSelection}
                            className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                        >
                            ✕
                        </button>
                        <span className="text-sm font-medium px-2">
                            {selectedCategories.length} selected
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
