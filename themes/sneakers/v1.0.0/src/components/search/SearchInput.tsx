'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';
import { SearchModal } from '../search/SearchModal';
import { Button } from '../shadcn-ui/button';

/**
 * Search Input Component
 * Desktop: Full search input
 * Mobile: Search icon that opens modal
 */

export function SearchInput() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [inputValue, setInputValue] = useState('');

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setInputValue(value);

        // Open modal when user starts typing
        if (value.trim() && !isModalOpen) {
            setIsModalOpen(true);
        }
    };

    const handleModalClose = () => {
        setIsModalOpen(false);
        setInputValue('');
    };

    const handleMobileClick = () => {
        setIsModalOpen(true);
    };

    return (
        <>
            {/* Desktop: Full Input */}
            <div className="relative flex-1 max-w-md hidden md:block">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <input
                    type="text"
                    placeholder="Search products..."
                    value={inputValue}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-2 bg-muted text-sm rounded-none focus:outline-none focus:ring-1 focus:ring-primary"
                />
            </div>

            {/* Mobile: Icon Button */}
            <Button
                variant="ghost"
                size="icon"
                onClick={handleMobileClick}
                className="md:hidden"
                aria-label="Search"
            >
                <Search className="h-5 w-5" />
            </Button>

            <SearchModal isOpen={isModalOpen} onClose={handleModalClose} />
        </>
    );
}
