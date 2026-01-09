'use client';

import { useFilters } from '@/contexts/FilterContext';
import { SORT_OPTIONS } from '@/types/filters';
import { ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

/**
 * Sort Dropdown Component
 * Accessible dropdown for sorting options
 */

export function SortDropdown() {
    const { filters, setFilter } = useFilters();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const selectedOption = SORT_OPTIONS.find(opt => opt.value === filters.sortBy) || SORT_OPTIONS[0];

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isOpen]);

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-4 py-2 text-sm border border-input bg-background hover:bg-accent transition-colors rounded-none min-w-[180px] justify-between"
                aria-haspopup="listbox"
                aria-expanded={isOpen}
            >
                <span className="text-muted-foreground">Sort:</span>
                <span className="font-medium">{selectedOption.label}</span>
                <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute top-full right-0 mt-1 w-full bg-background border border-input shadow-lg z-50 rounded-none">
                    <ul role="listbox" className="py-1">
                        {SORT_OPTIONS.map((option) => (
                            <li key={option.value}>
                                <button
                                    onClick={() => {
                                        setFilter('sortBy', option.value);
                                        setIsOpen(false);
                                    }}
                                    className={`
                    w-full px-4 py-2 text-sm text-left hover:bg-accent transition-colors
                    ${option.value === filters.sortBy ? 'bg-accent font-medium' : ''}
                  `}
                                    role="option"
                                    aria-selected={option.value === filters.sortBy}
                                >
                                    {option.label}
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
