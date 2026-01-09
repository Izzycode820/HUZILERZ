'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { FilterState, DEFAULT_FILTERS } from '@/types/filters';

/**
 * Filter Context
 * Centralized state management for product filtering
 * Decoupled from components for easy testing and maintenance
 */

interface FilterContextValue {
    filters: FilterState;
    setFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void;
    setFilters: (filters: Partial<FilterState>) => void;
    clearFilters: () => void;
    hasActiveFilters: boolean;
}

const FilterContext = createContext<FilterContextValue | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
    const [filters, setFiltersState] = useState<FilterState>(DEFAULT_FILTERS);

    // Set a single filter
    const setFilter = useCallback(<K extends keyof FilterState>(
        key: K,
        value: FilterState[K]
    ) => {
        setFiltersState(prev => ({ ...prev, [key]: value }));
    }, []);

    // Set multiple filters at once
    const setFilters = useCallback((newFilters: Partial<FilterState>) => {
        setFiltersState(prev => ({ ...prev, ...newFilters }));
    }, []);

    // Clear all filters
    const clearFilters = useCallback(() => {
        setFiltersState(DEFAULT_FILTERS);
    }, []);

    // Check if any filters are active (excluding search and sortBy)
    const hasActiveFilters =
        filters.categorySlug !== null ||
        filters.minPrice !== null ||
        filters.maxPrice !== null ||
        filters.inStock !== null ||
        filters.brand !== null;

    const value: FilterContextValue = {
        filters,
        setFilter,
        setFilters,
        clearFilters,
        hasActiveFilters,
    };

    return (
        <FilterContext.Provider value={value}>
            {children}
        </FilterContext.Provider>
    );
}

/**
 * Hook to access filter context
 * Throws error if used outside FilterProvider
 */
export function useFilters() {
    const context = useContext(FilterContext);
    if (!context) {
        throw new Error('useFilters must be used within FilterProvider');
    }
    return context;
}
