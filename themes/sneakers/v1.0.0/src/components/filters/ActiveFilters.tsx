'use client';

import { useFilters } from '@/contexts/FilterContext';
import { X } from 'lucide-react';

/**
 * Active Filters Display Component
 * Shows applied filters as removable chips
 */

export function ActiveFilters() {
    const { filters, setFilter, clearFilters, hasActiveFilters } = useFilters();

    if (!hasActiveFilters) return null;

    const activeFilterChips: { label: string; onRemove: () => void }[] = [];

    // Category filter
    if (filters.categorySlug) {
        activeFilterChips.push({
            label: `Category: ${filters.categorySlug}`,
            onRemove: () => setFilter('categorySlug', null),
        });
    }

    // Price range filter
    if (filters.minPrice !== null || filters.maxPrice !== null) {
        const priceLabel =
            filters.minPrice !== null && filters.maxPrice !== null
                ? `$${filters.minPrice} - $${filters.maxPrice}`
                : filters.minPrice !== null
                    ? `From $${filters.minPrice}`
                    : `Up to $${filters.maxPrice}`;

        activeFilterChips.push({
            label: priceLabel,
            onRemove: () => {
                setFilter('minPrice', null);
                setFilter('maxPrice', null);
            },
        });
    }

    // Brand filter
    if (filters.brand) {
        activeFilterChips.push({
            label: `Brand: ${filters.brand}`,
            onRemove: () => setFilter('brand', null),
        });
    }

    // Stock filter
    if (filters.inStock !== null) {
        activeFilterChips.push({
            label: filters.inStock ? 'In Stock' : 'Out of Stock',
            onRemove: () => setFilter('inStock', null),
        });
    }

    return (
        <div className="flex flex-wrap items-center gap-2 py-4">
            <span className="text-sm text-muted-foreground">Active Filters:</span>

            {activeFilterChips.map((chip, index) => (
                <button
                    key={index}
                    onClick={chip.onRemove}
                    className="inline-flex items-center gap-1.5 px-3 py-1 text-sm bg-primary/10 text-primary hover:bg-primary/20 transition-colors rounded-full group"
                >
                    {chip.label}
                    <X className="h-3 w-3 group-hover:scale-110 transition-transform" />
                </button>
            ))}

            <button
                onClick={clearFilters}
                className="text-sm text-muted-foreground hover:text-foreground underline underline-offset-2 ml-2"
            >
                Clear All
            </button>
        </div>
    );
}
