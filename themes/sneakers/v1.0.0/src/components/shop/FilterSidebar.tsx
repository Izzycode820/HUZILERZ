'use client';

import { AccordionItem } from '../ui/Accordion';
import { PriceRangeFilter } from '../filters/PriceRangeFilter';
import { StockFilter } from '../filters/StockFilter';

/**
 * Filter Sidebar Component
 * Refactored to use modular, decoupled filter components
 * Connected to FilterContext for state management
 */

export function FilterSidebar({ className }: { className?: string }) {
    return (
        <div className={className}>
            {/* Price Range Filter */}
            <AccordionItem title="Price" defaultOpen>
                <PriceRangeFilter />
            </AccordionItem>

            {/* Stock Availability Filter */}
            <AccordionItem title="Availability">
                <StockFilter />
            </AccordionItem>

            {/* TODO: Add Category and Brand filters when we have the data */}
            {/* These would require fetching categories/brands from the API */}
        </div>
    );
}
