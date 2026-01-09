'use client';

import { useState } from 'react';
import { useFilters } from '@/contexts/FilterContext';

/**
 * Price Range Filter Component
 * Decoupled, reusable component for min/max price filtering
 */

export function PriceRangeFilter() {
    const { filters, setFilter } = useFilters();
    const [localMin, setLocalMin] = useState(filters.minPrice?.toString() || '');
    const [localMax, setLocalMax] = useState(filters.maxPrice?.toString() || '');

    const handleMinChange = (value: string) => {
        setLocalMin(value);
        const numValue = value === '' ? null : parseFloat(value);
        if (numValue === null || !isNaN(numValue)) {
            setFilter('minPrice', numValue);
        }
    };

    const handleMaxChange = (value: string) => {
        setLocalMax(value);
        const numValue = value === '' ? null : parseFloat(value);
        if (numValue === null || !isNaN(numValue)) {
            setFilter('maxPrice', numValue);
        }
    };

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label htmlFor="min-price" className="text-xs text-muted-foreground block mb-1">
                        Min
                    </label>
                    <input
                        id="min-price"
                        type="number"
                        min="0"
                        placeholder="$0"
                        value={localMin}
                        onChange={(e) => handleMinChange(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-input bg-background rounded-none focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                </div>
                <div>
                    <label htmlFor="max-price" className="text-xs text-muted-foreground block mb-1">
                        Max
                    </label>
                    <input
                        id="max-price"
                        type="number"
                        min="0"
                        placeholder="Any"
                        value={localMax}
                        onChange={(e) => handleMaxChange(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-input bg-background rounded-none focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                </div>
            </div>

            {(filters.minPrice !== null || filters.maxPrice !== null) && (
                <div className="text-xs text-muted-foreground">
                    {filters.minPrice !== null && filters.maxPrice !== null
                        ? `$${filters.minPrice} - $${filters.maxPrice}`
                        : filters.minPrice !== null
                            ? `From $${filters.minPrice}`
                            : `Up to $${filters.maxPrice}`}
                </div>
            )}
        </div>
    );
}
