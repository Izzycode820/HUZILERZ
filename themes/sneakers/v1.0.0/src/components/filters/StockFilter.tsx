'use client';

import { useFilters } from '@/contexts/FilterContext';

/**
 * Stock Availability Filter Component
 * Simple toggle for in-stock filtering
 */

export function StockFilter() {
    const { filters, setFilter } = useFilters();

    const handleToggle = () => {
        // Cycle through: null → true → false → null
        if (filters.inStock === null) {
            setFilter('inStock', true);
        } else if (filters.inStock === true) {
            setFilter('inStock', false);
        } else {
            setFilter('inStock', null);
        }
    };

    return (
        <div className="space-y-3">
            <button
                onClick={handleToggle}
                className="w-full flex items-center justify-between px-3 py-2 text-sm border border-input hover:bg-accent transition-colors rounded-none"
            >
                <span>In Stock Only</span>
                <div className={`
          w-10 h-5 rounded-full transition-colors relative
          ${filters.inStock === true ? 'bg-primary' : 'bg-muted'}
        `}>
                    <div className={`
            absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform
            ${filters.inStock === true ? 'translate-x-5' : 'translate-x-0.5'}
          `} />
                </div>
            </button>

            {filters.inStock !== null && (
                <div className="text-xs text-muted-foreground px-1">
                    {filters.inStock ? 'Showing in-stock items only' : 'Showing out-of-stock items only'}
                </div>
            )}
        </div>
    );
}
