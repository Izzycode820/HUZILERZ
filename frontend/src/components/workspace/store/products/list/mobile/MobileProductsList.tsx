'use client';

import React from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/shadcn-ui/input';
import { ProductCard } from './ProductCard';
import { ProductsFilterChips } from './ProductsFilterChips';
import { MobileProductsActionBar } from './MobileProductsActionBar';

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

interface FilterChip {
    value: string;
    label: string;
    count?: number;
}

interface MobileProductsListProps {
    products: Product[];
    workspaceId: string;
    // Search
    searchTerm: string;
    onSearchChange: (value: string) => void;
    // Filter chips
    chips: FilterChip[];
    activeChip: string;
    onChipChange: (value: string) => void;
    // Selection
    selectedProducts: string[];
    onSelectProduct: (productId: string) => void;
    onLongPressProduct: (productId: string) => void;
    onClearSelection: () => void;
    // Bulk actions
    onBulkArchive: () => void;
    onBulkDelete: () => void;
    onBulkDuplicate?: () => void;
    onBulkExport?: () => void;
    // Row actions
    onEdit?: (productId: string) => void;
    onView?: (productId: string) => void;
    onDuplicate?: (productId: string) => void;
    onDelete?: (productId: string) => void;
    onCategoryUpdate?: () => void;
    // Loading
    isLoading?: boolean;
}

export function MobileProductsList({
    products,
    workspaceId,
    searchTerm,
    onSearchChange,
    chips,
    activeChip,
    onChipChange,
    selectedProducts,
    onSelectProduct,
    onLongPressProduct,
    onClearSelection,
    onBulkArchive,
    onBulkDelete,
    onBulkDuplicate,
    onBulkExport,
    onEdit,
    onView,
    onDuplicate,
    onDelete,
    onCategoryUpdate,
    isLoading,
}: MobileProductsListProps) {
    return (
        <div className="flex flex-col gap-4 pb-32">
            {/* Search Bar */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                <Input
                    placeholder="Search products..."
                    value={searchTerm}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-10 h-12 rounded-xl border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
                />
            </div>

            {/* Filter Chips */}
            <ProductsFilterChips
                chips={chips}
                activeChip={activeChip}
                onChipChange={onChipChange}
            />

            {/* Products List */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-white" />
                </div>
            ) : products.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <p className="text-zinc-500 dark:text-zinc-400">No products found</p>
                    <p className="text-sm text-zinc-400 dark:text-zinc-500 mt-1">
                        Try adjusting your filters
                    </p>
                </div>
            ) : (
                <div className="flex flex-col gap-2">
                    {products.map((product) => (
                        <ProductCard
                            key={product.id}
                            product={product}
                            workspaceId={workspaceId}
                            isSelected={selectedProducts.includes(product.id)}
                            isSelectionMode={selectedProducts.length > 0}
                            onSelect={onSelectProduct}
                            onLongPress={onLongPressProduct}
                            onEdit={onEdit}
                            onView={onView}
                            onDuplicate={onDuplicate}
                            onDelete={onDelete}
                            onCategoryUpdate={onCategoryUpdate}
                        />
                    ))}
                </div>
            )}

            {/* Mobile Action Bar (fixed position) */}
            <MobileProductsActionBar
                selectedCount={selectedProducts.length}
                selectedProductIds={selectedProducts}
                onCancel={onClearSelection}
                onArchive={onBulkArchive}
                onDelete={onBulkDelete}
                onDuplicate={onBulkDuplicate}
                onExport={onBulkExport}
                onCategoryUpdate={onCategoryUpdate}
            />
        </div>
    );
}
