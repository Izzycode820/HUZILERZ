'use client';

import { useState, useEffect } from 'react';
import { ShoppingBag } from 'lucide-react';
import { Button } from '../ui/Button';
import { Product } from '@/lib/mock-data/products';
import { cn } from '../ui/Button';

interface MobileStickyBarProps {
    product: Product;
}

export function MobileStickyBar({ product }: MobileStickyBarProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            const mainButton = document.getElementById('main-add-to-cart');
            if (mainButton) {
                const rect = mainButton.getBoundingClientRect();
                // Show if scrolled past the bottom of the main button
                if (rect.bottom < 0) {
                    setIsVisible(true);
                } else {
                    setIsVisible(false);
                }
            }
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll(); // Check initial state

        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    if (!isVisible) return null;

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-center gap-1 md:hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
            {/* Simple Underlined Price - Scroll to Top */}
            <button
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                className="text-sm font-bold underline decoration-2 bg-white/80 backdrop-blur-sm px-2 py-0.5 shadow-sm rounded-sm transition-transform active:scale-95"
            >
                ${product.price.toFixed(2)}
            </button>

            {/* Floating Hollow Circle Add to Cart */}
            <Button
                size="icon"
                className="h-14 w-14 rounded-full border-2 border-black bg-white text-black hover:bg-black hover:text-white shadow-xl transition-all hover:scale-105"
                onClick={() => {
                    // Logic to add to cart
                    console.log('Added to cart');
                }}
            >
                <ShoppingBag className="h-6 w-6" />
                <span className="sr-only">Add to Cart</span>
            </Button>
        </div>
    );
}
