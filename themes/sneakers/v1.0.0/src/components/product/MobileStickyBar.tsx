'use client';

import { useState, useEffect } from 'react';
import { ShoppingBag } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import { GetProductDetailsQuery } from '@/services/products/__generated__/get-product-details.generated';
import { cn } from '@/lib/utils';

type ProductType = NonNullable<GetProductDetailsQuery['product']>;

interface MobileStickyBarProps {
    product: ProductType;
    onAddToCart?: (pos: { x: number; y: number }) => void;
}

export function MobileStickyBar({ product, onAddToCart }: MobileStickyBarProps) {
    const [isVisible, setIsVisible] = useState(false);
    const price = parseFloat(product.price?.toString() || '0');

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
                className="text-sm font-bold underline decoration-2 bg-background/80 backdrop-blur-sm px-2 py-0.5 shadow-sm rounded-sm transition-transform active:scale-95 text-foreground border border-border"
            >
                ${price.toFixed(2)}
            </button>

            {/* Floating Hollow Circle Add to Cart */}
            <Button
                size="icon"
                className="h-14 w-14 rounded-full border-2 border-primary bg-background text-primary hover:bg-primary hover:text-primary-foreground shadow-xl transition-all hover:scale-105"
                onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const pos = {
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                    };

                    if (onAddToCart) {
                        onAddToCart(pos);
                    } else {
                        // Scroll to top to interact with main button
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                }}
            >
                <ShoppingBag className="h-6 w-6" />
                <span className="sr-only">Add to Cart</span>
            </Button>
        </div>


    );
}
