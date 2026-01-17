'use client';


import { Link } from 'react-router-dom';
import { ShoppingBag, Heart } from 'lucide-react';
import { Button } from '../shadcn-ui/button';

/**
 * Compact Product Card for Search Results
 * Responsive: Vertical card in grid (desktop), horizontal in list (mobile)
 */

interface CompactProductCardProps {
    id: string;
    name: string;
    slug: string;
    price: number;
    compareAtPrice?: number;
    imageUrl?: string;
    onAddToCart?: (id: string, startPos?: { x: number; y: number }) => void;
    onClose?: () => void;
}

export function CompactProductCard({
    id,
    name,
    slug,
    price,
    compareAtPrice,
    imageUrl,
    onAddToCart,
    onClose,
}: CompactProductCardProps) {
    const formatPrice = (amount: number) => `$${amount.toFixed(2)}`;

    const handleAddToCart = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        const rect = e.currentTarget.getBoundingClientRect();
        const startPos = {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2,
        };
        onAddToCart?.(id, startPos);
    };

    const handleWishlist = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        // TODO: Implement wishlist functionality
        console.log('Add to wishlist:', id);
    };

    return (
        <Link
            href={`/products/${slug}`}
            onClick={onClose}
            className="flex md:flex-col gap-3 p-3 hover:bg-accent transition-colors rounded-sm group border border-transparent hover:border-border relative"
        >
            {/* Image with Overlay Actions (Desktop Grid Only) */}
            <div className="relative w-20 h-20 md:w-full md:h-40 flex-shrink-0 bg-muted overflow-hidden">
                {imageUrl ? (
                    <Image
                        src={imageUrl}
                        alt={name}
                        fill
                        className="object-cover"
                        sizes="(max-width: 768px) 80px, 200px"
                        unoptimized
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center text-muted-foreground text-xs">
                        No Image
                    </div>
                )}

                {/* Hover Overlay with Actions - Desktop Grid Only */}
                <div className="hidden md:flex absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity items-center justify-center gap-2">
                    <Button
                        size="icon"
                        variant="secondary"
                        className="h-9 w-9 rounded-full"
                        onClick={handleAddToCart}
                    >
                        <ShoppingBag className="h-4 w-4" />
                    </Button>
                    <Button
                        size="icon"
                        variant="secondary"
                        className="h-9 w-9 rounded-full"
                        onClick={handleWishlist}
                    >
                        <Heart className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0 flex flex-col justify-between">
                <h3 className="text-sm font-medium text-foreground line-clamp-2 group-hover:text-primary transition-colors">
                    {name}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                    {compareAtPrice && compareAtPrice > price ? (
                        <>
                            <span className="text-sm font-bold text-destructive">{formatPrice(price)}</span>
                            <span className="text-xs text-muted-foreground line-through">{formatPrice(compareAtPrice)}</span>
                        </>
                    ) : (
                        <span className="text-sm font-bold text-foreground">{formatPrice(price)}</span>
                    )}
                </div>
            </div>

            {/* Mobile Horizontal Layout Actions */}
            <div className="md:hidden flex flex-col gap-1 justify-center">
                <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={handleAddToCart}
                >
                    <ShoppingBag className="h-4 w-4" />
                </Button>
                <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={handleWishlist}
                >
                    <Heart className="h-4 w-4" />
                </Button>
            </div>
        </Link>
    );
}
